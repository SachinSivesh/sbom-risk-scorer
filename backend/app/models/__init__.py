"""SQLAlchemy ORM models package — imports all models for Alembic discovery."""

from app.models.application import Application
from app.models.sbom import Sbom
from app.models.dependency import Dependency, DependencyEdge
from app.models.vulnerability import Vulnerability
from app.models.maintenance import MaintenanceSignal
from app.models.risk_report import RiskReport
from app.models.ai_report import AIReport
from app.models.license_rule import LicenseRule
from app.models.vulnerability_ref import VulnerabilityRef
from app.models.dependency_label import DependencyLabelRef
from app.models.sbom_dependency_ref import SbomDependencyRef
from app.models.transitive_dependency_ref import TransitiveDependencyRef

__all__ = [
    "Application",
    "Sbom",
    "Dependency",
    "DependencyEdge",
    "Vulnerability",
    "MaintenanceSignal",
    "RiskReport",
    "AIReport",
    "LicenseRule",
    "VulnerabilityRef",
    "DependencyLabelRef",
    "SbomDependencyRef",
    "TransitiveDependencyRef",
]
