"""Common FastAPI dependencies."""

from __future__ import annotations

from collections.abc import Iterator

from sqlmodel import Session

from ..database import get_session


def get_db_session() -> Iterator[Session]:
    """Expose database session for dependency injection."""
    yield from get_session()
