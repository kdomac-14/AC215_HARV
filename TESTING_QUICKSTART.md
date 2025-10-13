# Testing Quick Start Guide

## TL;DR - Complete Verification

```bash
make verify
```

This single command:
1. ✅ Builds all Docker containers
2. ✅ Starts services
3. ✅ Waits for readiness
4. ✅ Runs all tests (unit + integration + e2e)
5. ✅ Generates coverage reports
6. ✅ Exports evidence
7. ✅ Creates submission archive

## Prerequisites

```bash
# Install test dependencies
pip install -r requirements-test.txt

# (Optional) Install k6 for load tests
brew install k6  # macOS
```

## Common Commands

| Task | Command |
|------|---------|
| Full verification | `make verify` |
| Run all tests | `make test` |
| Unit tests only | `make test-unit` |
| Integration tests | `make test-integration` |
| E2E tests | `make test-e2e` |
| Load tests | `make test-load` |
| View coverage | `make coverage` |
| Export evidence | `make evidence` |
| Show help | `make help` |

## Manual Step-by-Step

### 1. Start Services
```bash
make run
# Wait for all services to complete
```

### 2. Run Tests
```bash
# In another terminal
make test
```

### 3. View Results
```bash
# Coverage report
open evidence/coverage/html/index.html

# E2E results
cat evidence/e2e/e2e_results.json | python -m json.tool

# Service logs
tail -f evidence/logs/serve.log
```

### 4. Export Evidence
```bash
make evidence
# Creates: milestone2_evidence_[timestamp].tar.gz
```

## Test Structure

```
tests/
├── unit/           # Fast, isolated (no services needed)
├── integration/    # API endpoints (services required)
├── e2e/           # Full workflows (services required)
└── load/          # Performance tests (k6)
```

## Success Criteria

- [x] All unit tests pass
- [x] All integration tests pass  
- [x] All E2E tests pass
- [x] Coverage ≥ 80%
- [x] Load test p95 < 1s
- [x] No errors in logs
- [x] Evidence archive created

## Troubleshooting

### Services Not Ready
```bash
# Check status
docker compose ps

# View logs
docker compose logs serve

# Restart
docker compose restart
```

### Tests Failing
```bash
# Check if services are running
curl http://localhost:8000/healthz

# Wait for services
bash scripts/wait_for_services.sh

# Run tests verbosely
pytest tests/ -vv
```

### Coverage Too Low
```bash
# See missing lines
pytest tests/ --cov-report=term-missing

# Add unit tests for quick wins
```

## Evidence Files

After running tests, find evidence at:
- `evidence/coverage/html/index.html` - Coverage report
- `evidence/e2e/e2e_results.json` - E2E results
- `evidence/load/results.json` - Load test data
- `evidence/logs/` - Service logs
- `evidence/screenshots/` - Screenshots (manual)
- `milestone2_evidence_*.tar.gz` - Submission archive

## CI/CD

Tests run automatically on GitHub Actions:
- **Trigger**: Push to main/develop or pull request
- **Jobs**: Lint → Test → Load Test
- **Artifacts**: Evidence files uploaded (30 days)

View at: GitHub → Actions tab

## Documentation

- **EVIDENCE.md** - Complete testing documentation
- **docs/testing.md** - Detailed testing guide
- **README.md** - Project overview with testing section

## Support

If stuck:
1. Check `docker compose logs`
2. Verify prerequisites installed
3. Review error messages
4. Check GitHub Actions for CI results

## Quick Validation

```bash
# 1. Health check
curl http://localhost:8000/healthz

# 2. Run unit tests (fast)
make test-unit

# 3. Run integration tests
make test-integration

# 4. Generate evidence
make evidence
```

Done! 🎉
