"""Shared pytest fixtures for backend tests."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from backend.app import database
from backend.app.config.settings import settings
from backend.app.main import create_app
from backend.app.repositories.attendance import AttendanceRepository


@pytest.fixture(name="test_engine")
def fixture_test_engine(tmp_path: Path):
    """Create an isolated SQLite engine for tests."""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="db_session")
def fixture_db_session(test_engine):
    """Provide a session bound to the test engine."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture(name="client")
def fixture_client(test_engine):
    """Spin up the FastAPI TestClient with overridden DB dependencies."""
    database.engine = test_engine
    app = create_app()

    with Session(test_engine) as session:
        AttendanceRepository(session).ensure_seed_courses(settings.default_courses)

    client = TestClient(app)
    return client


@pytest.fixture(name="sample_image_b64")
def fixture_sample_image_b64() -> str:
    """Generate deterministic base64 content for tests."""
    data = b"synthetic-image-content"
    return base64.b64encode(data).decode("utf-8")
