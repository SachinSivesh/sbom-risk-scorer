"""Pydantic schemas for AI-generated reports."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class AIReportAction(BaseModel):
    """A single prioritized remediation action."""
    title: str
    description: str
    priority: str  # HIGH | MEDIUM | LOW


class AIReportResponse(BaseModel):
    """AI-generated remediation summary response."""
    id: UUID
    risk_report_id: UUID
    summary: str
    top_actions: list[AIReportAction] = []
    model_used: str
    fallback_used: bool
    created_at: datetime

    model_config = {"from_attributes": True}
