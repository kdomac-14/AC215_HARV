"""FastAPI entrypoint for HARV backend."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from .api.routes import checkin, instructor
from .config.settings import settings
from .database import init_db, session_scope
from .repositories.attendance import AttendanceRepository

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Factory that constructs the FastAPI instance."""
    app = FastAPI(title=settings.app_name)

    @app.get("/health", response_model=dict)
    def health() -> dict:
        """Simple service health endpoint."""
        from backend.ml.model_loader import get_model_info

        model_info = get_model_info()
        return {
            "ok": True,
            "app": settings.app_name,
            "version": settings.app_version,
            "lecture_hall_bounds": settings.lecture_hall_bounds.model_dump(),
            "demo_courses": [course["code"] for course in settings.default_courses],
            "vision_model": (
                {
                    "name": model_info.get("model_name"),
                    "accuracy": model_info.get("accuracy"),
                    "last_updated": model_info.get("last_updated"),
                }
                if model_info
                else None
            ),
        }

    app.include_router(checkin.router, prefix=f"{settings.api_prefix}")
    app.include_router(instructor.router, prefix=f"{settings.api_prefix}")

    @app.on_event("startup")
    def startup() -> None:
        from backend.ml.model_loader import log_model_version

        init_db()
        with session_scope() as session:
            AttendanceRepository(session).ensure_seed_courses(settings.default_courses)

        # Log the promoted vision model version
        model_info = log_model_version()
        if model_info:
            logger.info(f"Backend started with vision model: {model_info.get('model_name')}")

    return app


app = create_app()
