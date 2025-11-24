"""Schemas for instructor endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CourseResponse(BaseModel):
    """Expose courses for instructor dashboards."""

    id: int
    code: str
    name: str


class AttendanceEventResponse(BaseModel):
    """Expose event data to the dashboard."""

    id: int
    student_id: str
    course_id: int
    instructor_id: str
    timestamp: datetime
    verification_method: str
    status: str
    confidence: Optional[float] = None
    requires_manual_review: bool
    notes: Optional[str] = None


class AttendanceFilters(BaseModel):
    """Query parameters for event listing."""

    verification_method: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class OverrideRequest(BaseModel):
    """Request body for override endpoint."""

    status: str = Field(..., pattern="^(present|absent)$")
    notes: str = Field(..., min_length=3, max_length=280)
