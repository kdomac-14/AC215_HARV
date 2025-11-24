"""Instructor endpoints for HARV."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from ...repositories.attendance import AttendanceRepository
from ...schemas.instructor import AttendanceEventResponse, CourseResponse, OverrideRequest
from ..deps import get_db_session

router = APIRouter(prefix="/instructor", tags=["instructor"])


@router.get("/courses", response_model=list[CourseResponse])
def list_courses(
    instructor_id: str = Query(..., example="instructor-harv"),
    session: Session = Depends(get_db_session),
) -> list[CourseResponse]:
    """List all courses for an instructor."""
    repository = AttendanceRepository(session)
    courses = repository.list_courses_for_instructor(instructor_id)
    return [CourseResponse(id=c.id, code=c.code, name=c.name) for c in courses]


@router.get("/attendance", response_model=list[AttendanceEventResponse])
def list_attendance(
    course_id: int,
    verification_method: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    start: Optional[datetime] = Query(default=None),
    end: Optional[datetime] = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[AttendanceEventResponse]:
    """Return attendance entries filtered by query params."""
    repository = AttendanceRepository(session)
    events = repository.list_events(
        course_id=course_id,
        verification_method=verification_method,
        status=status,
        start=start,
        end=end,
    )
    return [
        AttendanceEventResponse(
            id=event.id,
            student_id=event.student_id,
            course_id=event.course_id,
            instructor_id=event.instructor_id,
            timestamp=event.timestamp,
            verification_method=event.verification_method,
            status=event.status,
            confidence=event.confidence,
            requires_manual_review=event.requires_manual_review,
            notes=event.notes,
        )
        for event in events
    ]


@router.post("/attendance/{event_id}/override", response_model=AttendanceEventResponse)
def override_event(
    event_id: int,
    payload: OverrideRequest,
    session: Session = Depends(get_db_session),
) -> AttendanceEventResponse:
    """Allow an instructor to finalize the status of an attendance record."""
    repository = AttendanceRepository(session)
    try:
        event = repository.override_event(event_id, status=payload.status, notes=payload.notes)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return AttendanceEventResponse(
        id=event.id,
        student_id=event.student_id,
        course_id=event.course_id,
        instructor_id=event.instructor_id,
        timestamp=event.timestamp,
        verification_method=event.verification_method,
        status=event.status,
        confidence=event.confidence,
        requires_manual_review=event.requires_manual_review,
        notes=event.notes,
    )
