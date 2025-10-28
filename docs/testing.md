# Testing Documentation

## Quick Reference

| Command | Description |
|---------|-------------|
| `make test` | Run all tests (unit + integration + e2e) |
| `make test-unit` | Run unit tests only |
| `make test-integration` | Run integration tests |
| `make test-e2e` | Run end-to-end tests |
| `make test-load` | Run load tests with k6 |
| `make verify` | Complete verification (build + test + evidence) |
| `make coverage` | Generate and view coverage report |
| `make evidence` | Export evidence for submission |

## Test Organization

### Unit Tests (`tests/unit/`)

Fast, isolated tests for individual functions and utilities.

**Characteristics:**
- No external dependencies
- No service calls
- Fast execution (< 1s total)
- High coverage target (80%+)

**Examples:**
- `test_geo.py` - Haversine distance, calibration save/load
- `test_params.py` - Parameter validation
- `test_image_utils.py` - Image processing utilities

**Run:**
```bash
pytest tests/unit/ -v -m unit
```

### Integration Tests (`tests/integration/`)

Multi-component tests requiring running services.

**Characteristics:**
- Requires Docker services running
- Tests API endpoints
- Tests service interactions
- Validates artifacts

**Examples:**
- `test_api.py` - API endpoints (health, geo, verify)
- `test_artifacts.py` - Model, metrics, sample outputs

**Run:**
```bash
# Start services first
docker compose up -d

# Run integration tests
pytest tests/integration/ -v -m integration
```

### E2E Tests (`tests/e2e/`)

Full system tests covering complete workflows.

**Characteristics:**
- Tests complete user workflows
- Validates end-to-end functionality
- Generates evidence files
- Includes performance checks

**Examples:**
- Complete verification: calibrate → geo verify → image verify
- Error handling workflows
- Performance/latency validation

**Run:**
```bash
pytest tests/e2e/ -v -m e2e
```

### Load Tests (`tests/load/`)

Performance and stress tests using k6.

**Characteristics:**
- Tests system under concurrent load
- Validates performance thresholds
- Generates performance metrics
- Identifies bottlenecks

**Load profile:**
- Ramp up: 0 → 20 users (30s)
- Steady: 50 users (1min)
- Spike: 100 users (30s)
- Recovery: 50 users (1min)
- Ramp down: 50 → 0 (30s)

**Run:**
```bash
k6 run tests/load/load_test.js
```

## Test Configuration

### pytest.ini

Main pytest configuration:
- Test discovery patterns
- Coverage settings
- Markers for test categories
- Output formats

### conftest.py

Shared fixtures:
- `project_root` - Project root directory
- `artifacts_dir` - Artifacts location
- `evidence_dir` - Evidence output location
- `sample_image` - Test image fixture
- `sample_image_b64` - Base64 encoded image
- `wait_for_services` - Service readiness check

## Writing Tests

### Unit Test Example

```python
import pytest

@pytest.mark.unit
class TestMyFunction:
    def test_basic_functionality(self):
        result = my_function(input_data)
        assert result == expected_output
    
    def test_edge_cases(self):
        result = my_function(edge_case)
        assert result is not None
```

### Integration Test Example

```python
import pytest
import requests

@pytest.mark.integration
class TestAPI:
    def test_endpoint(self, api_base_url, wait_for_services):
        response = requests.get(f"{api_base_url}/healthz")
        assert response.status_code == 200
        assert response.json()["ok"] is True
```

### E2E Test Example

```python
import pytest
import requests

@pytest.mark.e2e
class TestWorkflow:
    def test_complete_flow(self, api_base_url, evidence_dir, wait_for_services):
        # Step 1: Health check
        health = requests.get(f"{api_base_url}/healthz")
        assert health.status_code == 200
        
        # Step 2: Calibrate
        calibrate = requests.post(
            f"{api_base_url}/geo/calibrate",
            json={"lat": 42.377, "lon": -71.1167, "epsilon_m": 100}
        )
        assert calibrate.status_code == 200
        
        # Step 3: Verify
        # ... rest of workflow
        
        # Save evidence
        with open(evidence_dir / "e2e" / "results.json", "w") as f:
            json.dump(results, f)
```

## Test Coverage

### Overview

HARV maintains comprehensive test coverage to ensure code quality and reliability. Current coverage: **52%** (exceeds Milestone 2 requirement of ≥50%).

### Running Coverage

**Quick coverage check (terminal output):**
```bash
make coverage
```

**Generate HTML report and open in browser:**
```bash
make coverage-html
```

**Manual pytest commands:**
```bash
# Terminal report with missing lines
pytest

# HTML report only
pytest --cov-report=html

# XML report for CI
pytest --cov-report=xml
```

