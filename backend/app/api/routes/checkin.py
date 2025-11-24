"""Student-facing check-in endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ...config.settings import settings
from ...repositories.attendance import AttendanceRepository
from ...schemas.checkin import (
    CheckInResponse,
    GPSCheckInRequest,
    VisionCheckInRequest,
)
from ...services.checkin import CheckInService
from ...services.gps import GPSFence
from ...services.vision import VisionService
from ..deps import get_db_session

router = APIRouter(prefix="/checkin", tags=["check-in"])

gps_fence = GPSFence(settings.lecture_hall_bounds)
vision_service = VisionService()


@router.post("/gps", response_model=CheckInResponse)
def gps_checkin(
    payload: GPSCheckInRequest, session: Session = Depends(get_db_session)
) -> CheckInResponse:
    """Accept GPS coordinates and store an attendance record."""
    repository = AttendanceRepository(session)
    service = CheckInService(
        repository=repository,
        gps_fence=gps_fence,
        vision_service=vision_service,
    )
    event, gps_result = service.handle_gps_checkin(
        student_id=payload.student_id,
        course_id=payload.course_id,
        instructor_id=payload.instructor_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        timestamp=payload.timestamp,
    )
    message = gps_result.message
    return CheckInResponse(
        status=event.status,
        message=message,
        record_id=event.id,
        requires_visual_verification=gps_result.requires_visual_verification,
    )


@router.post("/vision", response_model=CheckInResponse)
def vision_checkin(
    payload: VisionCheckInRequest, session: Session = Depends(get_db_session)
) -> CheckInResponse:
    """Fallback endpoint that verifies a student-provided capture."""
    if not payload.image_b64:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image payload missing")

    repository = AttendanceRepository(session)
    service = CheckInService(
        repository=repository,
        gps_fence=gps_fence,
        vision_service=vision_service,
    )
    event, vision_result = service.handle_vision_checkin(
        student_id=payload.student_id,
        course_id=payload.course_id,
        instructor_id=payload.instructor_id,
        image_b64=payload.image_b64,
        timestamp=payload.timestamp,
    )
    message = (
        "Visual verification accepted" if vision_result.is_match else "Scan did not match professor"
    )
    return CheckInResponse(
        status=event.status,
        message=message,
        record_id=event.id,
        requires_visual_verification=not vision_result.is_match,
        confidence=vision_result.confidence,
    )
