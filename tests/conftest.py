"""Root-level fixtures for all tests."""
import os
import json
import time
from pathlib import Path
from typing import Generator, Dict, Any

import pytest
import numpy as np
import cv2


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def artifacts_dir(project_root: Path) -> Path:
    """Return artifacts directory."""
    return project_root / "artifacts"


@pytest.fixture(scope="session")
def evidence_dir(project_root: Path) -> Path:
    """Create and return evidence directory."""
    evidence = project_root / "evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "coverage").mkdir(exist_ok=True)
    (evidence / "e2e").mkdir(exist_ok=True)
    (evidence / "load").mkdir(exist_ok=True)
    (evidence / "logs").mkdir(exist_ok=True)
    return evidence


@pytest.fixture(scope="session")
def test_params() -> Dict[str, Any]:
    """Load test parameters from params.yaml."""
    import yaml
    params_path = Path(__file__).parent.parent / "params.yaml"
    if params_path.exists():
        with open(params_path) as f:
            return yaml.safe_load(f)
    return {}


@pytest.fixture
def sample_image() -> np.ndarray:
    """Generate a simple test image (white square)."""
    return np.ones((224, 224, 3), dtype=np.uint8) * 255


@pytest.fixture
def sample_image_b64(sample_image: np.ndarray) -> str:
    """Generate base64-encoded test image."""
    import base64
    _, buf = cv2.imencode(".jpg", sample_image)
    return base64.b64encode(buf).decode()


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Return API base URL from environment or default."""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def dashboard_url() -> str:
    """Return dashboard URL from environment or default."""
    return os.getenv("DASHBOARD_URL", "http://localhost:8501")


@pytest.fixture(scope="session")
def wait_for_services(api_base_url: str) -> Generator[None, None, None]:
    """Wait for services to be ready before running tests."""
    import requests
    
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{api_base_url}/healthz", timeout=2)
            if response.status_code == 200:
                print(f"\n✓ Services ready after {attempt} attempts")
                break
        except requests.exceptions.RequestException:
            pass
        
        attempt += 1
        time.sleep(2)
    else:
        pytest.fail(f"Services not ready after {max_attempts * 2}s")
    
    yield