### Interpreting Coverage Output

**Terminal Output Example:**
```
---------- coverage: platform darwin, python 3.11.5 -----------
Name                       Stmts   Miss  Cover   Missing
--------------------------------------------------------
serve/src/geo.py              45      8    82%   67-74
serve/src/app.py              89     12    87%   120-131
tests/unit/test_geo.py        32      0   100%
--------------------------------------------------------
TOTAL                        485     72    85%
```

**Key Metrics:**
- **Stmts**: Total statements in file
- **Miss**: Statements not executed by tests
- **Cover**: Percentage coverage (Stmts - Miss) / Stmts
- **Missing**: Line numbers not covered

### Coverage Configuration

Configured in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
addopts = [
    "-q",                               # Quiet mode
    "--disable-warnings",               # Suppress warnings
    "--cov=src",                        # Coverage source
    "--cov-report=term-missing",        # Show missing lines
    "--cov-report=html",                # HTML report
    "--cov-report=xml",                 # XML for CI
]

[tool.coverage.run]
branch = true                           # Track branch coverage
source = ["src", "ingestion/src", ...]  # Source directories
omit = ["*/tests/*", ...]               # Exclude patterns

[tool.coverage.report]
precision = 2                           # Decimal places
show_missing = true                     # Show uncovered lines
skip_covered = false                    # Show all files
```

### Coverage Targets

| Component | Current | Target | Notes |
|-----------|---------|--------|-------|
| **Overall** | 52% | 50%+ | ✅ Meets MS2 requirement |
| Unit tests | 65% | 80%+ | Core logic coverage |
| Integration | 45% | 60%+ | API endpoints |
| E2E | 30% | 40%+ | Workflow coverage |

### Improving Coverage

1. **Identify uncovered lines:**
   ```bash
   make coverage
   # Look for "Missing" column
   ```

2. **View detailed HTML report:**
   ```bash
   make coverage-html
   # Click on files to see highlighted uncovered lines
   ```

3. **Focus areas for improvement:**
   - ✅ **Unit tests**: Test edge cases and error handling
   - ✅ **Integration tests**: Cover all API endpoints
   - ✅ **E2E tests**: Add workflow variations
   - ⚠️ **Avoid**: Testing external libraries or boilerplate

4. **Example: Adding coverage for uncovered function:**
   ```python
   # In serve/src/geo.py (uncovered lines 67-74)
   def validate_coordinates(lat: float, lon: float) -> bool:
       """Validate latitude and longitude ranges."""
       if not -90 <= lat <= 90:
           return False
       if not -180 <= lon <= 180:
           return False
       return True
   
   # Add test in tests/unit/test_geo.py
   @pytest.mark.unit
   class TestCoordinateValidation:
       def test_valid_coordinates(self):
           assert validate_coordinates(42.377, -71.1167) is True
       
       def test_invalid_latitude(self):
           assert validate_coordinates(91, -71.1167) is False
       
       def test_invalid_longitude(self):
           assert validate_coordinates(42.377, 181) is False
   ```

### Coverage Reports Location

All reports generated in `evidence/coverage/`:
```
evidence/coverage/
├── html/
│   ├── index.html          # Main coverage dashboard
│   ├── serve_src_geo_py.html
│   └── ...                 # Per-file coverage
├── coverage.xml            # CI/CD integration
└── .coverage               # Raw coverage data
```

**Note:** `evidence/` directory is gitignored. Only sample evidence in `docs/evidence/` is committed.

## Continuous Integration

### GitHub Actions Workflow

Located at `.github/workflows/ci.yml`

**Jobs:**
1. **Lint** - Code quality (ruff, mypy)
2. **Test** - Full test suite + coverage
3. **Load Test** - Performance testing (main branch only)

**Triggers:**
- Push to main/develop
- Pull requests to main/develop

**Artifacts:**
- Test evidence (coverage, logs, results)
- Load test results
- Evidence archive

### Viewing CI Results

1. Go to GitHub repository
2. Click "Actions" tab
3. Select workflow run
4. View logs and download artifacts

### Local CI Simulation

```bash
# Full workflow
make verify

# Or step by step
docker compose down -v
docker compose up -d --build
bash scripts/wait_for_services.sh
pytest tests/ -v
bash scripts/export_evidence.sh
```

## Evidence Collection

### Automatic Collection

```bash
make evidence
```

Collects:
- Coverage reports (HTML + XML)
- E2E results (JSON)
- Load test results (JSON)
- Service logs
- Artifacts (model, metrics)
- Creates timestamped archive

### Manual Collection

```bash
# Coverage
pytest tests/ --cov-report=html:evidence/coverage/html

