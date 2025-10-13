"""Unit tests for parameter validation."""
import pytest
import yaml
from pathlib import Path


@pytest.mark.unit
class TestParams:
    """Test parameter file structure."""
    
    def test_params_exists(self, project_root):
        """Verify params.yaml exists."""
        params_path = project_root / "params.yaml"
        assert params_path.exists(), "params.yaml not found"
    
    def test_params_valid_yaml(self, project_root):
        """Verify params.yaml is valid YAML."""
        params_path = project_root / "params.yaml"
        with open(params_path) as f:
            params = yaml.safe_load(f)
        assert isinstance(params, dict)
    
    def test_required_params(self, test_params):
        """Verify all required parameters are present."""
        required = ["seed", "img_size", "epochs", "batch_size", "lr", "model_name", "classes"]
        for key in required:
            assert key in test_params, f"Missing required parameter: {key}"
    
    def test_param_types(self, test_params):
        """Verify parameter types are correct."""
        assert isinstance(test_params["seed"], int)
        assert isinstance(test_params["img_size"], int)
        assert isinstance(test_params["epochs"], int)
        assert isinstance(test_params["batch_size"], int)
        assert isinstance(test_params["lr"], float)
        assert isinstance(test_params["model_name"], str)
        assert isinstance(test_params["classes"], list)
    
    def test_param_ranges(self, test_params):
        """Verify parameters are in valid ranges."""
        assert test_params["img_size"] > 0
        assert test_params["epochs"] > 0
        assert test_params["batch_size"] > 0
        assert 0 < test_params["lr"] < 1
        assert len(test_params["classes"]) >= 2
