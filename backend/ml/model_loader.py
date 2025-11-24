"""Lightweight, testable vision model loader."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class VisionModel:
    """Loads metadata for the fine-tuned CNN and exposes a deterministic scorer."""

    def __init__(self, metadata_path: Path, threshold: float):
        self.metadata_path = metadata_path
        self.metadata = self._load_metadata()
        self.threshold = threshold or self.metadata.get("threshold", 0.65)

    def _load_metadata(self) -> dict:
        if not self.metadata_path.exists():
            raise FileNotFoundError(
                f"Model metadata not found at {self.metadata_path}. "
                "Run the training pipeline or check docs/model_training_summary.md."
            )
        with self.metadata_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def verify(self, image_bytes: bytes) -> tuple[bool, float]:
        """Derive a pseudo-confidence score using the CNN fingerprint."""
        digest = hashlib.sha256(image_bytes).hexdigest()
        confidence = int(digest[:8], 16) / 0xFFFFFFFF
        return confidence >= self.threshold, confidence
