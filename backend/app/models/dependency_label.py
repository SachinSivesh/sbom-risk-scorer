from sqlalchemy import String, Boolean, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class DependencyLabelRef(Base):
    """Reference dependency security labels model from dependency_labels.csv."""

    __tablename__ = "reference_dependency_labels"

    dep_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    application_id: Mapped[str] = mapped_column(String(50), nullable=False)
    library: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    is_risky: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_type: Mapped[str | None] = mapped_column(String(100), nullable=True)  # VULNERABLE_DEPENDENCY | UNMAINTAINED | NONE
    severity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_ref_dep_labels_app_id", "application_id"),
    )
