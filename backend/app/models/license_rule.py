from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class LicenseRule(Base):
    """Offline license rules compatibility matrix database model."""

    __tablename__ = "license_rules"

    license: Mapped[str] = mapped_column(String(100), primary_key=True)
    spdx: Mapped[str | None] = mapped_column(String(100), nullable=True)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False)  # LOW | MEDIUM | HIGH | CRITICAL
    compatible_with_proprietary: Mapped[bool] = mapped_column(Boolean, default=True)
    viral: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
