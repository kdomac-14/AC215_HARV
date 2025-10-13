# Milestone 2: Testing Evidence Documentation

## Overview

This document describes the testing infrastructure, how to run tests, where outputs are saved, and how to interpret results for Milestone 2 verification.

## Test Infrastructure

### Test Hierarchy

```
tests/
├── unit/                   # Fast, isolated function-level tests
│   ├── test_geo.py        # Geolocation utility tests
│   ├── test_params.py     # Parameter validation tests
│   └── test_image_utils.py # Image processing tests
├── integration/           # Multi-service integration tests
│   ├── test_api.py        # API endpoint tests
│   └── test_artifacts.py  # Artifact validation tests
├── e2e/                   # Full system end-to-end tests
│   └── test_full_pipeline.py # Complete workflow tests
└── load/                  # Load and stress tests
    ├── load_test.js       # k6 load test script
    └── README.md          # Load testing documentation
```

### Test Coverage

- **Unit Tests**: 80%+ coverage target for isolated functions
- **Integration Tests**: API endpoints, service interactions
- **E2E Tests**: Complete workflows from calibration → verification
- **Load Tests**: 100+ concurrent users, performance validation

## Running Tests

### Prerequisites

1. **Install test dependencies:**
   ```bash
   pip install -r requirements-test.txt
   ```

2. **Install k6 (for load tests):**
   ```bash
   # macOS
   brew install k6
   
   # Linux
   sudo apt-get install k6
   ```

3. **Ensure services are running:**
   ```bash
   make run
   ```

### Quick Start

**Run all tests:**
```bash
make test
```

**Run specific test suites:**
```bash
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-e2e           # E2E tests only
make test-load          # Load tests only
```

**Complete verification workflow:**
```bash
make verify
```
This command:
1. Builds and starts all services
2. Waits for services to be ready
3. Runs all test suites
4. Generates coverage reports
5. Exports evidence

### Manual Test Execution

**Unit tests (no services required):**
```bash
pytest tests/unit/ -v -m unit
```

**Integration tests (requires running services):**
```bash
# Start services first
docker compose up -d

# Run tests
pytest tests/integration/ -v -m integration
```

**E2E tests with coverage:**
```bash
pytest tests/e2e/ -v -m e2e \
  --cov-report=html:evidence/coverage/html \
  --cov-report=xml:evidence/coverage/coverage.xml
```

**Load tests:**
```bash
k6 run tests/load/load_test.js --out json=evidence/load/results.json
```

## Evidence Generation

### Automatic Evidence Export

```bash
make evidence
```

This creates:
- Coverage reports (HTML + XML)
- E2E test results (JSON)
- Load test results (JSON)
- Service logs
- Timestamped archive for submission

### Evidence Directory Structure

```
evidence/
├── coverage/
│   ├── html/              # HTML coverage report
│   │   └── index.html     # Open in browser
│   └── coverage.xml       # XML for CI/Codecov
├── e2e/
│   └── e2e_results.json   # E2E test results
├── load/
│   └── results.json       # k6 load test results
├── logs/
│   ├── serve.log          # API service logs
│   └── dashboard.log      # Dashboard logs
└── screenshots/           # Manual screenshots
    ├── api_test.png
    ├── dashboard.png
    └── docker_ps.png
```

### Creating the Submission Archive

```bash
bash scripts/export_evidence.sh
```

Output: `milestone2_evidence_YYYYMMDD_HHMMSS.tar.gz`

## Interpreting Results

### Coverage Reports

**View HTML report:**
```bash
open evidence/coverage/html/index.html  # macOS
xdg-open evidence/coverage/html/index.html  # Linux
```

**Understanding coverage metrics:**
- **Stmts**: Total statements in file
- **Miss**: Statements not executed
- **Cover**: Percentage covered (target: 80%+)
- Green = good coverage
- Yellow/Red = needs more tests

### E2E Results

**View E2E results:**
```bash
cat evidence/e2e/e2e_results.json | python -m json.tool
```

**Expected structure:**
```json
{
  "health": {
    "ok": true,
    "model": "mobilenet_v3_small",
    "geo_provider": "MockProvider"
  },
  "calibration": {
    "ok": true,
    "calibration": {
      "lat": 42.377,
      "lon": -71.1167,
      "epsilon_m": 100.0
    }
  },
  "geo_verification": {
    "ok": true,
    "distance_m": 45.231,
    "source": "client_gps"
  },
  "image_verification": {
    "ok": true,
    "label": "ProfA",
    "confidence": 0.8234,
    "latency_ms": 125
  }
}
```

### Load Test Results

**Key metrics to check:**
- **http_req_duration**: p95 should be < 1000ms
- **http_req_failed**: Should be < 10%
- **checks**: Pass rate should be > 90%

