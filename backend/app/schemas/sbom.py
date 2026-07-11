"""Pydantic schemas for SBOM upload and status."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class SbomUploadResponse(BaseModel):
    """Response for SBOM upload."""
    sbom_id: UUID
    status: str

    model_config = {"from_attributes": True}


class SbomStatusResponse(BaseModel):
    """Response for SBOM status polling."""
    sbom_id: UUID
    status: str
    progress_step: Optional[str] = None
    error_detail: Optional[str] = None
    component_count: Optional[int] = None
    warnings: Optional[list[str]] = None
    created_at: datetime

    model_config = {"from_attributes": True}
