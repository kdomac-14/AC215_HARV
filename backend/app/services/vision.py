"""Wrapper around the lightweight ML model used for visual verification."""

from __future__ import annotations

import base64
from dataclasses import dataclass

from backend.ml.model_loader import VisionModel

from ..config.settings import settings


@dataclass
class VisionResult:
    """Outcome of running the light-weight CNN."""

    is_match: bool
    confidence: float


class VisionService:
    """Decodes payloads and delegates to the model loader."""

    def __init__(self, model: VisionModel | None = None):
        self.model = model or VisionModel(
            metadata_path=settings.vision_model_metadata, threshold=settings.vision_threshold
        )

    def evaluate(self, image_b64: str) -> VisionResult:
        """Decode base64 image and score it using the CNN loader."""
        image_bytes = base64.b64decode(image_b64, validate=True)
        is_match, confidence = self.model.verify(image_bytes)
        return VisionResult(is_match=is_match, confidence=confidence)
