"""Pydantic schemas for Application requests/responses."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional


class ApplicationCreate(BaseModel):
    """Request body for creating an application."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ApplicationResponse(BaseModel):
    """Response body for an application."""
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationListItem(BaseModel):
    """Application summary for the portfolio view."""
    id: UUID
    name: str
    description: Optional[str] = None
    latest_score: Optional[int] = None
    latest_category: Optional[str] = None
    last_analyzed_at: Optional[datetime] = None
    sbom_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplicationDetail(BaseModel):
    """Full application detail with SBOM history."""
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    sboms: list["SbomSummary"] = []

    model_config = {"from_attributes": True}


class SbomSummary(BaseModel):
    """Brief SBOM info for application detail view."""
    id: UUID
    original_filename: str
    format: str
    status: str
    component_count: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}
