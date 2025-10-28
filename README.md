# HARV - Harvard Attendance Recognition and Verification

## Milestone 2: Transfer Learning Vision Track with Full Containerization

End-to-end ML pipeline for face/object recognition with basic liveness detection. Uses transfer learning (MobileNetV3/EfficientNet-Lite0) and containerized components.

## Project Overview

**Components:**
- **Ingestion**: Creates manifest for data pipeline
- **Preprocess**: Generates synthetic training data (circles vs rectangles for two classes)
- **Train**: Transfer learning with MobileNetV3 on CPU
- **Evaluate**: Model evaluation with classification report
- **Export**: TorchScript model export
- **Serve**: FastAPI inference API with "word of the day" liveness challenge
- **Dashboard**: Streamlit UI for testing

**Tech Stack:**
- Python 3.11, uv dependency management
- PyTorch 2.3, Torchvision, OpenCV
- FastAPI, Streamlit
- Docker & Docker Compose
- Optional: W&B for experiment tracking

## Prerequisites

- **Docker** (24.0+)
- **Docker Compose** (2.0+)

Check versions:
```bash
docker --version
docker compose version
```

## Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd AC215-HARV
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env if needed (optional W&B, ports, challenge word)
```

### 3. Run Full Pipeline
```bash
make run
```

This single command:
- Builds all Docker images
- Runs ingestion → preprocess → train → evaluate → export sequentially
- Starts the API server on port 8000
- Starts the dashboard on port 8501

**Expected output:** All services complete successfully, API and dashboard remain running.

### 4. Test the API

#### Health Check
```bash
curl http://localhost:8000/healthz
```

Expected response:
```json
{"ok": true, "model": "mobilenet_v3_small"}
```

#### Verify Endpoint (Manual Test)

Generate a test image and verify:
```bash
python3 - << 'PY'
import base64, numpy as np, cv2, json
img = 255*np.ones((224,224,3), dtype=np.uint8)
_, buf = cv2.imencode(".jpg", img)
print(json.dumps({"image_b64": base64.b64encode(buf).decode(), "challenge_word":"orchid"}))
PY
```

Copy the JSON output and use it with curl:
```bash
curl -X POST http://localhost:8000/verify \
  -H "Content-Type: application/json" \
  -d '{"image_b64":"<BASE64_STRING>","challenge_word":"orchid"}'
```

Expected response:
```json
{
  "ok": true,
  "label": "ProfA",
  "confidence": 0.5234,
  "latency_ms": 15
}
```

### 5. Test the Dashboard

Open browser to: http://localhost:8501

1. Upload any image (jpg, jpeg, png)
2. Dashboard auto-fills challenge word
3. Click "Verify" to see results

## Phase 0: Geolocation-first Authentication

### Overview
Before any photo verification, the system verifies students are physically in the classroom using IP-based geolocation compared against professor-calibrated coordinates.

### Features
- **Multiple Providers**: Google Geolocation API, ip-api.com (free), or Mock provider for dev
- **Configurable Epsilon**: Professor sets acceptable distance radius in meters
- **Client GPS Override**: Optional HTML5 GPS coordinates for higher accuracy
- **Full Logging**: All verification attempts logged to `artifacts/geo/verify_log.jsonl`

### Configuration

Environment variables in `.env`:
```bash
GOOGLE_API_KEY=              # Optional: for Google Geolocation API
GEO_PROVIDER=auto            # auto | google | ipapi | mock
GEO_EPSILON_M=60             # Default epsilon (meters)
TRUST_X_FORWARDED_FOR=true   # Use X-Forwarded-For for client IP
```

**Provider Selection:**
- `auto`: Uses Google if API key is set, otherwise ip-api.com
- `google`: Google Geolocation API (requires GOOGLE_API_KEY)
- `ipapi`: Free ip-api.com service (no key required)
- `mock`: Returns Harvard Yard coordinates for offline dev/testing

### Professor Workflow

#### 1. Calibrate Classroom Location

Via Dashboard:
1. Open http://localhost:8501
2. Enter classroom latitude and longitude
3. Set epsilon (acceptable distance in meters)
4. Click "Save Calibration"

Via API:
```bash
curl -X POST http://localhost:8000/geo/calibrate \
  -H "Content-Type: application/json" \
  -d '{"lat":42.3770,"lon":-71.1167,"epsilon_m":60}'
