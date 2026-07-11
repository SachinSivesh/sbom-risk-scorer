"""SBOM ORM model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Sbom(Base):
    """An uploaded SBOM file linked to an application."""

    __tablename__ = "sboms"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    filename_stored: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False)  # cyclonedx | spdx
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="queued"
    )  # queued | parsing | analyzing | completed | parse_failed | failed
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    component_count: Mapped[int | None] = mapped_column(nullable=True)
    warnings: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of warning strings
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    application = relationship("Application", back_populates="sboms")
    dependencies = relationship("Dependency", back_populates="sbom", cascade="all, delete-orphan")
    edges = relationship("DependencyEdge", back_populates="sbom", cascade="all, delete-orphan")
    risk_report = relationship("RiskReport", back_populates="sbom", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_sboms_application_id", "application_id"),
        Index("idx_sboms_status", "status"),
    )
