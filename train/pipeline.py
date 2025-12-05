"""
Production training pipeline for HARV vision models.

This module coordinates training, evaluation, and conditional model promotion.
It is designed to be called from CI pipelines or Vertex AI training jobs.

Usage:
    python -m train.pipeline --config ml/configs/harv_vision_v1.yaml --min_accuracy 0.8

The pipeline:
    1. Runs training to a staging directory
    2. Loads fresh metrics and compares against prior best
    3. Promotes the new model if it meets thresholds
    4. Logs all decisions for auditability

Author: HARV Team
License: MIT
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

# Configure logging for CI/Vertex AI visibility
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("harv.pipeline")


def load_metrics(path: Path) -> dict[str, Any] | None:
    """
    Load metrics from a JSON file.

    Args:
        path: Path to the metrics JSON file.

    Returns:
        Dictionary of metrics, or None if file doesn't exist.
    """
    if not path.exists():
        logger.info(f"Metrics file not found: {path}")
        return None
    
    with path.open("r", encoding="utf-8") as f:
        metrics = json.load(f)
    logger.info(f"Loaded metrics from {path}: accuracy={metrics.get('accuracy', 'N/A')}")
    return metrics


def save_metrics(metrics: dict[str, Any], path: Path) -> None:
    """
    Save metrics to a JSON file.

    Args:
        metrics: Dictionary of metrics to save.
        path: Destination path for the JSON file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {path}")


def run_training(config_path: Path, staging_dir: Path) -> dict[str, Any]:
    """
    Execute the training routine and return metrics.

    Imports ml.train_cnn and runs training with output redirected
    to a staging directory to avoid overwriting production weights
    until validation passes.

    Args:
        config_path: Path to the YAML configuration file.
        staging_dir: Directory for staging model outputs.

    Returns:
        Dictionary containing training metrics.

    Raises:
        ImportError: If ml.train_cnn cannot be imported.
        RuntimeError: If training fails.
    """
    try:
        from ml.train_cnn import Config, train
    except ImportError as e:
        logger.error(f"Failed to import ml.train_cnn: {e}")
        logger.info("Ensure you're running from the repository root directory.")
        raise

    logger.info(f"Loading config from {config_path}")
    cfg = Config.from_yaml(config_path)

    # Override output paths to use staging directory
    staging_output = staging_dir / "model"
    staging_metrics = staging_dir / "metrics.json"
    
    cfg = replace(cfg, output_dir=staging_output, metrics_path=staging_metrics)
    
    logger.info(f"Training with staging output: {staging_output}")
    logger.info(f"Config: epochs={cfg.epochs}, lr={cfg.learning_rate}, batch_size={cfg.batch_size}")

    try:
        metrics = train(cfg)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise RuntimeError(f"Training execution failed: {e}") from e

    logger.info(f"Training complete. Metrics: {metrics}")
    return metrics


def promote_model(
    staging_dir: Path,
    production_dir: Path,
    metrics: dict[str, Any],
    best_metrics_path: Path,
) -> None:
    """
    Promote staged model to production by copying weights and updating best metrics.

    Args:
        staging_dir: Directory containing staged model outputs.
        production_dir: Production model directory to copy to.
        metrics: New metrics to save as the best.
        best_metrics_path: Path for the best metrics JSON file.
    """
    staging_model = staging_dir / "model"
    
    # Ensure production directory exists
    production_dir.mkdir(parents=True, exist_ok=True)

    # Copy model weights
    src_weights = staging_model / "weights.pt"
    dst_weights = production_dir / "weights.pt"
    if src_weights.exists():
        shutil.copy2(src_weights, dst_weights)
        logger.info(f"Copied weights: {src_weights} -> {dst_weights}")
    else:
        logger.warning(f"Weights file not found: {src_weights}")

    # Copy metadata
    src_metadata = staging_model / "metadata.json"
    dst_metadata = production_dir / "metadata.json"
    if src_metadata.exists():
        shutil.copy2(src_metadata, dst_metadata)
        logger.info(f"Copied metadata: {src_metadata} -> {dst_metadata}")
    else:
        logger.warning(f"Metadata file not found: {src_metadata}")

    # Update best metrics
    save_metrics(metrics, best_metrics_path)
    logger.info(f"Model promoted to production: {production_dir}")


