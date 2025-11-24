"""Domain services orchestrating GPS and vision check-ins."""

from __future__ import annotations

from datetime import datetime

from ..repositories.attendance import AttendanceRepository
from ..services.gps import GPSFence
from ..services.vision import VisionResult, VisionService


class CheckInService:
    """Coordinates validation logic and persistence."""

    def __init__(
        self,
        *,
        repository: AttendanceRepository,
        gps_fence: GPSFence,
        vision_service: VisionService,
    ):
        self.repository = repository
        self.gps_fence = gps_fence
        self.vision_service = vision_service

    def handle_gps_checkin(
        self,
        *,
        student_id: str,
        course_id: int,
        instructor_id: str,
        latitude: float,
        longitude: float,
        timestamp: datetime,
    ):
        """Validate GPS coordinates and store a record."""
        gps_result = self.gps_fence.evaluate(latitude=latitude, longitude=longitude)
        status = "present" if gps_result.within_bounds else "pending"
        event = self.repository.create_event(
            student_id=student_id,
            course_id=course_id,
            instructor_id=instructor_id,
            verification_method="gps",
            status=status,
            latitude=latitude,
            longitude=longitude,
            requires_manual_review=gps_result.requires_visual_verification,
            timestamp=timestamp,
            notes=gps_result.message,
        )
        return event, gps_result

    def handle_vision_checkin(
        self,
        *,
        student_id: str,
        course_id: int,
        instructor_id: str,
        image_b64: str,
        timestamp: datetime,
    ):
        """Score an uploaded image and persist the event."""
        result: VisionResult = self.vision_service.evaluate(image_b64)
        status = "present" if result.is_match else "rejected"
        event = self.repository.create_event(
            student_id=student_id,
            course_id=course_id,
            instructor_id=instructor_id,
            verification_method="vision",
            status=status,
            confidence=result.confidence,
            requires_manual_review=not result.is_match and result.confidence >= 0.5,
            timestamp=timestamp,
        )
        return event, result