```

Response:
```json
{
  "ok": true,
  "calibration": {
    "lat": 42.377,
    "lon": -71.1167,
    "epsilon_m": 60,
    "updated_at": 1697222400
  }
}
```

Calibration is persisted in `artifacts/config/calibration.json`.

#### 2. Check Calibration Status

```bash
curl http://localhost:8000/geo/status
```

### Student Workflow

#### Verify Location by IP

Via Dashboard:
1. Click "Verify by IP/GPS" button
2. System detects your IP and resolves to coordinates
3. Distance to classroom is calculated
4. Pass/fail based on epsilon threshold

Via API:
```bash
curl -X POST http://localhost:8000/geo/verify \
  -H "Content-Type: application/json" \
  -d '{}'
```

Response (success):
```json
{
  "ok": true,
  "source": "ip_geo",
  "client_ip": "128.103.224.1",
  "distance_m": 45.231,
  "epsilon_m": 60,
  "estimated_lat": 42.3765,
  "estimated_lon": -71.1172,
  "estimated_accuracy_m": 1000.0
}
```

Response (too far):
```json
{
  "ok": false,
  "source": "ip_geo",
  "client_ip": "8.8.8.8",
  "distance_m": 4523.891,
  "epsilon_m": 60,
  "estimated_lat": 37.4224,
  "estimated_lon": -122.0842,
  "estimated_accuracy_m": 1000.0
}
```

#### Verify with Client GPS Override

For higher accuracy (e.g., mobile apps with HTML5 geolocation):

```bash
curl -X POST http://localhost:8000/geo/verify \
  -H "Content-Type: application/json" \
  -d '{
    "client_gps_lat": 42.37710,
    "client_gps_lon": -71.11660,
    "client_gps_accuracy_m": 15
  }'
```

Response:
```json
{
  "ok": true,
  "source": "client_gps",
  "client_ip": "128.103.224.1",
  "distance_m": 12.456,
  "epsilon_m": 60,
  "estimated_lat": 42.3771,
  "estimated_lon": -71.1166,
  "estimated_accuracy_m": 15.0
}
```

### Artifacts & Logs

**Calibration:**
- Location: `artifacts/config/calibration.json`
- Contains: lat, lon, epsilon_m, updated_at timestamp

**Verification Log:**
- Location: `artifacts/geo/verify_log.jsonl`
- Format: JSON Lines (one JSON object per line)
- Contains: timestamp, IP, source, coordinates, distance, pass/fail

Example log entry:
```json
{"ok":true,"ip":"128.103.224.1","source":"ip_geo","lat":42.3765,"lon":-71.1172,"acc_m":1000.0,"dist_m":45.231,"eps_m":60,"ts":1697222450}
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/geo/calibrate` | POST | Set classroom coordinates and epsilon |
| `/geo/status` | GET | Get current calibration |
| `/geo/verify` | POST | Verify student location |
| `/healthz` | GET | Health check (includes geo_provider info) |

### Distance Calculation

Uses **Haversine formula** for great-circle distance on Earth's surface:

```
distance_m = 2 * R * arcsin(sqrt(
  sin²((lat2-lat1)/2) + 
  cos(lat1) * cos(lat2) * sin²((lon2-lon1)/2)
))
```

Where R = 6,371,000 meters (Earth's mean radius).

### Production Deployment Notes

1. **Behind Reverse Proxy**: Set `TRUST_X_FORWARDED_FOR=true` to use the original client IP from X-Forwarded-For header

2. **Google API**: For production accuracy, obtain a Google API key:
   - Enable Geolocation API in Google Cloud Console
   - Set `GOOGLE_API_KEY` in `.env`
   - Set `GEO_PROVIDER=google`

3. **Rate Limits**:
   - ip-api.com: 45 requests/minute (free tier)
   - Google: Pay-per-use, higher accuracy

4. **Epsilon Tuning**:
   - WiFi/IP-based: 50-100m recommended (typical IP geolocation accuracy)
   - GPS-based: 10-30m possible with good signal
   - Consider building layout and WiFi AP distribution

5. **Privacy**: Log entries contain IP addresses; ensure GDPR/privacy compliance

### Development & Testing

**Mock Provider** (for offline development):
```bash
# In .env
GEO_PROVIDER=mock
```

Returns Harvard Yard coordinates (42.3745, -71.1189) with 800m accuracy for all requests.

**Testing Different Locations:**

Calibrate to Harvard:
```bash
curl -X POST http://localhost:8000/geo/calibrate \
  -H "Content-Type: application/json" \
  -d '{"lat":42.3770,"lon":-71.1167,"epsilon_m":100}'
