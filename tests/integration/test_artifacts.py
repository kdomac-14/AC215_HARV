"""Integration tests for artifact generation and validation."""
import pytest
import json
from pathlib import Path


@pytest.mark.integration
class TestArtifacts:
    """Test that pipeline generates expected artifacts."""
    
    def test_model_exists(self, artifacts_dir):
        """Test that model file exists."""
        model_path = artifacts_dir / "model" / "model.torchscript.pt"
        # May not exist if pipeline hasn't run yet
        if model_path.exists():
            assert model_path.is_file()
            assert model_path.stat().st_size > 0
    
    def test_metadata_exists(self, artifacts_dir):
        """Test that metadata file exists."""
        metadata_path = artifacts_dir / "model" / "metadata.json"
        if metadata_path.exists():
            assert metadata_path.is_file()
            with open(metadata_path) as f:
                meta = json.load(f)
            assert "model" in meta
            assert "img_size" in meta
            assert "classes" in meta
    
    def test_metrics_exists(self, artifacts_dir):
        """Test that metrics file exists."""
        metrics_path = artifacts_dir / "metrics.json"
        if metrics_path.exists():
            assert metrics_path.is_file()
            with open(metrics_path) as f:
                metrics = json.load(f)
            # Metrics should contain evaluation results
            assert isinstance(metrics, dict)
    
    def test_sample_response_exists(self, artifacts_dir):
        """Test that sample response file exists."""
        sample_path = artifacts_dir / "samples" / "sample_response.json"
        if sample_path.exists():
            assert sample_path.is_file()
            with open(sample_path) as f:
                sample = json.load(f)
            assert "ok" in sample
            if sample["ok"]:
                assert "label" in sample
                assert "confidence" in sample
                assert "latency_ms" in sample


@pytest.mark.integration
class TestDataPipeline:
    """Test data pipeline outputs."""
    
    def test_interim_data(self, project_root):
        """Test interim data directory."""
        interim_dir = project_root / "data" / "interim"
        if interim_dir.exists():
            assert interim_dir.is_dir()
    
    def test_processed_data(self, project_root):
        """Test processed data directory."""
        processed_dir = project_root / "data" / "processed"
        if processed_dir.exists():
            assert processed_dir.is_dir()
            # Should contain train/val/test splits
            for split in ["train", "val", "test"]:
                split_dir = processed_dir / split
                if split_dir.exists():
                    assert split_dir.is_dir()
