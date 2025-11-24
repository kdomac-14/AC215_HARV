"""FastAPI entrypoint for HARV backend."""

from __future__ import annotations

from fastapi import FastAPI

from .api.routes import checkin, instructor
from .config.settings import settings
from .database import init_db, session_scope
from .repositories.attendance import AttendanceRepository


def create_app() -> FastAPI:
    """Factory that constructs the FastAPI instance."""
    app = FastAPI(title=settings.app_name)

    @app.get("/health", response_model=dict)
    def health() -> dict:
        """Simple service health endpoint."""
        return {
            "status": "ok",
            "app": settings.app_name,
            "lecture_hall_bounds": settings.lecture_hall_bounds.dict(),
        }

    app.include_router(checkin.router, prefix=f"{settings.api_prefix}")
    app.include_router(instructor.router, prefix=f"{settings.api_prefix}")

    @app.on_event("startup")
    def startup() -> None:
        init_db()
        with session_scope() as session:
            AttendanceRepository(session).ensure_seed_courses(settings.default_courses)

    return app


app = create_app()