```

Test with GPS near Harvard (should pass):
```bash
curl -X POST http://localhost:8000/geo/verify \
  -H "Content-Type: application/json" \
  -d '{"client_gps_lat":42.3765,"client_gps_lon":-71.1170,"client_gps_accuracy_m":20}'
```

Test with GPS far from Harvard (should fail):
```bash
curl -X POST http://localhost:8000/geo/verify \
  -H "Content-Type: application/json" \
  -d '{"client_gps_lat":40.7128,"client_gps_lon":-74.0060,"client_gps_accuracy_m":20}'
```

## Repository Structure

```
AC215-HARV/
├── README.md                    # This file
├── EVIDENCE.md                  # Testing evidence documentation
├── Makefile                     # One-command orchestration
├── pytest.ini                   # Pytest configuration
├── requirements-test.txt        # Testing dependencies
├── docker-compose.yml           # Full pipeline definition
├── params.yaml                  # ML hyperparameters
├── dvc.yaml                     # DVC pipeline (optional)
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
│
├── data/
│   ├── raw/                     # Raw input data
│   ├── interim/                 # Ingestion output
│   └── processed/               # Train/val/test splits
│
├── artifacts/
│   ├── checkpoints/             # Training checkpoints
│   ├── model/                   # Exported TorchScript model
│   ├── metrics.json             # Evaluation metrics
│   └── samples/                 # Sample API responses
│
├── evidence/                    # Testing evidence (gitignored)
│   ├── coverage/                # Coverage reports
│   ├── e2e/                     # E2E test results
│   ├── load/                    # Load test results
│   ├── logs/                    # Service logs
│   └── screenshots/             # Verification screenshots
│
├── infra/
│   ├── setup.md                 # Infrastructure runbook
│   └── screenshots/             # Infrastructure screenshots
│
├── scripts/
│   ├── run_tests.sh             # Test execution script
│   ├── wait_for_services.sh     # Service readiness check
│   └── export_evidence.sh       # Evidence export script
│
├── tests/
│   ├── conftest.py              # Shared test fixtures
│   ├── unit/                    # Unit tests (fast, isolated)
│   ├── integration/             # Integration tests (multi-service)
│   ├── e2e/                     # End-to-end tests (full system)
│   └── load/                    # Load tests (k6)
│
├── ingestion/                   # Data ingestion component
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/ingest.py
│
├── preprocess/                  # Data preprocessing component
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/preprocess.py
│
├── train/                       # Model training component
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/train.py
│
├── evaluate/                    # Model evaluation component
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/evaluate.py
│
├── export/                      # Model export component
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/export.py
│
├── serve/                       # FastAPI serving component
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/
│       ├── app.py               # API endpoints
│       ├── geo.py               # Geolocation utilities
│       └── postprocess.py       # Post-processing utilities
│
├── dashboard/                   # Streamlit dashboard
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── app/app.py
│
├── docs/
│   ├── testing.md               # Testing documentation
│   ├── pipeline.md              # Pipeline documentation
│   └── rag.md                   # RAG documentation
│
└── .github/
    └── workflows/
        └── ci.yml               # CI/CD workflow (lint, test, load test)
```

## Testing & Validation

### Overview

Comprehensive testing infrastructure for Milestone 2 validation:
- **Unit Tests**: Fast, isolated function tests
- **Integration Tests**: Multi-service API and artifact validation
- **E2E Tests**: Complete workflow verification
- **Load Tests**: Performance validation with k6 (100+ concurrent users)
- **CI/CD**: Automated GitHub Actions workflow
- **Coverage**: 50%+ test infrastructure coverage

### Quick Start

**Run all tests:**
```bash
# Prerequisites: services must be running
make run

