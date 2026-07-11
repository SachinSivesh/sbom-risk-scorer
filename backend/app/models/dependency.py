"""Dependency and DependencyEdge ORM models."""

import uuid
from sqlalchemy import String, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Dependency(Base):
    """A single software dependency extracted from an SBOM."""

    __tablename__ = "dependencies"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    sbom_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sboms.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    ecosystem: Mapped[str] = mapped_column(
        String(50), nullable=False, default="unknown"
    )  # npm | pypi | maven | go | cargo | rubygems | nuget | unknown
    purl: Mapped[str | None] = mapped_column(String(500), nullable=True)
    license_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_direct: Mapped[bool] = mapped_column(Boolean, default=False)
    repo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    sbom = relationship("Sbom", back_populates="dependencies")
    vulnerabilities = relationship(
        "Vulnerability", back_populates="dependency", cascade="all, delete-orphan"
    )
    maintenance_signal = relationship(
        "MaintenanceSignal", back_populates="dependency", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_dependencies_sbom_id", "sbom_id"),
        Index("idx_dependencies_name_version", "name", "version"),
    )


class DependencyEdge(Base):
    """A directed edge in the dependency graph (from → to)."""

    __tablename__ = "dependency_edges"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    sbom_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sboms.id", ondelete="CASCADE"), nullable=False
    )
    from_dependency_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dependencies.id"), nullable=False
    )
    to_dependency_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dependencies.id"), nullable=False
    )

    # Relationships
    sbom = relationship("Sbom", back_populates="edges")

    __table_args__ = (
        Index("idx_edges_sbom_id", "sbom_id"),
        UniqueConstraint("from_dependency_id", "to_dependency_id", name="uq_edge_pair"),
    )
