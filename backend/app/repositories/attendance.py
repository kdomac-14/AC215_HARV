"""Repository helper for persisting attendance events."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from sqlmodel import Session, select

from ..models.attendance import AttendanceEvent, Course


class AttendanceRepository:
    """Encapsulates CRUD operations for attendance domain objects."""

    def __init__(self, session: Session):
        self.session = session

    def ensure_seed_courses(self, seed_courses: Iterable[dict]) -> None:
        """Ensure default courses exist and stay in sync with seed config."""
        existing_courses = {course.code: course for course in self.session.exec(select(Course))}
        mutated = False

        for course in seed_courses:
            code = course["code"]
            current = existing_courses.get(code)
            if current:
                if current.name != course["name"] or current.instructor_id != course["instructor_id"]:
                    current.name = course["name"]
                    current.instructor_id = course["instructor_id"]
                    self.session.add(current)
                    mutated = True
                continue

            self.session.add(Course(**course))
            mutated = True

        if mutated:
            self.session.commit()

    def create_event(
        self,
        *,
        student_id: str,
        course_id: int,
        instructor_id: str,
        verification_method: str,
        status: str,
        latitude: float | None = None,
        longitude: float | None = None,
        requires_manual_review: bool = False,
        confidence: float | None = None,
        notes: str | None = None,
        timestamp: datetime | None = None,
    ) -> AttendanceEvent:
        """Persist a new attendance event."""
        event = AttendanceEvent(
            student_id=student_id,
            course_id=course_id,
            instructor_id=instructor_id,
            verification_method=verification_method,
            status=status,
            latitude=latitude,
            longitude=longitude,
            requires_manual_review=requires_manual_review,
            confidence=confidence,
            notes=notes,
            timestamp=timestamp or datetime.now(tz=timezone.utc),
        )
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def list_courses_for_instructor(self, instructor_id: str) -> list[Course]:
        """Return all courses the instructor can manage."""
        statement = select(Course).where(Course.instructor_id == instructor_id)
        return list(self.session.exec(statement))

    def list_events(
        self,
        *,
        course_id: int,
        verification_method: str | None = None,
        status: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[AttendanceEvent]:
        """Retrieve attendance events for instructor dashboards."""
        statement = select(AttendanceEvent).where(AttendanceEvent.course_id == course_id)
        if verification_method:
            statement = statement.where(AttendanceEvent.verification_method == verification_method)
        if status:
            statement = statement.where(AttendanceEvent.status == status)
        if start:
            statement = statement.where(AttendanceEvent.timestamp >= start)
        if end:
            statement = statement.where(AttendanceEvent.timestamp <= end)
        return list(self.session.exec(statement))

    def override_event(self, event_id: int, *, status: str, notes: str | None) -> AttendanceEvent:
        """Allow instructors to manually update an event."""
        event = self.session.get(AttendanceEvent, event_id)
        if not event:
            raise ValueError(f"Attendance event {event_id} not found")
        event.status = status
        event.notes = notes
        event.requires_manual_review = False
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event
