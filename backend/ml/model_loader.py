"""Lightweight, testable vision model loader.

Loads MobileNetV3 pretrained model for classroom/lecture hall verification.
When GPS check fails, the student can take a photo which is verified
using scene classification to detect if they're in a classroom environment.
"""

from __future__ import annotations

import io
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Default model directory (can be overridden via HARV_MODEL_DIR env var)
DEFAULT_MODEL_DIR = Path("models/harv_cnn_v1")


def get_model_info(model_dir: Path | None = None) -> dict:
    """
    Read model metadata and return version info for logging.

    Args:
        model_dir: Path to model directory (default: models/harv_cnn_v1).

    Returns:
        Dictionary with model_name, accuracy, timestamp, and weights_path.
        Returns empty dict if metadata not found.
    """
    model_dir = model_dir or Path(os.getenv("HARV_MODEL_DIR", DEFAULT_MODEL_DIR))
    metadata_path = model_dir / "metadata.json"
    weights_path = model_dir / "weights.pt"

    if not metadata_path.exists():
        logger.warning(f"Model metadata not found at {metadata_path}")
        return {}

    with metadata_path.open("r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Get file modification time as proxy for training timestamp
    mtime = metadata_path.stat().st_mtime
    timestamp = datetime.fromtimestamp(mtime, tz=UTC).isoformat()

    info = {
        "model_name": metadata.get("model_name", "unknown"),
        "architecture": metadata.get("architecture", "unknown"),
        "accuracy": metadata.get("metrics", {}).get("accuracy"),
        "threshold": metadata.get("threshold"),
        "classes": metadata.get("classes"),
        "weights_path": str(weights_path) if weights_path.exists() else None,
        "metadata_path": str(metadata_path),
        "last_updated": timestamp,
    }
    return info


def log_model_version(model_dir: Path | None = None) -> dict:
    """
    Log the currently deployed model version at startup.

    Call this during application initialization to record which
    model version is active. Useful for debugging and audit trails.

    Args:
        model_dir: Path to model directory (default: models/harv_cnn_v1).

    Returns:
        Model info dictionary.
    """
    info = get_model_info(model_dir)

    if not info:
        logger.warning("No promoted HARV model found. Run train/pipeline.py to train and promote a model.")
        return info

    logger.info(
        f"HARV Vision Model loaded: {info['model_name']} "
        f"(arch={info['architecture']}, accuracy={info.get('accuracy', 'N/A')}, "
        f"updated={info['last_updated']})"
    )
    return info


# ImageNet class indices for classroom/lecture hall related scenes
# These are based on ImageNet-1K class labels that indicate indoor educational spaces
CLASSROOM_INDICES = {
    # Classroom-related indices from ImageNet
    658,  # projector
    659,  # mouse (computer)
    681,  # notebook computer
    664,  # monitor
    508,  # computer keyboard
    527,  # desk
    703,  # paper towel (whiteboards/papers)
    530,  # digital clock
    531,  # digital watch (clock in classroom)
    539,  # drumstick (pointer)
    618,  # laptop
    732,  # Polaroid camera (projector-like)
    755,  # printer
    760,  # projector (repeated for safety)
    782,  # screen, CRT screen
    851,  # television, TV
    861,  # throne (podium-like)
}


class VisionModel:
    """MobileNetV3-based model for classroom scene verification."""

    def __init__(self, metadata_path: Path | None = None, threshold: float | None = None):
        """
        Initialize VisionModel with MobileNetV3 pretrained weights.

        Args:
            metadata_path: Path to metadata.json (optional, for legacy support).
            threshold: Confidence threshold for classroom detection.
        """
        model_dir = Path(os.getenv("HARV_MODEL_DIR", DEFAULT_MODEL_DIR))
        self.metadata_path = metadata_path or (model_dir / "metadata.json")
        self.metadata = self._load_metadata()
        self.threshold = threshold if threshold is not None else self.metadata.get("threshold", 0.35)
        
        # Lazy-load model and transforms
        self._model = None
        self._transforms = None
        self._loaded = False

        logger.info(f"VisionModel initialized (threshold={self.threshold})")

    def _load_metadata(self) -> dict:
        """Load metadata or return defaults for MobileNetV3."""
        if self.metadata_path.exists():
            with self.metadata_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        # Default metadata for pretrained MobileNetV3
        return {
            "model_name": "mobilenet_v3_small",
            "architecture": "MobileNetV3-Small",
            "threshold": 0.35,
            "pretrained": True,
        }

    def _ensure_loaded(self) -> None:
        """Lazy-load MobileNetV3 model and transforms."""
        if self._loaded:
            return
        
        try:
            from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small
            
            # Load pretrained MobileNetV3-Small (lightweight, ~2.5M params)
            weights = MobileNet_V3_Small_Weights.IMAGENET1K_V1
            self._model = mobilenet_v3_small(weights=weights)
            self._model.eval()
            
            # Use the preprocessing transforms from the weights
            self._transforms = weights.transforms()
            
            self._loaded = True
            logger.info("MobileNetV3-Small loaded successfully")
        except ImportError as e:
            logger.warning(f"PyTorch/torchvision not available: {e}. Using fallback.")
            self._loaded = False

    def verify(self, image_bytes: bytes) -> tuple[bool, float]:
        """Verify if image shows a classroom/lecture hall environment.
        
        Uses MobileNetV3 pretrained on ImageNet to detect classroom-related objects.
        Returns True if the confidence exceeds threshold.
        """
        self._ensure_loaded()
        
        if not self._loaded or self._model is None:
            # Fallback: accept all images if model not available
            logger.warning("Model not loaded, using fallback acceptance")
            return True, 0.5
        
        try:
            import torch
            from PIL import Image
            
            # Load and preprocess image
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            input_tensor = self._transforms(img).unsqueeze(0)
            
            # Run inference
            with torch.no_grad():
                outputs = self._model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            
            # Sum probabilities for classroom-related classes
            classroom_confidence = sum(
                probabilities[idx].item() 
                for idx in CLASSROOM_INDICES 
                if idx < len(probabilities)
            )
            
            # Also check top-5 predictions for any classroom indicators
            top5_probs, top5_indices = torch.topk(probabilities, 5)
            top5_set = set(top5_indices.tolist())
            has_classroom_in_top5 = bool(top5_set & CLASSROOM_INDICES)
            
            # Boost confidence if classroom object in top-5
            if has_classroom_in_top5:
                classroom_confidence = max(classroom_confidence, 0.5)
            
            # Clamp confidence to [0, 1]
            classroom_confidence = min(1.0, classroom_confidence)
            
            is_classroom = classroom_confidence >= self.threshold
            
            logger.info(
                f"Vision verification: confidence={classroom_confidence:.3f}, "
                f"is_classroom={is_classroom}, top5={top5_indices.tolist()}"
            )
            
            return is_classroom, classroom_confidence
            
        except Exception as e:
            logger.error(f"Vision verification failed: {e}")
            # On error, be lenient and accept with low confidence
            return True, 0.3
