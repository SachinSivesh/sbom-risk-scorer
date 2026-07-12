from datetime import date
from sqlalchemy import String, Date, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class SbomDependencyRef(Base):
    """Reference direct dependencies list model from sbom_dependencies.csv."""

    __tablename__ = "reference_sbom_dependencies"

    dep_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    application_id: Mapped[str] = mapped_column(String(50), nullable=False)
    application_name: Mapped[str] = mapped_column(String(255), nullable=False)
    library: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    license: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dependency_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # direct
    last_updated: Mapped[date | None] = mapped_column(Date, nullable=True)
    transitive_deps: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_ref_sbom_deps_app_id", "application_id"),
    )
