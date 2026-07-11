"""AIReport ORM model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AIReport(Base):
    """AI-generated remediation summary for a risk report."""

    __tablename__ = "ai_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    risk_report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("risk_reports.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    top_actions_json: Mapped[list] = mapped_column(JSON, nullable=True)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    risk_report = relationship("RiskReport", back_populates="ai_report")
