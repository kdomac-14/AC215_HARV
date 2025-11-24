"""Repository tests validate persistence logic."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session, SQLModel, create_engine, select

from backend.app.models.attendance import Course
from backend.app.repositories.attendance import AttendanceRepository


def get_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    session.add(
        Course(id=1, code="CS50", name="CS50", instructor_id="instructor-harv"),
    )
    session.commit()
    return session


def test_create_and_override_event():
    session = get_session()
    repo = AttendanceRepository(session)
    event = repo.create_event(
        student_id="student",
        course_id=1,
        instructor_id="instructor-harv",
        verification_method="gps",
        status="present",
        timestamp=datetime.now(tz=timezone.utc),
    )
    assert event.id is not None

    updated = repo.override_event(event.id, status="absent", notes="Manual adjustment")
    assert updated.status == "absent"
    assert updated.notes == "Manual adjustment"


def test_ensure_seed_courses_upserts_missing_entries():
    session = get_session()
    repo = AttendanceRepository(session)
    seed = [
        {"id": 1, "code": "CS50", "name": "CS50 - Intro to CS", "instructor_id": "instructor-harv"},
        {
            "id": 99,
            "code": "DEMO001",
            "name": "Demo Class for Student 001",
            "instructor_id": "instructor-harv",
        },
    ]
    repo.ensure_seed_courses(seed)

    courses = session.exec(select(Course)).all()
    mapping = {course.code: course for course in courses}
    assert mapping["CS50"].name == "CS50 - Intro to CS"
    assert mapping["DEMO001"].instructor_id == "instructor-harv"