def run_pipeline(
    config_path: Path,
    min_accuracy: float,
    staging_dir: Path | None = None,
    production_dir: Path | None = None,
    metrics_dir: Path | None = None,
) -> bool:
    """
    Execute the full training and promotion pipeline.

    Args:
        config_path: Path to the training configuration YAML.
        min_accuracy: Minimum accuracy threshold for promotion (0.0-1.0).
        staging_dir: Override for staging directory (default: artifacts/staging).
        production_dir: Override for production model dir (default: from config).
        metrics_dir: Override for metrics directory (default: artifacts/metrics).

    Returns:
        True if the model was promoted, False otherwise.
    """
    # Set defaults
    if staging_dir is None:
        staging_dir = Path("artifacts/staging")
    if metrics_dir is None:
        metrics_dir = Path("artifacts/metrics")

    # Load config to get default production paths
    try:
        from ml.train_cnn import Config
        cfg = Config.from_yaml(config_path)
    except ImportError:
        logger.error("Cannot import ml.train_cnn to read config defaults")
        raise

    if production_dir is None:
        production_dir = cfg.output_dir

    # Derive metrics paths from experiment name
    experiment_name = cfg.experiment_name
    new_metrics_path = staging_dir / "metrics.json"
    best_metrics_path = metrics_dir / f"{experiment_name}_best.json"

    logger.info("=" * 60)
    logger.info("HARV Vision Pipeline Starting")
    logger.info("=" * 60)
    logger.info(f"Config: {config_path}")
    logger.info(f"Min accuracy threshold: {min_accuracy}")
    logger.info(f"Production directory: {production_dir}")
    logger.info(f"Best metrics path: {best_metrics_path}")

    # Clean staging directory
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Run training
    logger.info("-" * 60)
    logger.info("Step 1: Running training")
    logger.info("-" * 60)
    new_metrics = run_training(config_path, staging_dir)

    # Step 2: Load prior best metrics
    logger.info("-" * 60)
    logger.info("Step 2: Comparing with prior best")
    logger.info("-" * 60)
    prior_metrics = load_metrics(best_metrics_path)

    new_accuracy = new_metrics.get("accuracy", 0.0)
    prior_accuracy = prior_metrics.get("accuracy", 0.0) if prior_metrics else 0.0

    logger.info(f"New model accuracy: {new_accuracy:.4f}")
    logger.info(f"Prior best accuracy: {prior_accuracy:.4f}")
    logger.info(f"Minimum threshold: {min_accuracy:.4f}")

    # Step 3: Evaluate promotion criteria
    logger.info("-" * 60)
    logger.info("Step 3: Evaluating promotion criteria")
    logger.info("-" * 60)

    meets_threshold = new_accuracy >= min_accuracy
    beats_prior = new_accuracy >= prior_accuracy

    if not meets_threshold:
        logger.warning(
            f"REJECTED: New accuracy ({new_accuracy:.4f}) "
            f"below minimum threshold ({min_accuracy:.4f})"
        )
        return False

    if not beats_prior:
        logger.warning(
            f"REJECTED: New accuracy ({new_accuracy:.4f}) "
            f"does not beat prior best ({prior_accuracy:.4f})"
        )
        return False

    # Step 4: Promote model
    logger.info("-" * 60)
    logger.info("Step 4: Promoting model to production")
    logger.info("-" * 60)
    promote_model(staging_dir, production_dir, new_metrics, best_metrics_path)

    # Also copy metrics to the standard location for downstream consumers
    standard_metrics_path = metrics_dir / f"{experiment_name}.json"
    save_metrics(new_metrics, standard_metrics_path)

    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE: Model promoted successfully")
    logger.info("=" * 60)
    return True


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for the pipeline.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="HARV Vision Training Pipeline - Coordinates training and conditional model promotion.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run with default threshold
    python -m train.pipeline --config ml/configs/harv_vision_v1.yaml

    # Run with custom accuracy threshold
    python -m train.pipeline --config ml/configs/harv_vision_v1.yaml --min_accuracy 0.85

    # Run with custom directories
    python -m train.pipeline --config ml/configs/harv_vision_v1.yaml \\
        --staging-dir /tmp/staging \\
        --production-dir models/production
        """,
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("ml/configs/harv_vision_v1.yaml"),
        help="Path to YAML training config (default: ml/configs/harv_vision_v1.yaml)",
    )
    parser.add_argument(
        "--min_accuracy",
        "--min-accuracy",
        type=float,
        default=0.8,
        help="Minimum accuracy threshold for promotion (default: 0.8)",
    )
    parser.add_argument(
        "--staging-dir",
        type=Path,
        default=None,
        help="Staging directory for intermediate outputs (default: artifacts/staging)",
    )
    parser.add_argument(
        "--production-dir",
        type=Path,
        default=None,
        help="Production model directory (default: from config)",
    )
    parser.add_argument(
        "--metrics-dir",
        type=Path,
        default=None,
        help="Metrics output directory (default: artifacts/metrics)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for the training pipeline.

    Returns:
        Exit code: 0 if model promoted, 1 if not promoted, 2 on error.
    """
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    try:
        promoted = run_pipeline(
            config_path=args.config,
            min_accuracy=args.min_accuracy,
            staging_dir=args.staging_dir,
            production_dir=args.production_dir,
            metrics_dir=args.metrics_dir,
        )
        return 0 if promoted else 1
    except Exception as e:
        logger.exception(f"Pipeline failed with error: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