**View load test summary:**
```bash
# k6 prints summary to console
# For detailed analysis, use k6 cloud or parse JSON output
```

### Test Success Criteria

✅ **Passing criteria:**
- All unit tests pass
- Integration tests pass with services running
- E2E workflow completes successfully
- Coverage ≥ 50% (test infrastructure)
- Load test p95 latency < 1s (if k6 installed)
- No critical failures in logs

❌ **Common failure reasons:**
- Services not running (run `make run` first)
- Port conflicts (check .env configuration)
- Missing dependencies (run `pip install -r requirements-test.txt`)
- Model not trained (run full pipeline first)

## CI/CD Integration

### GitHub Actions

Workflow runs automatically on push/PR to main/develop branches.

**Workflow stages:**
1. **Lint** - Code quality checks (ruff, mypy)
2. **Test** - Full test suite with coverage
3. **Load Test** - Performance testing (main branch only)

**View CI results:**
- Go to GitHub Actions tab
- Check workflow run status
- Download evidence artifacts from completed runs

**Artifacts uploaded:**
- `test-evidence-{SHA}` - Coverage, logs, E2E results
- `load-test-results-{SHA}` - Load test data

### Local CI Simulation

```bash
# Simulate CI workflow locally
docker compose down -v
docker compose up -d --build
bash scripts/wait_for_services.sh
pytest tests/ -v
bash scripts/export_evidence.sh
```

## Screenshot Instructions

### Required Screenshots

1. **Docker containers running:**
   ```bash
   docker compose ps
   # Screenshot the output
   ```

2. **API health check:**
   ```bash
   curl http://localhost:8000/healthz
   # Screenshot the output
   ```

3. **Test execution:**
   ```bash
   make test
   # Screenshot showing tests passing
   ```

4. **Coverage report:**
   ```bash
   open evidence/coverage/html/index.html
   # Screenshot the coverage dashboard
   ```

5. **Dashboard UI:**
   ```bash
   # Open http://localhost:8501 in browser
   # Screenshot the dashboard interface
   ```

### Taking Screenshots

**macOS:**
```bash
# Full screen
screencapture evidence/screenshots/test_output.png

# Window selection
screencapture -w evidence/screenshots/coverage.png
```

**Linux:**
```bash
scrot evidence/screenshots/test_output.png
```

**Manual:**
- Save to `evidence/screenshots/` directory
- Name descriptively: `api_health.png`, `test_passed.png`, etc.

## Troubleshooting

### Services Not Ready

**Problem:** Tests fail with connection errors

**Solution:**
```bash
# Check if services are running
docker compose ps

# View logs
docker compose logs serve

# Restart services
docker compose restart
```

### Coverage Too Low

**Problem:** Coverage < 80%

**Solution:**
```bash
# View detailed coverage report
pytest tests/ --cov-report=term-missing

# Add tests for uncovered lines
# Focus on unit tests for quick wins
```

### Load Tests Failing

**Problem:** k6 not found or tests timing out

**Solution:**
```bash
# Install k6
brew install k6  # macOS

# Check service performance
curl http://localhost:8000/healthz
# Should respond in < 100ms

# Reduce load if needed
k6 run tests/load/load_test.js --vus 10 --duration 30s
```

### Test Timeouts

**Problem:** Tests hang or timeout

**Solution:**
```bash
# Increase timeout in pytest.ini
# Or set environment variable
export PYTEST_TIMEOUT=30

# Check service health
docker compose ps
docker compose logs serve | tail -50
```

## Validation Checklist

Before submitting evidence:

- [ ] All services build successfully (`docker compose build`)
- [ ] Services start and run (`docker compose up -d`)
- [ ] Health check passes (`curl localhost:8000/healthz`)
- [ ] Unit tests pass (`make test-unit`)
- [ ] Integration tests pass (`make test-integration`)
- [ ] E2E tests pass (`make test-e2e`)
- [ ] Coverage ≥ 50% (`make coverage`)
- [ ] Load tests complete (`make test-load`)
- [ ] Evidence exported (`make evidence`)
- [ ] Screenshots captured (in `evidence/screenshots/`)
- [ ] Archive created (`milestone2_evidence_*.tar.gz`)

## Contact & Support

If you encounter issues:
1. Check logs: `docker compose logs`
2. Verify prerequisites are installed
3. Review error messages in test output
4. Check GitHub Actions for CI results

## Summary

This testing infrastructure provides:
- ✅ **Comprehensive coverage**: Unit, integration, E2E, load tests
- ✅ **Automated validation**: One command to verify everything
- ✅ **Clear evidence**: Reports, logs, metrics for grading
- ✅ **CI/CD ready**: GitHub Actions workflow included
- ✅ **Reproducible**: Documented steps, automated scripts

Run `make verify` for complete validation and evidence generation.
