"""GPS validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from ..config.settings import LectureHallBounds


@dataclass
class GPSResult:
    """Outcome of a GPS fence evaluation."""

    within_bounds: bool
    requires_visual_verification: bool
    message: str


class GPSFence:
    """Simple bounding-box fence with buffer logic."""

    def __init__(self, bounds: LectureHallBounds, buffer_meters: float = 40.0):
        self.bounds = bounds
        # convert ~1e-5 degrees ≈ 1.11 m at Harvard lat
        self.buffer = buffer_meters * 0.00001

    def evaluate(self, latitude: float, longitude: float) -> GPSResult:
        """Check whether a coordinate is inside the lecture hall."""
        inside_lat = self.bounds.min_lat <= latitude <= self.bounds.max_lat
        inside_lon = self.bounds.min_lon <= longitude <= self.bounds.max_lon
        within = inside_lat and inside_lon
        if within:
            return GPSResult(
                within_bounds=True,
                requires_visual_verification=False,
                message="GPS location confirmed within lecture hall.",
            )

        # Determine if user is close to the fence (for a more specific message).
        lat_buffer = (
            (self.bounds.min_lat - self.buffer) <= latitude <= (self.bounds.max_lat + self.buffer)
        )
        lon_buffer = (
            (self.bounds.min_lon - self.buffer) <= longitude <= (self.bounds.max_lon + self.buffer)
        )
        near = lat_buffer and lon_buffer
        message = (
            "Location close to hall, please use visual verification."
            if near
            else "GPS location outside of lecture hall bounds. Please verify with a photo of the classroom."
        )
        # Always require visual verification when outside bounds
        return GPSResult(
            within_bounds=False,
            requires_visual_verification=True,
            message=message,
        )

    @staticmethod
    def as_tuple(bounds: LectureHallBounds) -> tuple[float, float, float, float]:
        """Expose bounds as tuple for testing."""
        return (bounds.min_lat, bounds.max_lat, bounds.min_lon, bounds.max_lon)

    @staticmethod
    def distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Rough Euclidean distance for educational demos."""
        return sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)
