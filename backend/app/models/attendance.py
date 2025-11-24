"""SQLModel models representing courses and attendance events."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Course(SQLModel, table=True):
    """Course metadata for instructor views."""

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str
    name: str
    instructor_id: str


class AttendanceEvent(SQLModel, table=True):
    """Attendance record generated from GPS or vision verification."""

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str
    course_id: int = Field(foreign_key="course.id")
    instructor_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    verification_method: str
    status: str = "pending"
    confidence: Optional[float] = None
    requires_manual_review: bool = False
    notes: Optional[str] = None
