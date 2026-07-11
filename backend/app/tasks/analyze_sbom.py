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

        session.flush()  # Get IDs assigned

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

        # ── Step 3: Analyze (concurrent) ────────────────────────────
        sbom.status = "analyzing"
        session.commit()

        # Prepare dependency data for analyzers
        dep_data = [
            {
                "id": str(dep.id),
                "name": dep.name,
                "version": dep.version,
                "ecosystem": dep.ecosystem,
                "license_id": dep.license_id,
                "repo_url": dep.repo_url,
                "is_direct": dep.is_direct,
            }
            for dep in dep_models
        ]

        # Run analyzers concurrently
        vuln_results, license_results, maint_results = _run_async(
            _run_analyzers(dep_data)
        )

        vuln_warnings = vuln_results[1] if isinstance(vuln_results, tuple) else []
        vuln_data = vuln_results[0] if isinstance(vuln_results, tuple) else vuln_results
        all_warnings.extend(vuln_warnings)

        # Persist vulnerability findings
        for vr in vuln_data:
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

        # Persist maintenance signals
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

        # ── Step 4: Score ───────────────────────────────────────────
        risk_engine = RiskEngine()

        # Build per-dependency scores
        dep_scores = []
        vuln_by_dep = {vr.dependency_id: vr for vr in vuln_data}
        license_by_dep = {lr.dependency_id: lr for lr in license_results}
        maint_by_dep = {mr.dependency_id: mr for mr in maint_results}

        for dep in dep_models:
            dep_id_str = str(dep.id)
            vr = vuln_by_dep.get(dep_id_str)
            lr = license_by_dep.get(dep_id_str)
            mr = maint_by_dep.get(dep_id_str)

            vuln_score = 0
            if vr:
                vuln_score = risk_engine.compute_vuln_score([
                    {"severity": v.severity} for v in vr.vulnerabilities
                ])

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
                vuln_score=vuln_score,
                license_score=license_score,
                maintenance_score=maintenance_score,
            ))

        score_result = risk_engine.calculate(dep_scores)

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

        # ── Step 5: AI Summary ──────────────────────────────────────
        try:
            remediation_service = RemediationService()
            report_dict = {
                "overall_score": score_result.overall_score,
                "category": score_result.category,
                "vulnerability_subscore": score_result.vulnerability_subscore,
                "license_subscore": score_result.license_subscore,
                "maintenance_subscore": score_result.maintenance_subscore,
                "breakdown": score_result.breakdown,
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
            ai_report = AIReport(
                id=uuid.uuid4(),
                risk_report_id=risk_report.id,
                summary=f"Risk score: {score_result.overall_score}/100 ({score_result.category}). Automated analysis complete.",
                top_actions_json=[],
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
