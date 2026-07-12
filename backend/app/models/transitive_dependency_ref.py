import uuid
from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class TransitiveDependencyRef(Base):
    """Reference transitive dependency mapping model from transitive_dependencies.json."""

    __tablename__ = "reference_transitive_dependencies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    parent_library: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_version: Mapped[str] = mapped_column(String(100), nullable=False)
    child_library: Mapped[str] = mapped_column(String(255), nullable=False)
    child_version: Mapped[str] = mapped_column(String(100), nullable=False)
    application_id: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        Index("idx_ref_trans_deps_app_id", "application_id"),
    )
