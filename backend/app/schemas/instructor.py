"""Schemas for instructor endpoints."""

from __future__ import annotations

from datetime import datetime

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
    confidence: float | None = None
    requires_manual_review: bool
    notes: str | None = None


class AttendanceFilters(BaseModel):
    """Query parameters for event listing."""

    verification_method: str | None = Field(default=None)
    status: str | None = Field(default=None)
    start: datetime | None = None
    end: datetime | None = None


class OverrideRequest(BaseModel):
    """Request body for override endpoint."""

    status: str = Field(..., pattern="^(present|absent)$")
    notes: str = Field(..., min_length=3, max_length=280)
