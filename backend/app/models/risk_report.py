"""RiskReport ORM model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, ForeignKey, Index, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class RiskReport(Base):
    """Computed risk report for an SBOM analysis."""

    __tablename__ = "risk_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    sbom_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sboms.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id"), nullable=False
    )
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-100
    category: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # LOW | MEDIUM | HIGH | CRITICAL
    vulnerability_subscore: Mapped[int] = mapped_column(Integer, nullable=False)
    license_subscore: Mapped[int] = mapped_column(Integer, nullable=False)
    maintenance_subscore: Mapped[int] = mapped_column(Integer, nullable=False)
    breakdown_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    sbom = relationship("Sbom", back_populates="risk_report")
    application = relationship("Application", back_populates="risk_reports")
    ai_report = relationship("AIReport", back_populates="risk_report", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_risk_reports_application_id_created_at", "application_id", "created_at"),
    )
