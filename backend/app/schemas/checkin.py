"""Request/response models for student check-ins."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GPSCheckInRequest(BaseModel):
    """Payload submitted when a student performs a GPS check-in."""

    student_id: str = Field(..., example="student123")
    course_id: int = Field(..., example=1)
    instructor_id: str = Field(..., example="instructor-harv")
    device_id: str = Field(..., example="ios-123")
    latitude: float = Field(..., example=42.3765)
    longitude: float = Field(..., example=-71.1167)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VisionCheckInRequest(BaseModel):
    """Payload for visual verification."""

    student_id: str
    course_id: int
    instructor_id: str
    image_b64: str = Field(..., description="Base64 encoded capture from the student app.")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CheckInResponse(BaseModel):
    """Shared response for both GPS and vision flows."""

    status: str
    message: str
    record_id: int
    requires_visual_verification: bool = False
    confidence: Optional[float] = None
