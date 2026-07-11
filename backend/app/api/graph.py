"""Dependency graph API routes."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import get_db
from app.models.sbom import Sbom
from app.models.dependency import Dependency, DependencyEdge
from app.models.vulnerability import Vulnerability
from app.models.license import evaluate_license_expression

router = APIRouter()


@router.get("/{sbom_id}")
async def get_dependency_graph(
    sbom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Fetch the dependency graph for visualization."""
    # Verify SBOM exists
    sbom_result = await db.execute(
        select(Sbom).filter(Sbom.id == sbom_id)
    )
    sbom = sbom_result.scalar_one_or_none()
    if not sbom:
        raise HTTPException(status_code=404, detail={
            "code": "SBOM_NOT_FOUND",
            "message": f"SBOM {sbom_id} not found",
        })

    # Get dependencies with vulnerabilities
    deps_result = await db.execute(
        select(Dependency)
        .filter(Dependency.sbom_id == sbom_id)
        .options(selectinload(Dependency.vulnerabilities))
    )
    deps = deps_result.scalars().all()

    # Get edges
    edges_result = await db.execute(
        select(DependencyEdge).filter(DependencyEdge.sbom_id == sbom_id)
    )
    edges = edges_result.scalars().all()

    # Build nodes with risk levels
    nodes = []
    for dep in deps:
        # Determine risk level based on vulnerability severity
        risk_level = "NONE"
        if dep.vulnerabilities:
            max_severity = max(
                (v.severity for v in dep.vulnerabilities),
                key=lambda s: {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "UNKNOWN": 2}.get(s, 0),
            )
            risk_level = max_severity

        # Also consider license risk
        _, license_risk = evaluate_license_expression(dep.license_id)
        if license_risk == "HIGH" and risk_level in ("NONE", "LOW"):
            risk_level = "MEDIUM"

        nodes.append({
            "id": str(dep.id),
            "label": f"{dep.name}@{dep.version}",
            "ecosystem": dep.ecosystem,
            "is_direct": dep.is_direct,
            "risk_level": risk_level,
            "name": dep.name,
            "version": dep.version,
            "license_id": dep.license_id,
            "vuln_count": len(dep.vulnerabilities),
        })

    # Build edges
    edge_list = [
        {
            "from": str(e.from_dependency_id),
            "to": str(e.to_dependency_id),
        }
        for e in edges
    ]

    return {
        "nodes": nodes,
        "edges": edge_list,
    }
