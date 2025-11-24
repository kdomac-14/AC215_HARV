"""SQLModel models representing courses and attendance events."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class Course(SQLModel, table=True):
    """Course metadata for instructor views."""

    id: int | None = Field(default=None, primary_key=True)
    code: str
    name: str
    instructor_id: str


class AttendanceEvent(SQLModel, table=True):
    """Attendance record generated from GPS or vision verification."""

    id: int | None = Field(default=None, primary_key=True)
    student_id: str
    course_id: int = Field(foreign_key="course.id")
    instructor_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    latitude: float | None = None
    longitude: float | None = None
    verification_method: str
    status: str = "pending"
    confidence: float | None = None
    requires_manual_review: bool = False
    notes: str | None = None
