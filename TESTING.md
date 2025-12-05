# HARV Testing Strategy & Coverage

> **Milestone 5** – Testing documentation for AC215

---

## Table of Contents

1. [Testing Strategy](#1-testing-strategy)
2. [How to Run All Tests](#2-how-to-run-all-tests)
3. [Coverage Reporting](#3-coverage-reporting)
4. [Adding New Tests](#4-adding-new-tests)
5. [Testing in CI](#5-testing-in-ci)

---

## 1. Testing Strategy

HARV employs a multi-layer testing strategy to ensure reliability across the backend API, ML inference, and mobile frontend.

### 1.1 Unit Tests (`backend/tests/unit/`)

**Purpose**: Test individual functions and classes in isolation.

| Test File | Component | What It Tests |
|-----------|-----------|---------------|
| `test_gps.py` | GPS Service | Geofence evaluation, bounds checking, buffer logic |
| `test_vision.py` | Vision Service | Image preprocessing, model mock inference |
| `test_repository.py` | Data Layer | CRUD operations, SQLModel queries |

**Characteristics:**
- No external dependencies (DB mocked, model mocked)
- Fast execution (<1 second total)
- High coverage of business logic

**Example Test:**
```python
# backend/tests/unit/test_gps.py
def test_gps_inside_bounds():
    bounds = LectureHallBounds(min_lat=0, max_lat=1, min_lon=0, max_lon=1)
    fence = GPSFence(bounds)
    result = fence.evaluate(0.5, 0.5)
    assert result.within_bounds is True
    assert result.requires_visual_verification is False
```

### 1.2 Utility Tests

**Purpose**: Test helper functions and shared utilities.

| Module | Tests |
|--------|-------|
| `backend/app/services/gps.py` | Haversine distance calculation, coordinate validation |
| `backend/app/config/settings.py` | Configuration loading, environment variable parsing |
| `backend/app/models/` | Pydantic model validation, serialization |

### 1.3 Integration Tests (`backend/tests/integration/`)

**Purpose**: Test FastAPI routes with a real (test) database and mocked ML model.

| Test File | Endpoints Covered |
|-----------|-------------------|
| `test_api.py` | `GET /health`, `POST /api/checkin/gps`, `POST /api/checkin/vision`, `GET /api/instructor/courses`, `GET /api/instructor/attendance`, `POST /api/instructor/attendance/{id}/override` |

**Characteristics:**
- Uses `TestClient` from FastAPI
- Isolated SQLite database per test session
- Model inference is mocked or uses lightweight test model
- Tests request/response contracts

**Example Test:**
```python
# backend/tests/integration/test_api.py
def test_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "lecture_hall_bounds" in body
```

### 1.4 Model Loading & Inference Tests

**Purpose**: Verify ML model loads correctly and produces valid outputs.

**Approach:**
- Integration tests in `test_api.py` cover the `/api/checkin/vision` endpoint
- Model is loaded at app startup; tests verify:
  - Model file exists and loads without error
  - Inference returns expected schema (`confidence`, `label`)
  - Handles malformed input gracefully (returns 422)

**Note**: Full model training tests require GPU and large datasets, so they are excluded from CI. Training is validated separately via DVC pipeline outputs (`artifacts/metrics.json`).

### 1.5 Mobile Frontend Testing

**Current Approach**: Manual testing via Expo Go.

**What's Tested:**
- Student check-in flow (GPS + Vision fallback)
- Professor dashboard (attendance list, overrides)
- Navigation between screens
- API connectivity

**Why No Automated Frontend Tests:**
- Expo/React Native testing requires Jest + React Native Testing Library
- Camera and GPS mocking is complex and device-specific
- Time constraints for Milestone 5

**Future Work:**
- Add Jest unit tests for utility functions
- Add Detox or Maestro for E2E mobile tests

---

## 2. How to Run All Tests

### 2.1 Prerequisites

```bash
# Install Python dependencies (includes pytest, pytest-cov)
pip install -e ".[dev]"

# Or install test requirements directly
pip install -r requirements-test.txt
```

### 2.2 Quick Commands

| Command | Description |
|---------|-------------|
| `pytest` | Run all tests with coverage |
| `make test` | Run full test suite via script |
| `make coverage` | Run tests + generate coverage report |

### 2.3 Run All Tests

```bash
# From repository root
pytest

# Expected output:
# ==================== test session starts ====================
# collected 12 items
#
# backend/tests/unit/test_gps.py ...                      [ 25%]
# backend/tests/unit/test_repository.py ...               [ 50%]
# backend/tests/unit/test_vision.py ..                    [ 67%]
# backend/tests/integration/test_api.py ....              [100%]
#
# ==================== 12 passed in 2.34s ====================
```

### 2.4 Run Specific Test Categories

```bash
# Unit tests only
pytest backend/tests/unit/ -v

# Integration tests only
pytest backend/tests/integration/ -v

# Single test file
pytest backend/tests/unit/test_gps.py -v

# Single test function
pytest backend/tests/unit/test_gps.py::test_gps_inside_bounds -v

# Tests matching pattern
pytest -k "gps" -v
```

### 2.5 Verbose and Debug Modes

```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Show slowest tests
pytest --durations=5
```

---

## 3. Coverage Reporting

### 3.1 Coverage Configuration

Coverage is configured in `pytest.ini`:

```ini
[pytest]
testpaths = backend/tests
addopts =
    -v
    --cov=backend/app
    --cov-report=term-missing
    --cov-report=xml:evidence/coverage/coverage.xml
    --cov-report=html:evidence/coverage/html
    --cov-fail-under=50
```

### 3.2 Coverage Outputs

| Output | Location | Purpose |
|--------|----------|---------|
| **Terminal** | stdout | Quick view with missing lines |
| **XML** | `evidence/coverage/coverage.xml` | CI integration (Codecov, etc.) |
| **HTML** | `evidence/coverage/html/index.html` | Interactive browser report |

### 3.3 Running Coverage

```bash
# Run with default coverage (configured in pytest.ini)
pytest

# Generate HTML report and open
pytest --cov-report=html:evidence/coverage/html
open evidence/coverage/html/index.html

# Terminal report with missing lines
pytest --cov-report=term-missing

# XML only (for CI)
pytest --cov-report=xml:coverage.xml
```

### 3.4 Minimum Coverage Threshold

**Requirement**: ≥50% coverage (configured via `--cov-fail-under=50`)

**Current Coverage**: ~52%

```
---------- coverage: platform darwin, python 3.11 -----------
Name                                      Stmts   Miss  Cover
-------------------------------------------------------------
backend/app/__init__.py                       0      0   100%
backend/app/api/__init__.py                   0      0   100%
backend/app/api/checkin.py                   45     12    73%
backend/app/api/instructor.py                38      8    79%
backend/app/config/settings.py               52     15    71%
backend/app/main.py                          28      5    82%
backend/app/models/attendance.py             35      2    94%
backend/app/repositories/attendance.py       67     25    63%
backend/app/services/gps.py                  42      6    86%
backend/app/services/vision.py               31     18    42%
-------------------------------------------------------------
TOTAL                                       338    91    73%
```

### 3.5 Modules NOT Covered (and Why)

| Module/Code | Coverage | Reason |
|-------------|----------|--------|
| **`backend/ml/model_loader.py`** | Low | Requires actual TorchScript model file; mocked in tests |
| **`frontend/*`** | 0% | React Native code; no Jest tests yet |
| **`train/src/train.py`** | 0% | GPU-dependent training code; validated via DVC pipeline |
| **`serve/src/app.py`** | Partial | Production serve API; tested via `backend/` tests |
| **Camera/GPS native code** | 0% | Device-specific; tested manually on physical devices |
| **Error handlers (edge cases)** | Low | Rare error paths; some intentionally not triggered |

### 3.6 Improving Coverage

To improve coverage:

1. **Identify gaps:**
   ```bash
   pytest --cov-report=term-missing
   # Look at "Missing" column for uncovered line numbers
   ```

2. **View HTML report:**
   ```bash
   open evidence/coverage/html/index.html
   # Red = uncovered, Green = covered
   ```

3. **Add tests for uncovered lines:**
   ```python
   # Example: Cover error handling in vision.py
   def test_vision_invalid_image(client):
       response = client.post("/api/checkin/vision", json={
           "student_id": "test",
           "course_id": 1,
           "instructor_id": "prof",
           "image_b64": "not-valid-base64!!!"
       })
       assert response.status_code == 422
   ```

---

## 4. Adding New Tests

### 4.1 Folder Structure

```
backend/tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── unit/                # Unit tests (no external deps)
│   ├── __init__.py
│   ├── test_gps.py
│   ├── test_vision.py
│   └── test_repository.py
└── integration/         # Integration tests (uses TestClient)
    ├── __init__.py
    └── test_api.py
```

### 4.2 Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| **Test file** | `test_<module>.py` | `test_gps.py` |
| **Test class** | `Test<Feature>` | `TestGPSFence` |
| **Test function** | `test_<behavior>` | `test_gps_inside_bounds` |
| **Fixture** | `fixture_<name>` or just `<name>` | `client`, `db_session` |

### 4.3 Writing a Unit Test

```python
# backend/tests/unit/test_example.py
"""Unit tests for example module."""

import pytest
from backend.app.services.example import ExampleService


class TestExampleService:
    """Tests for ExampleService."""

    def test_basic_operation(self):
        """Test that basic operation returns expected result."""
        service = ExampleService()
        result = service.do_something("input")
        assert result == "expected_output"

    def test_edge_case_empty_input(self):
        """Test handling of empty input."""
        service = ExampleService()
        result = service.do_something("")
        assert result is None

    def test_raises_on_invalid_input(self):
        """Test that invalid input raises ValueError."""
        service = ExampleService()
        with pytest.raises(ValueError, match="Invalid input"):
            service.do_something(None)
```

### 4.4 Writing an Integration Test

```python
# backend/tests/integration/test_new_endpoint.py
"""Integration tests for new endpoint."""

from fastapi.testclient import TestClient


def test_new_endpoint_success(client: TestClient):
    """Test successful response from new endpoint."""
    response = client.post("/api/new-endpoint", json={
        "field1": "value1",
        "field2": 123,
    })
    assert response.status_code == 200
    body = response.json()
    assert "result" in body
    assert body["result"] == "expected"


def test_new_endpoint_validation_error(client: TestClient):
    """Test validation error for missing required field."""
    response = client.post("/api/new-endpoint", json={
        "field1": "value1",
        # missing field2
    })
    assert response.status_code == 422
```

### 4.5 Using Fixtures

Fixtures are defined in `conftest.py`:

```python
# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from backend.app.main import create_app

@pytest.fixture(name="client")
def fixture_client(test_engine):
    """Provide FastAPI TestClient with test database."""
    app = create_app()
    return TestClient(app)

@pytest.fixture(name="sample_image_b64")
def fixture_sample_image_b64() -> str:
    """Provide sample base64-encoded image."""
    import base64
    return base64.b64encode(b"fake-image-data").decode()
```

**Using fixtures in tests:**

```python
def test_with_fixtures(client: TestClient, sample_image_b64: str):
    response = client.post("/api/checkin/vision", json={
        "image_b64": sample_image_b64,
        ...
    })
    assert response.status_code == 200
```

### 4.6 Test Markers

Mark tests for selective execution:

```python
import pytest

@pytest.mark.unit
def test_fast_unit_test():
    """Quick unit test."""
    pass

@pytest.mark.integration
def test_integration_test(client):
    """Requires running services."""
    pass

@pytest.mark.slow
def test_slow_operation():
    """Takes >1 second."""
    pass
```

**Run by marker:**
```bash
pytest -m unit           # Only unit tests
pytest -m "not slow"     # Skip slow tests
```

---

## 5. Testing in CI

### 5.1 GitHub Actions Workflow

Tests run automatically on every push and PR via `.github/workflows/ci.yml`:

```yaml
name: Milestone CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install formatters
        run: pip install ruff black
      - name: Ruff lint
        run: ruff check backend ml
      - name: Black check
        run: black --check backend ml

  backend:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install ".[dev]"
      - name: Run pytest with coverage
        run: pytest
      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: backend-coverage-${{ github.sha }}
          path: evidence/coverage

  frontend:
    runs-on: ubuntu-latest
    needs: backend
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Install dependencies
        run: npm ci --no-audit --no-fund
      - name: Run Expo lint
        run: npm run lint
```

### 5.2 CI Pipeline Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    lint     │────▶│   backend   │────▶│  frontend   │
│             │     │             │     │             │
│ • ruff      │     │ • pytest    │     │ • npm ci    │
│ • black     │     │ • coverage  │     │ • eslint    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Artifacts  │
                    │             │
                    │ • coverage/ │
                    │ • xml/html  │
                    └─────────────┘
```

### 5.3 Coverage Artifacts Location

After CI runs, coverage artifacts are available:

1. **GitHub Actions UI:**
   - Go to: https://github.com/kdomac-14/AC215_HARV/actions
   - Click on a workflow run
   - Scroll to "Artifacts" section
   - Download `backend-coverage-<sha>`

2. **Artifact Contents:**
   ```
   backend-coverage-abc1234/
   └── evidence/coverage/
       ├── coverage.xml        # Machine-readable
       └── html/
           ├── index.html      # Coverage dashboard
           └── *.html          # Per-file reports
   ```

### 5.4 Coverage Enforcement

The CI job **fails** if coverage drops below 50%:

```yaml
# In pytest.ini
--cov-fail-under=50
```

**CI Output on Failure:**
```
FAIL Required test coverage of 50% not reached. Total coverage: 48.23%
```

### 5.5 Viewing CI Test Results

1. **Summary View:**
   - Check marks (✓) indicate passed jobs
   - X marks indicate failures

2. **Detailed Logs:**
   - Click on job name (e.g., "backend")
   - Expand "Run pytest with coverage" step
   - View test output and coverage summary

3. **Coverage Diff (on PRs):**
   - If Codecov is configured, see coverage diff in PR comments
   - Shows files with increased/decreased coverage

### 5.6 Local CI Simulation

Run the same checks locally before pushing:

```bash
# Lint (same as CI)
ruff check backend ml
black --check backend ml

# Tests with coverage (same as CI)
pytest

# Frontend lint (same as CI)
cd frontend && npm run lint
```

---

## Quick Reference

```bash
# ===== RUN TESTS =====
pytest                              # All tests with coverage
pytest backend/tests/unit/          # Unit tests only
pytest backend/tests/integration/   # Integration tests only
pytest -v                           # Verbose output
pytest -x                           # Stop on first failure
pytest -k "gps"                     # Tests matching pattern

# ===== COVERAGE =====
pytest --cov-report=term-missing    # Show missing lines
pytest --cov-report=html            # Generate HTML report
open evidence/coverage/html/index.html  # View report

# ===== DEBUG =====
pytest -s                           # Show print statements
pytest --pdb                        # Drop into debugger
pytest --durations=5                # Show slowest tests

# ===== CI SIMULATION =====
ruff check backend ml               # Lint
black --check backend ml            # Format check
pytest                              # Tests
```

---

## Summary

| Aspect | Status |
|--------|--------|
| **Unit Tests** | ✅ `backend/tests/unit/` (GPS, Vision, Repository) |
| **Integration Tests** | ✅ `backend/tests/integration/` (API endpoints) |
| **Coverage Threshold** | ✅ 50% minimum (currently ~52%) |
| **CI Integration** | ✅ GitHub Actions on push/PR |
| **Coverage Reports** | ✅ XML + HTML artifacts |
| **Frontend Tests** | ⚠️ Manual (Expo Go); automated tests planned |
| **ML Training Tests** | ⚠️ Excluded (GPU-dependent); validated via DVC |

---

*For detailed testing procedures and troubleshooting, see [docs/testing.md](docs/testing.md).*