# In another terminal
make test
```

**Complete verification (one command):**
```bash
make verify
```
This builds services, runs all tests, and generates evidence.

### Test Suites

**Unit Tests** (no services required):
```bash
make test-unit
# Tests: haversine distance, param validation, image utils
# Fast execution: < 5 seconds
```

**Integration Tests** (requires services):
```bash
make test-integration
# Tests: API endpoints, artifact validation
# Validates: /healthz, /geo/*, /verify endpoints
```

**End-to-End Tests** (full workflow):
```bash
make test-e2e
# Tests: Complete calibration → geo verify → image verify workflow
# Generates: evidence/e2e/e2e_results.json
```

**Load Tests** (performance):
```bash
make test-load
# Requires: k6 installed (brew install k6)
# Load profile: 0→20→50→100→50→0 users
# Success criteria: p95 < 1s, error rate < 10%
```

### Coverage Reports

**Generate coverage:**
```bash
make coverage
```
Opens HTML coverage report showing line-by-line test coverage.

**Target:** 50%+ test infrastructure coverage

### Evidence Collection

**Export all evidence:**
```bash
make evidence
```

Creates:
- `evidence/coverage/` - HTML and XML coverage reports
- `evidence/e2e/` - E2E test results (JSON)
- `evidence/load/` - Load test results (JSON)
- `evidence/logs/` - Service logs
- `evidence/screenshots/` - Manual screenshots
- `milestone2_evidence_[timestamp].tar.gz` - Submission archive

### CI/CD Workflow

**GitHub Actions** (`.github/workflows/ci.yml`):
- **Lint**: ruff, mypy code quality checks
- **Test**: Full test suite with coverage (80% threshold)
- **Load Test**: Performance validation (main branch only)
- **Artifacts**: Evidence uploaded for 30 days

**Triggers:**
- Push to main/develop
- Pull requests to main/develop

**View results:**
- GitHub → Actions tab → Download artifacts

### Documentation

- **EVIDENCE.md**: Complete testing documentation
- **docs/testing.md**: Detailed testing guide
- Run `make help` for all available commands

### Validation Checklist

Before submission:
- [ ] Services build and run (`make run`)
- [ ] Health check passes (`curl localhost:8000/healthz`)
- [ ] All tests pass (`make test`)
- [ ] Coverage ≥ 50% (`make coverage`)
- [ ] Load tests complete (`make test-load`)
- [ ] Evidence exported (`make evidence`)
- [ ] Screenshots captured
- [ ] Archive created

## Deliverables

### Created Artifacts
- **Model**: `artifacts/model/model.torchscript.pt`
- **Metadata**: `artifacts/model/metadata.json`
- **Metrics**: `artifacts/metrics.json`
- **Sample Response**: `artifacts/samples/sample_response.json`

### Testing Artifacts
- **Coverage Reports**: `evidence/coverage/html/index.html`
- **E2E Results**: `evidence/e2e/e2e_results.json`
- **Load Test Results**: `evidence/load/results.json`
- **Service Logs**: `evidence/logs/`
- **Submission Archive**: `milestone2_evidence_[timestamp].tar.gz`

### Logs & Documentation
- **Testing Guide**: `EVIDENCE.md`
- **Testing Docs**: `docs/testing.md`
- **Setup Guide**: `infra/setup.md`
- **Screenshots**: `evidence/screenshots/`

## Configuration

### Environment Variables (.env)
```bash
WANDB_API_KEY=              # Optional: W&B API key for experiment tracking
WANDB_DISABLED=true         # Set to false to enable W&B
SERVICE_PORT=8000           # API port
DASH_PORT=8501              # Dashboard port
CHALLENGE_WORD=orchid       # Liveness challenge word
```

### Model Parameters (params.yaml)
```yaml
seed: 42
img_size: 224
epochs: 3
batch_size: 16
lr: 0.0005
model_name: mobilenet_v3_small  # or efficientnet_lite0
classes: ["ProfA", "Room1"]     # Demo classes
```

## Makefile Commands

### Pipeline Commands
```bash
make run      # Build and run full pipeline (blocking)
make down     # Stop all services and remove volumes
make logs     # Follow logs from all services
make clean    # Remove generated artifacts and data
```

### Testing Commands
```bash
make test              # Run all tests (unit + integration + e2e)
make test-unit         # Run unit tests only
make test-integration  # Run integration tests (requires services)
make test-e2e          # Run end-to-end tests (requires services)
make test-load         # Run load tests with k6
make verify            # Complete verification: build + test + evidence
make coverage          # Generate and view coverage report
make evidence          # Export evidence for submission
make help              # Show all available commands
```

## Current Limitations & Future Work

### Milestone 2 Scope
- ✅ Transfer learning vision track
- ✅ Basic liveness (word challenge)
- ✅ Full containerization
- ✅ CPU-only training
- ✅ **Real Face Dataset**: Kaggle human faces dataset (7,219 images)
- ✅ **Face Recognition Pipeline**: Automatic face detection and classification
- ✅ **Blurry Face Recognition**: Fine-tuning for distance/blur robustness
- ✅ **Enhanced Data Processing**: Face detection, blur augmentation, advanced evaluation
- ❌ MediaPipe blink detection (MS3)
- ❌ GPU acceleration (MS3+)

### Recent Enhancements (Milestone 2 Complete)
1. **Real Face Data Integration**: Successfully integrated Kaggle human faces dataset
2. **Advanced Face Processing**: OpenCV face detection with automatic ProfA/Room1 classification
3. **Blur Augmentation Pipeline**: Distance simulation with multiple blur levels (0.0, 0.5, 1.0, 1.5, 2.0)
4. **Enhanced Training**: Transfer learning with ImageNet pretrained weights and face-specific augmentation
5. **Comprehensive Evaluation**: Face-specific metrics, confusion matrices, and blur performance analysis
6. **Robust Fallback**: Automatic fallback to synthetic data if real data unavailable
7. **Diagnostic Tools**: Dataset verification, quality analysis, and setup automation

### Next Steps (Milestone 3)
1. **MediaPipe Liveness**: Implement blink detection using MediaPipe Face Mesh
2. **GPU Support**: Add CUDA support for faster training
4. **Model Optimization**: Quantization, pruning for edge deployment
5. **Advanced Monitoring**: Add Prometheus metrics, Grafana dashboards

## Troubleshooting

### Port Conflicts
If ports 8000/8501 are in use:
```bash
# Edit .env
SERVICE_PORT=8080
DASH_PORT=8502
```

### Memory Issues
Reduce batch size in `params.yaml`:
```yaml
batch_size: 8  # or 4
```

### Docker Build Failures
Clear Docker cache:
```bash
docker system prune -a
make run
```

### Permission Issues (Linux)
Add user to docker group:
```bash
sudo usermod -aG docker $USER
```

## Development

### Running Individual Components
```bash
# Build specific service
docker compose build preprocess

