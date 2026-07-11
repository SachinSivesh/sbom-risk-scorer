"""Pydantic schemas for dependencies."""

from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class DependencyResponse(BaseModel):
    """Response body for a single dependency."""
    id: UUID
    name: str
    version: str
    ecosystem: str
    purl: Optional[str] = None
    license_id: Optional[str] = None
    is_direct: bool
    repo_url: Optional[str] = None

    model_config = {"from_attributes": True}
