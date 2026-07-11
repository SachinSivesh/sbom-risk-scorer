"""Application CRUD API routes."""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import get_db
from app.models.application import Application
from app.models.sbom import Sbom
from app.models.risk_report import RiskReport
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationListItem,
    ApplicationDetail,
    SbomSummary,
)
from app.schemas.risk_report import RiskTrendPoint

router = APIRouter()


@router.post("", response_model=ApplicationResponse, status_code=201)
async def create_application(
    body: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new application."""
    app = Application(
        id=uuid.uuid4(),
        name=body.name,
        description=body.description,
    )
    db.add(app)
    await db.flush()
    await db.refresh(app)
    return app


@router.get("", response_model=list[ApplicationListItem])
async def list_applications(db: AsyncSession = Depends(get_db)):
    """List all applications with their latest risk score."""
    result = await db.execute(
        select(Application).order_by(Application.created_at.desc())
    )
    apps = result.scalars().all()

    items = []
    for app in apps:
        # Get latest risk report
        report_result = await db.execute(
            select(RiskReport)
            .filter(RiskReport.application_id == app.id)
            .order_by(RiskReport.created_at.desc())
            .limit(1)
        )
        latest_report = report_result.scalar_one_or_none()

        # Get SBOM count
        count_result = await db.execute(
            select(func.count()).select_from(Sbom).filter(Sbom.application_id == app.id)
        )
        sbom_count = count_result.scalar() or 0

        items.append(ApplicationListItem(
            id=app.id,
            name=app.name,
            description=app.description,
            latest_score=latest_report.overall_score if latest_report else None,
            latest_category=latest_report.category if latest_report else None,
            last_analyzed_at=latest_report.created_at if latest_report else None,
            sbom_count=sbom_count,
            created_at=app.created_at,
        ))

    return items


@router.get("/{app_id}", response_model=ApplicationDetail)
async def get_application(
    app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get application detail with SBOM history."""
    result = await db.execute(
        select(Application)
        .filter(Application.id == app_id)
        .options(selectinload(Application.sboms))
    )
    app = result.scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=404, detail={
            "code": "APPLICATION_NOT_FOUND",
            "message": f"Application {app_id} not found",
        })

    return ApplicationDetail(
        id=app.id,
        name=app.name,
        description=app.description,
        created_at=app.created_at,
        updated_at=app.updated_at,
        sboms=[
            SbomSummary(
                id=s.id,
                original_filename=s.original_filename,
                format=s.format,
                status=s.status,
                component_count=s.component_count,
                created_at=s.created_at,
            )
            for s in sorted(app.sboms, key=lambda x: x.created_at, reverse=True)
        ],
    )


@router.get("/{app_id}/trend", response_model=list[RiskTrendPoint])
async def get_risk_trend(
    app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get historical risk score trend for an application."""
    # Verify application exists
    result = await db.execute(
        select(Application).filter(Application.id == app_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail={
            "code": "APPLICATION_NOT_FOUND",
            "message": f"Application {app_id} not found",
        })

    result = await db.execute(
        select(RiskReport)
        .filter(RiskReport.application_id == app_id)
        .order_by(RiskReport.created_at.asc())
    )
    reports = result.scalars().all()

    return [
        RiskTrendPoint(
            sbom_id=r.sbom_id,
            overall_score=r.overall_score,
            category=r.category,
            created_at=r.created_at,
        )
        for r in reports
    ]
