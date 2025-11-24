"""Unit tests for GPS fence logic."""

from __future__ import annotations

from backend.app.config.settings import LectureHallBounds
from backend.app.services.gps import GPSFence


def test_gps_inside_bounds():
    bounds = LectureHallBounds(min_lat=0, max_lat=1, min_lon=0, max_lon=1)
    fence = GPSFence(bounds)
    result = fence.evaluate(0.5, 0.5)
    assert result.within_bounds is True
    assert result.requires_visual_verification is False


def test_gps_requires_visual_review():
    bounds = LectureHallBounds(min_lat=0, max_lat=1, min_lon=0, max_lon=1)
    fence = GPSFence(bounds, buffer_meters=20000)
    result = fence.evaluate(1.2, 1.2)
    assert result.within_bounds is False
    assert result.requires_visual_verification is True


def test_gps_outside_bounds():
    bounds = LectureHallBounds(min_lat=0, max_lat=1, min_lon=0, max_lon=1)
    fence = GPSFence(bounds, buffer_meters=1)
    result = fence.evaluate(5, 5)
    assert result.within_bounds is False
    assert result.requires_visual_verification is False
