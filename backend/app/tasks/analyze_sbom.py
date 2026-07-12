"""Celery task orchestrating the full SBOM analysis pipeline."""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.celery_app import celery_app
from app.config import get_settings
from app.parsers.base import SBOMParser
from app.parsers.cyclonedx_parser import CycloneDXParser
from app.parsers.spdx_parser import SPDXParser
from app.resolvers.graph_builder import GraphBuilder
from app.analyzers.vulnerability_analyzer import VulnerabilityAnalyzer
from app.analyzers.license_analyzer import LicenseAnalyzer
from app.analyzers.maintenance_analyzer import MaintenanceAnalyzer
from app.scoring.risk_engine import RiskEngine, DependencyScore
from app.ai.remediation_service import RemediationService
from app.storage.file_storage import get_file_storage
from app.models.sbom import Sbom
from app.models.dependency import Dependency, DependencyEdge
from app.models.vulnerability import Vulnerability
from app.models.maintenance import MaintenanceSignal
from app.models.risk_report import RiskReport
from app.models.ai_report import AIReport
from app.utils.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()

# Synchronous engine for Celery tasks
sync_engine = create_engine(settings.SYNC_DATABASE_URL)
SyncSession = sessionmaker(bind=sync_engine)


def _run_async(coro):
    """Helper to run async code in sync Celery task."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(name="app.tasks.analyze_sbom.analyze", bind=True, max_retries=0)
def analyze_sbom_task(self, sbom_id: str):
    """
    Full SBOM analysis pipeline:
    1. Parse SBOM → 2. Build graph → 3. Analyze (vuln + license + maintenance)
    → 4. Score → 5. AI summary
    """
    session = SyncSession()

    try:
        sbom = session.query(Sbom).filter(Sbom.id == uuid.UUID(sbom_id)).first()
        if not sbom:
            logger.error("SBOM not found", sbom_id=sbom_id)
            return

        logger.info("Starting SBOM analysis", sbom_id=sbom_id)
        all_warnings = []

        # ── Step 1: Parse SBOM ──────────────────────────────────────
        sbom.status = "parsing"
        session.commit()

        try:
            storage = get_file_storage()
            raw_content = storage.read(sbom.filename_stored)
            sbom_data = json.loads(raw_content)

            # Detect format and parse
            fmt = SBOMParser.detect_format(sbom_data)
            parser = CycloneDXParser() if fmt == "cyclonedx" else SPDXParser()
            parse_result = parser.parse(sbom_data)
            all_warnings.extend(parse_result.warnings)

            logger.info(
                "SBOM parsed successfully",
                dep_count=len(parse_result.dependencies),
                edge_count=len(parse_result.edges),
            )

        except Exception as e:
            sbom.status = "parse_failed"
            sbom.error_detail = str(e)
            session.commit()
            logger.error("SBOM parsing failed", error=str(e), sbom_id=sbom_id)
            return

        # ── Step 2: Persist dependencies and build graph ────────────
        sbom.status = "resolving"
        session.commit()

        dep_models = []
        bom_ref_to_dep_id = {}

        for parsed_dep in parse_result.dependencies:
            dep = Dependency(
                id=uuid.uuid4(),
                sbom_id=sbom.id,
                name=parsed_dep.name,
                version=parsed_dep.version,
                ecosystem=parsed_dep.ecosystem,
                purl=parsed_dep.purl,
                license_id=parsed_dep.license_id,
                is_direct=parsed_dep.is_direct,
                repo_url=parsed_dep.repo_url,
            )
            dep_models.append(dep)
            session.add(dep)
            if parsed_dep.bom_ref:
                bom_ref_to_dep_id[parsed_dep.bom_ref] = dep.id

        session.flush()

        # Build graph and persist edges
        graph_builder = GraphBuilder()
        dep_graph = graph_builder.build(
            parse_result.dependencies,
            parse_result.edges,
            parse_result.root_ref,
        )
        all_warnings.extend(dep_graph.warnings)

        for edge in parse_result.edges:
            from_id = bom_ref_to_dep_id.get(edge.from_ref)
            to_id = bom_ref_to_dep_id.get(edge.to_ref)
            if from_id and to_id:
                edge_model = DependencyEdge(
                    id=uuid.uuid4(),
                    sbom_id=sbom.id,
                    from_dependency_id=from_id,
                    to_dependency_id=to_id,
                )
                session.add(edge_model)

        sbom.component_count = len(dep_models)
        session.commit()

        # Compute depths using networkx
        import networkx as nx
        dg = nx.DiGraph()
        for edge in parse_result.edges:
            from_id = bom_ref_to_dep_id.get(edge.from_ref)
            to_id = bom_ref_to_dep_id.get(edge.to_ref)
            if from_id and to_id:
                dg.add_edge(from_id, to_id)

        dep_depths = {}
        for dep in dep_models:
            if dep.is_direct:
                dep_depths[dep.id] = 1

        for direct_dep in [d for d in dep_models if d.is_direct]:
            if direct_dep.id in dg:
                try:
                    for target, path in nx.single_source_shortest_path(dg, direct_dep.id).items():
                        dep_depths[target] = min(dep_depths.get(target, 999), len(path))
                except Exception as e:
                    logger.error("Error computing graph shortest path", error=str(e))

        # ── Step 3: Sequential Stage Analysis ─────────────────────────
        app_id_val = sbom.application.app_id if sbom.application else None
        dep_data = [
            {
                "id": str(dep.id),
                "name": dep.name,
                "version": dep.version,
                "ecosystem": dep.ecosystem,
                "license_id": dep.license_id,
                "repo_url": dep.repo_url,
                "is_direct": dep.is_direct,
                "app_id": app_id_val,
            }
            for dep in dep_models
        ]

        # 3.1 Vulnerability Analysis
        sbom.status = "vuln_checking"
        session.commit()
        vuln_analyzer = VulnerabilityAnalyzer()
        vuln_results, vuln_warnings = _run_async(vuln_analyzer.analyze(dep_data))
        all_warnings.extend(vuln_warnings)

        for vr in vuln_results:
            dep_uuid = uuid.UUID(vr.dependency_id)
            for v in vr.vulnerabilities:
                vuln_model = Vulnerability(
                    id=uuid.uuid4(),
                    dependency_id=dep_uuid,
                    vuln_id=v.vuln_id,
                    severity=v.severity,
                    summary=v.summary,
                    fixed_version=v.fixed_version,
                    source=v.source,
                )
                session.add(vuln_model)

        # 3.2 License Analysis
        sbom.status = "license_checking"
        session.commit()
        license_analyzer = LicenseAnalyzer()
        license_results = license_analyzer.analyze(dep_data)

        # 3.3 Maintenance Analysis
        sbom.status = "maint_checking"
        session.commit()
        maint_analyzer = MaintenanceAnalyzer()
        maint_results = _run_async(maint_analyzer.analyze(dep_data))

        for mr in maint_results:
            dep_uuid = uuid.UUID(mr.dependency_id)
            maint_model = MaintenanceSignal(
                id=uuid.uuid4(),
                dependency_id=dep_uuid,
                last_commit_at=mr.last_commit_at,
                stars=mr.stars,
                is_archived=mr.is_archived,
                release_frequency_days=mr.release_frequency_days,
                maintenance_score=mr.maintenance_score,
                status=mr.status,
            )
            session.add(maint_model)

        session.commit()

        # ── Step 4: Risk Scoring ──────────────────────────────────────
        sbom.status = "scoring"
        session.commit()
        risk_engine = RiskEngine()

        # Build per-dependency scores and perform transitive propagation
        dep_scores = []
        vuln_by_dep = {vr.dependency_id: vr for vr in vuln_results}
        license_by_dep = {lr.dependency_id: lr for lr in license_results}
        maint_by_dep = {mr.dependency_id: mr for mr in maint_results}

        # Initialize base vulnerability scores
        vuln_scores = {}
        for dep in dep_models:
            dep_id_str = str(dep.id)
            vr = vuln_by_dep.get(dep_id_str)
            base_score = 0
            if vr:
                base_score = risk_engine.compute_vuln_score([
                    {"severity": v.severity} for v in vr.vulnerabilities
                ])
            vuln_scores[dep.id] = base_score

        # Propagate child vulnerability risk up to parent (attenuated by 50%)
        # Run up to 5 passes to cover transitive depth chains
        for _ in range(5):
            for parent_id in list(dg.nodes):
                for child_id in dg.successors(parent_id):
                    propagated = round(vuln_scores.get(child_id, 0) * 0.5)
                    if propagated > vuln_scores.get(parent_id, 0):
                        vuln_scores[parent_id] = propagated

        # Retrieve application criticality
        app_criticality = sbom.application.criticality if sbom.application else "MEDIUM"

        for dep in dep_models:
            dep_id_str = str(dep.id)
            lr = license_by_dep.get(dep_id_str)
            mr = maint_by_dep.get(dep_id_str)

            # Use propagated score
            v_score = vuln_scores.get(dep.id, 0)

            license_score = 0
            if lr:
                license_score = risk_engine.compute_license_score(lr.risk_level)

            maintenance_score = None
            if mr and mr.maintenance_score is not None:
                maintenance_score = mr.maintenance_score

            dep_scores.append(DependencyScore(
                dependency_id=dep_id_str,
                name=dep.name,
                version=dep.version,
                is_direct=dep.is_direct,
                vuln_score=v_score,
                license_score=license_score,
                maintenance_score=maintenance_score,
                depth=dep_depths.get(dep.id, 2),
                license_id=dep.license_id or "UNKNOWN",
                vulnerabilities=[{"severity": v.severity} for v in (vuln_by_dep.get(dep_id_str).vulnerabilities if vuln_by_dep.get(dep_id_str) else [])],
            ))

        score_result = risk_engine.calculate(dep_scores, criticality=app_criticality)

        # Persist risk report
        risk_report = RiskReport(
            id=uuid.uuid4(),
            sbom_id=sbom.id,
            application_id=sbom.application_id,
            overall_score=score_result.overall_score,
            category=score_result.category,
            vulnerability_subscore=score_result.vulnerability_subscore,
            license_subscore=score_result.license_subscore,
            maintenance_subscore=score_result.maintenance_subscore,
            breakdown_json=score_result.breakdown,
        )
        session.add(risk_report)
        session.flush()

        # ── Step 5: AI Summary ────────────────────────────────────────
        sbom.status = "ai_assessing"
        session.commit()

        try:
            remediation_service = RemediationService()
            report_dict = {
                "overall_score": score_result.overall_score,
                "category": score_result.category,
                "vulnerability_subscore": score_result.vulnerability_subscore,
                "license_subscore": score_result.license_subscore,
                "maintenance_subscore": score_result.maintenance_subscore,
                "breakdown": score_result.breakdown,
                "application": {
                    "name": sbom.application.name if sbom.application else "unknown",
                    "criticality": sbom.application.criticality if sbom.application else "MEDIUM",
                    "language": sbom.application.language if sbom.application else "unknown",
                    "license_model": sbom.application.license_model if sbom.application else "proprietary",
                    "business_owner": sbom.application.business_owner if sbom.application else "unknown",
                    "department": sbom.application.department if sbom.application else "unknown",
                    "deployment": sbom.application.deployment if sbom.application else "unknown",
                }
            }
            ai_result = _run_async(remediation_service.generate_summary(report_dict))

            ai_report = AIReport(
                id=uuid.uuid4(),
                risk_report_id=risk_report.id,
                summary=ai_result["summary"],
                top_actions_json=ai_result["top_actions"],
                model_used=ai_result["model_used"],
                fallback_used=ai_result["fallback_used"],
            )
            session.add(ai_report)
        except Exception as e:
            logger.error("AI summary generation failed", error=str(e))
            # Create a fallback AI report
            fallback_text = (
                "### Executive Summary\n"
                f"Automated risk scoring is complete. The application received an overall Risk Index score of {score_result.overall_score}/100, placing it in the {score_result.category} risk category.\n\n"
                "### Major Risks\n"
                f"The application exhibits a vulnerability subscore of {score_result.vulnerability_subscore}/100, representing the main driver of threat exposure.\n\n"
                "### License Issues\n"
                f"Open source compliance checks yielded a subscore of {score_result.license_subscore}/100, outlining copyright and legal liabilities.\n\n"
                "### Supply Chain Exposure\n"
                f"Dependency maintenance and freshness metrics evaluated to {score_result.maintenance_subscore}/100.\n\n"
                "### Business Impact\n"
                f"Operational risk scales with business criticality. Deployment governance gates must verify overall alignment.\n\n"
                "### Recommended Remediation\n"
                "1. Address high-risk and critical vulnerabilities first.\n"
                "2. Remediate licensing policy conflicts.\n"
                "3. Clean deprecated or unmaintained packages.\n\n"
                "### Deployment Recommendation\n"
                f"Deployment gate check: {score_result.breakdown.get('policy_evaluation', {}).get('status', 'REJECTED')}.\n\n"
                "### Confidence Level\n"
                "100% automated validation (offline reference datasets and rules matrices)."
            )
            ai_report = AIReport(
                id=uuid.uuid4(),
                risk_report_id=risk_report.id,
                summary=fallback_text,
                top_actions_json=[
                    {"title": "Execute Patch Management", "description": "Prioritize updating packages with direct vulnerabilities.", "priority": "HIGH"},
                    {"title": "Review Copyleft Licensing", "description": "Ensure legal clearance for viral GPL/AGPL compliance.", "priority": "MEDIUM"}
                ],
                model_used="error-fallback",
                fallback_used=True,
            )
            session.add(ai_report)

        # ── Finalize ────────────────────────────────────────────────
        sbom.status = "completed"
        sbom.warnings = json.dumps(all_warnings) if all_warnings else None
        session.commit()

        logger.info(
            "SBOM analysis completed",
            sbom_id=sbom_id,
            score=score_result.overall_score,
            category=score_result.category,
        )

    except Exception as e:
        logger.error("SBOM analysis task failed", error=str(e), sbom_id=sbom_id)
        try:
            sbom = session.query(Sbom).filter(Sbom.id == uuid.UUID(sbom_id)).first()
            if sbom:
                sbom.status = "failed"
                sbom.error_detail = str(e)
                session.commit()
        except Exception:
            pass
    finally:
        session.close()


async def _run_analyzers(dep_data: list[dict]):
    """Run all three analyzers concurrently."""
    vuln_analyzer = VulnerabilityAnalyzer()
    license_analyzer = LicenseAnalyzer()
    maint_analyzer = MaintenanceAnalyzer()

    # License analysis is synchronous, wrap it
    async def run_license():
        return license_analyzer.analyze(dep_data)

    vuln_results, license_results, maint_results = await asyncio.gather(
        vuln_analyzer.analyze(dep_data),
        run_license(),
        maint_analyzer.analyze(dep_data),
        return_exceptions=True,
    )

    # Handle exceptions in individual analyzers
    if isinstance(vuln_results, Exception):
        logger.error("Vulnerability analyzer failed", error=str(vuln_results))
        vuln_results = ([], ["VULN_LOOKUP_DEGRADED"])
    if isinstance(license_results, Exception):
        logger.error("License analyzer failed", error=str(license_results))
        license_results = []
    if isinstance(maint_results, Exception):
        logger.error("Maintenance analyzer failed", error=str(maint_results))
        maint_results = []

    return vuln_results, license_results, maint_results