# E2E results (generated by tests)
cat evidence/e2e/e2e_results.json

# Service logs
docker compose logs serve > evidence/logs/serve.log
docker compose logs dashboard > evidence/logs/dashboard.log

# Screenshots
screencapture evidence/screenshots/coverage.png
```

### Evidence Structure

```
evidence/
├── coverage/
│   ├── html/index.html       # Interactive coverage report
│   └── coverage.xml          # XML for CI tools
├── e2e/
│   └── e2e_results.json      # E2E test results
├── load/
│   └── results.json          # k6 load test data
├── logs/
│   ├── serve.log             # API service logs
│   └── dashboard.log         # Dashboard logs
└── screenshots/              # Manual screenshots
    ├── docker_ps.png
    ├── api_health.png
    ├── test_passed.png
    └── coverage_report.png
```

## Best Practices

### Test Organization

- ✅ Group related tests in classes
- ✅ Use descriptive test names
- ✅ One assertion per test (when possible)
- ✅ Use fixtures for common setup
- ✅ Mark tests appropriately (unit/integration/e2e)

### Test Independence

- ✅ Tests should not depend on each other
- ✅ Clean up after tests (use fixtures)
- ✅ Use isolated test data
- ✅ Don't share mutable state

### Performance

- ✅ Unit tests should be fast (< 1s total)
- ✅ Use mocks for external dependencies
- ✅ Run slow tests separately (-m slow)
- ✅ Parallelize when possible (pytest-xdist)

### Documentation

- ✅ Add docstrings to test classes/functions
- ✅ Comment complex test logic
- ✅ Document test data and fixtures
- ✅ Keep README files updated

## Troubleshooting

### Tests Not Found

**Problem:** pytest doesn't discover tests

**Solution:**
- Ensure test files start with `test_`
- Check test functions start with `test_`
- Verify `pytest.ini` configuration
- Run with `-v` for verbose output

### Import Errors

**Problem:** Cannot import modules

**Solution:**
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install package in editable mode
pip install -e .
```

### Service Connection Errors

**Problem:** Integration tests fail with connection errors

**Solution:**
```bash
# Check services are running
docker compose ps

# Check health endpoint
curl http://localhost:8000/healthz

# Wait for services
bash scripts/wait_for_services.sh

# Check logs
docker compose logs serve
```

### Coverage Issues

**Problem:** Coverage too low or incorrect

**Solution:**
```bash
# Generate detailed report
pytest tests/ --cov-report=term-missing

# Exclude test files from coverage
# (configured in pytest.ini)

# Add unit tests for uncovered code
```

### Slow Tests

**Problem:** Test suite takes too long

**Solution:**
```bash
# Run only fast tests
pytest tests/unit/ -v

# Skip slow tests
pytest tests/ -v -m "not slow"

# Parallelize tests
pytest tests/ -n auto

# Profile slow tests
pytest tests/ --durations=10
```

## Advanced Usage

### Running Specific Tests

```bash
# Single test file
pytest tests/unit/test_geo.py -v

# Single test class
pytest tests/unit/test_geo.py::TestHaversine -v

# Single test function
pytest tests/unit/test_geo.py::TestHaversine::test_zero_distance -v

# By marker
pytest tests/ -m unit -v
pytest tests/ -m "unit and not slow" -v
```

### Debugging Tests

```bash
# Drop into debugger on failure
pytest tests/ --pdb

# Show print statements
pytest tests/ -s

# Verbose output
pytest tests/ -vv

# Show local variables on failure
pytest tests/ -l
```

### Parallel Execution

```bash
# Auto-detect CPU count
pytest tests/ -n auto

# Specific number of workers
pytest tests/ -n 4
```

### Test Selection

```bash
# Last failed tests
pytest tests/ --lf

# Failed first, then rest
pytest tests/ --ff

# Only tests matching pattern
pytest tests/ -k "geo"
```

## Integration with IDEs

### VSCode

Add to `.vscode/settings.json`:
```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests",
    "-v"
  ]
}
```

### PyCharm

1. Settings → Tools → Python Integrated Tools
2. Set Default test runner: pytest
3. Right-click test file → Run pytest

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [k6 Documentation](https://k6.io/docs/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/actions)

## Summary

The testing infrastructure provides:
- **Comprehensive validation** across all layers
- **Automated execution** via make commands
- **CI/CD integration** with GitHub Actions
- **Evidence generation** for milestone submission
- **Performance validation** with load testing

For complete validation, run:
```bash
make verify
```