# Run specific service
docker compose run preprocess

# View service logs
docker compose logs -f train
```

### Local Development (without Docker)
```bash
cd train/
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e .
python -m src.train
```

## Deployment

HARV can be deployed to Google Cloud Platform (GCP) using Cloud Run. See detailed guides:

- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Comprehensive deployment guide
- **[GCP_QUICK_START.md](./GCP_QUICK_START.md)** - Quick reference and TL;DR

### Quick Deploy to GCP

```bash
# 1. Setup GCP service account
make gcp-setup

# 2. Deploy to Cloud Run (uploads artifacts + deploys)
make gcp-full-deploy
```

**GCP Configuration:**
- Project ID: `ac215-475022`
- Region: `us-central1`
- Service: `harv-backend`

## License

[Your License Here]

## Contact

[Your Contact Information]

---

## Grader Quick Start

### Option 1: Full Verification (Recommended)
```bash
# Clone and setup
git clone <repository-url>
cd AC215-HARV
cp .env.example .env

# Run complete verification (builds, tests, generates evidence)
make verify

# View evidence
open evidence/coverage/html/index.html  # Coverage report
cat evidence/e2e/e2e_results.json       # E2E results
```

### Option 2: Manual Testing
```bash
# Setup
cp .env.example .env

# Start pipeline
make run
# Wait for services to complete (all services show "done" or "running")

# Test API
curl http://localhost:8000/healthz

# Test dashboard
# Open http://localhost:8501 in browser

# Run tests (in new terminal)
make test

# Export evidence
make evidence
```

### Expected Results
- ✅ All Docker services build successfully
- ✅ API responds to health check
- ✅ Dashboard loads at http://localhost:8501
- ✅ All tests pass (unit, integration, e2e)
- ✅ Coverage ≥ 50%
- ✅ Evidence archive created: `milestone2_evidence_*.tar.gz`