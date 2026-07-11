"""Pydantic schemas for risk reports."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional, Any


class RiskReportResponse(BaseModel):
    """Full risk report response."""
    id: UUID
    sbom_id: UUID
    application_id: UUID
    overall_score: int
    category: str  # LOW | MEDIUM | HIGH | CRITICAL
    vulnerability_subscore: int
    license_subscore: int
    maintenance_subscore: int
    breakdown: Optional[dict[str, Any]] = None
    created_at: datetime
    dependencies: list["DependencyWithFindings"] = []

    model_config = {"from_attributes": True}


class DependencyWithFindings(BaseModel):
    """Dependency with its vulnerability, license, and maintenance findings."""
    id: UUID
    name: str
    version: str
    ecosystem: str
    is_direct: bool
    license_id: Optional[str] = None
    license_risk: Optional[str] = None
    repo_url: Optional[str] = None
    vulnerabilities: list["VulnerabilityItem"] = []
    maintenance_score: Optional[int] = None
    maintenance_status: Optional[str] = None


class VulnerabilityItem(BaseModel):
    """Vulnerability item within a dependency finding."""
    vuln_id: str
    severity: str
    summary: str
    fixed_version: Optional[str] = None
    source: str = "osv"


class RiskTrendPoint(BaseModel):
    """A single point in the risk trend time series."""
    sbom_id: UUID
    overall_score: int
    category: str
    created_at: datetime

    model_config = {"from_attributes": True}
