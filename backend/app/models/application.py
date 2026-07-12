"""Application ORM model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Application(Base):
    """An application whose dependencies are being analyzed."""

    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Dataset extension fields
    app_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    criticality: Mapped[str | None] = mapped_column(String(50), nullable=True)
    license_model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    business_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    deployment: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


    # Relationships
    sboms = relationship("Sbom", back_populates="application", cascade="all, delete-orphan")
    risk_reports = relationship("RiskReport", back_populates="application")

    __table_args__ = (
        Index("idx_applications_name", "name"),
        Index("idx_applications_app_id", "app_id"),
    )
