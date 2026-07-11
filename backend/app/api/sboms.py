"""SBOM upload and status API routes."""

import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.config import get_settings
from app.models.application import Application
from app.models.sbom import Sbom
from app.schemas.sbom import SbomUploadResponse, SbomStatusResponse
from app.storage.file_storage import get_file_storage
from app.parsers.base import SBOMParser
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


@router.post("", response_model=SbomUploadResponse, status_code=202)
async def upload_sbom(
    file: UploadFile = File(...),
    application_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload an SBOM file for analysis."""
    # Validate application_id
    if not application_id:
        raise HTTPException(status_code=400, detail={
            "code": "MISSING_APPLICATION",
            "message": "application_id is required",
        })

    try:
        app_uuid = uuid.UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail={
            "code": "VALIDATION_ERROR",
            "message": "Invalid application_id format",
        })

    # Check application exists
    result = await db.execute(
        select(Application).filter(Application.id == app_uuid)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail={
            "code": "APPLICATION_NOT_FOUND",
            "message": f"Application {application_id} not found",
        })

    # Read file content
    content = await file.read()

    # Check file size
    if len(content) > settings.MAX_SBOM_SIZE_BYTES:
        raise HTTPException(status_code=413, detail={
            "code": "FILE_TOO_LARGE",
            "message": f"File size exceeds {settings.MAX_SBOM_SIZE_BYTES // (1024*1024)} MB limit",
        })

    # Validate JSON
    try:
        sbom_data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_JSON",
            "message": "File is not valid JSON",
        })

    # Detect SBOM format
    try:
        sbom_format = SBOMParser.detect_format(sbom_data)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "UNSUPPORTED_SBOM_FORMAT",
            "message": "File is not a recognized CycloneDX or SPDX SBOM",
        })

    # Store the file
    storage = get_file_storage()
    stored_filename = storage.save(content)

    # Create SBOM record
    sbom = Sbom(
        id=uuid.uuid4(),
        application_id=app_uuid,
        filename_stored=stored_filename,
        original_filename=file.filename or "unknown.json",
        format=sbom_format,
        status="queued",
    )
    db.add(sbom)
    await db.flush()
    await db.refresh(sbom)

    # Trigger async analysis task
    from app.tasks.analyze_sbom import analyze_sbom_task
    analyze_sbom_task.delay(str(sbom.id))

    logger.info(
        "SBOM uploaded and queued for analysis",
        sbom_id=str(sbom.id),
        format=sbom_format,
        filename=file.filename,
    )

    return SbomUploadResponse(
        sbom_id=sbom.id,
        status="queued",
    )


@router.get("/{sbom_id}/status", response_model=SbomStatusResponse)
async def get_sbom_status(
    sbom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Poll the status of an SBOM analysis."""
    result = await db.execute(
        select(Sbom).filter(Sbom.id == sbom_id)
    )
    sbom = result.scalar_one_or_none()

    if not sbom:
        raise HTTPException(status_code=404, detail={
            "code": "SBOM_NOT_FOUND",
            "message": f"SBOM {sbom_id} not found",
        })

    warnings = None
    if sbom.warnings:
        try:
            warnings = json.loads(sbom.warnings)
        except json.JSONDecodeError:
            warnings = [sbom.warnings]

    return SbomStatusResponse(
        sbom_id=sbom.id,
        status=sbom.status,
        progress_step=sbom.status,
        error_detail=sbom.error_detail,
        component_count=sbom.component_count,
        warnings=warnings,
        created_at=sbom.created_at,
    )
