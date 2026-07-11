"""Risk report and AI summary API routes."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import get_db
from app.models.sbom import Sbom
from app.models.risk_report import RiskReport
from app.models.ai_report import AIReport
from app.models.dependency import Dependency
from app.models.vulnerability import Vulnerability
from app.models.maintenance import MaintenanceSignal
from app.schemas.risk_report import RiskReportResponse, DependencyWithFindings, VulnerabilityItem
from app.schemas.ai_report import AIReportResponse, AIReportAction
from app.models.license import evaluate_license_expression

router = APIRouter()


@router.get("/{sbom_id}", response_model=RiskReportResponse)
async def get_risk_report(
    sbom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Fetch the completed risk report for an SBOM."""
    # Check SBOM status first
    sbom_result = await db.execute(
        select(Sbom).filter(Sbom.id == sbom_id)
    )
    sbom = sbom_result.scalar_one_or_none()

    if not sbom:
        raise HTTPException(status_code=404, detail={
            "code": "SBOM_NOT_FOUND",
            "message": f"SBOM {sbom_id} not found",
        })

    if sbom.status != "completed":
        raise HTTPException(status_code=409, detail={
            "code": "ANALYSIS_NOT_COMPLETE",
            "message": f"Analysis status: {sbom.status}",
        })

    # Get risk report
    result = await db.execute(
        select(RiskReport).filter(RiskReport.sbom_id == sbom_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail={
            "code": "REPORT_NOT_FOUND",
            "message": f"Risk report for SBOM {sbom_id} not found",
        })

    # Get dependencies with findings
    deps_result = await db.execute(
        select(Dependency)
        .filter(Dependency.sbom_id == sbom_id)
        .options(
            selectinload(Dependency.vulnerabilities),
            selectinload(Dependency.maintenance_signal),
        )
    )
    deps = deps_result.scalars().all()

    dep_findings = []
    for dep in deps:
        _, license_risk = evaluate_license_expression(dep.license_id)

        vulns = [
            VulnerabilityItem(
                vuln_id=v.vuln_id,
                severity=v.severity,
                summary=v.summary,
                fixed_version=v.fixed_version,
                source=v.source,
            )
            for v in dep.vulnerabilities
        ]

        maint = dep.maintenance_signal
        dep_findings.append(DependencyWithFindings(
            id=dep.id,
            name=dep.name,
            version=dep.version,
            ecosystem=dep.ecosystem,
            is_direct=dep.is_direct,
            license_id=dep.license_id,
            license_risk=license_risk,
            repo_url=dep.repo_url,
            vulnerabilities=vulns,
            maintenance_score=maint.maintenance_score if maint else None,
            maintenance_status=maint.status if maint else None,
        ))

    return RiskReportResponse(
        id=report.id,
        sbom_id=report.sbom_id,
        application_id=report.application_id,
        overall_score=report.overall_score,
        category=report.category,
        vulnerability_subscore=report.vulnerability_subscore,
        license_subscore=report.license_subscore,
        maintenance_subscore=report.maintenance_subscore,
        breakdown=report.breakdown_json,
        created_at=report.created_at,
        dependencies=dep_findings,
    )


@router.get("/{sbom_id}/ai-summary", response_model=AIReportResponse)
async def get_ai_summary(
    sbom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Fetch the AI-generated remediation summary."""
    # Check SBOM status first
    sbom_result = await db.execute(
        select(Sbom).filter(Sbom.id == sbom_id)
    )
    sbom = sbom_result.scalar_one_or_none()

    if not sbom:
        raise HTTPException(status_code=404, detail={
            "code": "SBOM_NOT_FOUND",
            "message": f"SBOM {sbom_id} not found",
        })

    if sbom.status != "completed":
        raise HTTPException(status_code=409, detail={
            "code": "ANALYSIS_NOT_COMPLETE",
            "message": f"Analysis status: {sbom.status}",
        })

    # Get risk report first with its AI report preloaded
    result = await db.execute(
        select(RiskReport)
        .filter(RiskReport.sbom_id == sbom_id)
        .options(selectinload(RiskReport.ai_report))
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail={
            "code": "REPORT_NOT_FOUND",
            "message": f"Risk report for SBOM {sbom_id} not found",
        })

    ai_report = report.ai_report

    if not ai_report:
        raise HTTPException(status_code=404, detail={
            "code": "AI_REPORT_NOT_FOUND",
            "message": f"AI report for SBOM {sbom_id} not found",
        })

    actions = []
    if ai_report.top_actions_json:
        for a in ai_report.top_actions_json:
            actions.append(AIReportAction(
                title=a.get("title", ""),
                description=a.get("description", ""),
                priority=a.get("priority", "MEDIUM"),
            ))

    return AIReportResponse(
        id=ai_report.id,
        risk_report_id=ai_report.risk_report_id,
        summary=ai_report.summary,
        top_actions=actions,
        model_used=ai_report.model_used,
        fallback_used=ai_report.fallback_used,
        created_at=ai_report.created_at,
    )
