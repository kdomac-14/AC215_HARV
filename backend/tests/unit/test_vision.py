"""Unit tests for the deterministic model loader."""

from __future__ import annotations

import base64
from pathlib import Path

from backend.app.services.vision import VisionService
from backend.ml.model_loader import VisionModel


def test_vision_model_scoring(tmp_path: Path):
    """Model returns deterministic confidence for identical images."""
    metadata = tmp_path / "metadata.json"
    metadata.write_text('{"threshold": 0.5}', encoding="utf-8")
    model = VisionModel(metadata_path=metadata, threshold=0.5)
    image = b"vision-bytes"
    first = model.verify(image)
    second = model.verify(image)
    assert first == second


def test_vision_service_returns_result(tmp_path: Path):
    metadata = tmp_path / "metadata.json"
    metadata.write_text('{"threshold": 0.1}', encoding="utf-8")
    service = VisionService(model=VisionModel(metadata_path=metadata, threshold=0.1))
    payload = base64.b64encode(b"another-image").decode("utf-8")
    result = service.evaluate(payload)
    assert 0 <= result.confidence <= 1
