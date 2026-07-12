from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.application import Application
from app.models.risk_report import RiskReport
from app.models.dependency import Dependency
from app.models.vulnerability import Vulnerability
from app.models.maintenance import MaintenanceSignal

router = APIRouter()

@router.get("/summary")
async def get_portfolio_summary(db: AsyncSession = Depends(get_db)):
    """Compute portfolio-wide security metrics for executive roll-up dashboard."""
    # 1. Fetch all applications
    app_result = await db.execute(select(Application))
    apps = app_result.scalars().all()
    total_apps = len(apps)
    
    if total_apps == 0:
        return {
            "total_applications": 0,
            "average_risk_score": 0,
            "criticality_distribution": {},
            "department_risks": [],
            "license_distribution": {},
            "vulnerability_stats": {"total": 0, "critical": 0, "high": 0},
            "top_risky_apps": []
        }

    # 2. Get latest risk report for each application
    avg_score_sum = 0
    scored_apps_count = 0
    top_risky_apps = []
    
    criticality_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    dept_scores = {} # dept -> (total_score, count)
    
    for app in apps:
        crit = app.criticality or "MEDIUM"
        criticality_counts[crit] = criticality_counts.get(crit, 0) + 1
        
        # Query latest report
        report_result = await db.execute(
            select(RiskReport)
            .filter(RiskReport.application_id == app.id)
            .order_by(RiskReport.created_at.desc())
            .limit(1)
        )
        report = report_result.scalar_one_or_none()
        
        if report:
            score = report.overall_score
            avg_score_sum += score
            scored_apps_count += 1
            
            top_risky_apps.append({
                "id": str(app.id),
                "name": app.name,
                "score": score,
                "category": report.category,
                "criticality": crit,
                "department": app.department or "Engineering"
            })
            
            dept = app.department or "Engineering"
            dept_scores.setdefault(dept, []).append(score)

    avg_portfolio_score = round(avg_score_sum / scored_apps_count) if scored_apps_count > 0 else 0
    top_risky_apps = sorted(top_risky_apps, key=lambda x: x["score"], reverse=True)[:5]
    
    department_risks = [
        {
            "department": dept,
            "average_score": round(sum(scores) / len(scores)),
            "app_count": len(scores)
        }
        for dept, scores in dept_scores.items()
    ]

    # 3. Query vulnerabilities and licenses metrics across all active dependencies
    vuln_count_res = await db.execute(
        select(Vulnerability.severity, func.count(Vulnerability.id))
        .group_by(Vulnerability.severity)
    )
    vuln_breakdown = vuln_count_res.all()
    vuln_stats = {"total": 0, "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for sev, count in vuln_breakdown:
        vuln_stats[sev] = count
        vuln_stats["total"] += count

    license_risk_res = await db.execute(
        select(Dependency.license_id, func.count(Dependency.id))
        .group_by(Dependency.license_id)
    )
    license_breakdown = license_risk_res.all()
    license_distribution = {lic: count for lic, count in license_breakdown if lic}

    return {
        "total_applications": total_apps,
        "average_risk_score": avg_portfolio_score,
        "criticality_distribution": criticality_counts,
        "department_risks": department_risks,
        "license_distribution": license_distribution,
        "vulnerability_stats": vuln_stats,
        "top_risky_apps": top_risky_apps
    }
