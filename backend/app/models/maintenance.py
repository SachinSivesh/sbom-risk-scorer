"""MaintenanceSignal ORM model."""

import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class MaintenanceSignal(Base):
    """Maintenance health signals for a dependency's source repository."""

    __tablename__ = "maintenance_signals"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    dependency_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dependencies.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    last_commit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stars: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    release_frequency_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    maintenance_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="UNKNOWN"
    )  # OK | REPO_NOT_FOUND | UNKNOWN | RATE_LIMITED

    # Relationships
    dependency = relationship("Dependency", back_populates="maintenance_signal")
