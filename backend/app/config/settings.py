"""Application configuration module for HARV backend."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEMO_STUDENT_IDS = ("001", "002", "003", "004", "005")


def _default_course_seed() -> list[dict]:
    """Combine canonical and demo course seeds."""
    base_courses = [
        {
            "id": 1,
            "code": "CS50",
            "name": "CS50 - Computer Science",
            "instructor_id": "instructor-harv",
        },
        {
            "id": 2,
            "code": "AC215",
            "name": "AC215 - Applied ML",
            "instructor_id": "instructor-ac215",
        },
        {
            "id": 3,
            "code": "STAT110",
            "name": "STAT110 - Intro Probability",
            "instructor_id": "instructor-harv",
        },
    ]
    demo_courses = [
        {
            "id": 100 + idx,
            "code": f"DEMO{student_id}",
            "name": f"Demo Class for Student {student_id}",
            "instructor_id": "instructor-harv",
        }
        for idx, student_id in enumerate(DEMO_STUDENT_IDS, start=1)
    ]
    return base_courses + demo_courses


class LectureHallBounds(BaseModel):
    """Bounding box for a lecture hall used during GPS validation."""

    min_lat: float = 42.3740
    max_lat: float = 42.3785
    min_lon: float = -71.1200
    max_lon: float = -71.1140


class Settings(BaseSettings):
    """Centralized configuration for API, database, and ML services."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="HARV_", extra="ignore")

    app_name: str = "HARV Attendance API"
    api_prefix: str = "/api"
    database_url: str = Field(
        default=f"sqlite:///{Path('backend') / 'harv.db'}", env="HARV_DATABASE_URL"
    )
    lecture_hall_bounds: LectureHallBounds = LectureHallBounds()
    vision_threshold: float = 0.65
    vision_model_metadata: Path = Path("models") / "harv_cnn_v1" / "metadata.json"
    default_courses: list[dict] = Field(default_factory=_default_course_seed)


settings = Settings()
