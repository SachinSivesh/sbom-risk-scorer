"""SQLAlchemy ORM models package — imports all models for Alembic discovery."""

from app.models.application import Application
from app.models.sbom import Sbom
from app.models.dependency import Dependency, DependencyEdge
from app.models.vulnerability import Vulnerability
from app.models.maintenance import MaintenanceSignal
from app.models.risk_report import RiskReport
from app.models.ai_report import AIReport

__all__ = [
    "Application",
    "Sbom",
    "Dependency",
    "DependencyEdge",
    "Vulnerability",
    "MaintenanceSignal",
    "RiskReport",
    "AIReport",
]
