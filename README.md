# HARV - Harvard Attendance Recognition and Verification

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-24.0%2B-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Milestone 2**: Transfer Learning Vision Track with Full Containerization + Geolocation-First Verification

End-to-end ML pipeline for face recognition with geolocation-based attendance verification. Uses transfer learning (MobileNetV3 on CPU) with containerized components for reproducible deployment.

---

## 🎯 Project Overview

HARV enables classroom attendance verification through a two-stage process:

1. **Geolocation Verification** (Phase 0): Students must be physically present in the classroom (IP/GPS-based)
2. **Face Recognition** (Phase 1): Visual verification with liveness challenge ("word of the day")

**Key Features:**
- CPU-optimized training (no GPU required for graders)
- Containerized pipeline (Docker Compose orchestration)
- Real face dataset support with blur augmentation
- Geolocation providers: Google API, ip-api.com, or Mock
- Production-ready API (FastAPI + TorchScript inference)
- Interactive dashboard (Streamlit)

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│   Ingestion → Preprocess → Train → Evaluate → Export       │
│       ↓           ↓          ↓         ↓         ↓          │
│                    Artifacts Storage                        │
│                           ↓                                  │
│            ┌──────────────┴──────────────┐                 │
│            ↓                              ↓                  │
│      Serve (API)  ←──────────→  Dashboard (UI)             │
│            ↓                                                 │
│     Geolocation Subsystem                                   │
└─────────────────────────────────────────────────────────────┘
```

**See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) for detailed system design.**

---

## 🚀 Quick Start

### Prerequisites

| Tool | Version | Check | Install |
|------|---------|-------|---------|
| Docker | 24.0+ | `docker --version` | [Get Docker](https://docs.docker.com/get-docker/) |
| Docker Compose | 2.0+ | `docker compose version` | Included with Docker Desktop |

**System Requirements:** 8GB RAM, 10GB disk space

### 1. Clone & Setup

```bash
git clone https://github.com/kdomac-14/AC215_HLAV.git
cd AC215_HLAV

# Copy environment template
cp .env.example .env

# Optional: Edit .env for W&B, Google API, etc.
```

### 2. Run Full Pipeline

```bash
make run
```

**This single command:**
- Builds all Docker images (~5-10 min first time)
- Runs pipeline: ingestion → preprocess → train → evaluate → export (~2-3 min)
- Starts API (port 8000) and Dashboard (port 8501)

**Expected Output:**
```
✅ All services built successfully
✅ Pipeline complete: model saved to artifacts/model/
✅ Services ready:
   - API: http://localhost:8000
   - Dashboard: http://localhost:8501
```

### 3. Validate System

**Health check:**
```bash
curl http://localhost:8000/healthz
```

Expected:
```json
{
  "ok": true,
  "model": "mobilenet_v3_small",
  "classes": ["ProfA", "Room1"]
}
```

**Dashboard:** Open http://localhost:8501 in browser

**Run tests:**
```bash
make test
```

---

## 📊 Pipeline Components

| Component | Purpose | Input | Output | Time |
|-----------|---------|-------|--------|------|
| **Ingestion** | Create manifest | Raw images | `manifest.csv` | <1s |
| **Preprocess** | Face detection + augmentation | Manifest + images | Train/val/test splits | 1-2min |
| **Train** | Transfer learning | Processed images | Model checkpoint | 2-3min |
| **Evaluate** | Metrics computation | Checkpoint + test set | `metrics.json` | 10s |
| **Export** | TorchScript export | Checkpoint | `model.torchscript.pt` | 5s |

**Detailed docs:** [docs/PIPELINE.md](./docs/PIPELINE.md)

---

## 🧪 Testing & Coverage

### Run All Tests

```bash
make test
```

Runs:
- **Unit tests**: Fast, isolated function tests (<5s)
- **Integration tests**: API endpoint validation (requires services)
- **E2E tests**: Complete workflow verification

### Coverage Report

```bash
make coverage
```

Opens HTML report showing **≥50% test coverage** (Milestone 2 requirement).

**Current Coverage:** 52% (test infrastructure focus)

### Complete Verification

```bash
make verify
```

Builds, tests, and generates evidence package for submission.

**See [docs/testing.md](./docs/testing.md) for comprehensive testing guide.**

---

## 🔧 Configuration

### Environment Variables (`.env`)

```bash
# Core Settings
WANDB_DISABLED=true           # Set false to enable W&B tracking
SERVICE_PORT=8000             # API port
DASH_PORT=8501                # Dashboard port
CHALLENGE_WORD=orchid         # Liveness challenge word

# Geolocation
GEO_PROVIDER=mock             # auto | google | ipapi | mock
GEO_EPSILON_M=60              # Acceptable distance (meters)
GOOGLE_API_KEY=               # Optional: for Google Geolocation API

# GCP Deployment (Optional)
PROJECT_ID=ac215-475022
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
```

### Model Hyperparameters (`params.yaml`)

```yaml
# Model
model_name: mobilenet_v3_small  # or efficientnet_b0
freeze_ratio: 0.7               # Freeze 70% of layers

# Training
epochs: 3
batch_size: 16
lr: 0.0005

# Data
img_size: 224
use_real_faces: false           # true for real datasets
blur_augmentation: true         # Simulate distance effects
seed: 42
```

---

## 🗂️ Repository Structure

```
AC215-HARV/
├── README.md                   # This file
├── Makefile                    # Single-command workflows
├── docker-compose.yml          # Service orchestration
├── params.yaml                 # ML hyperparameters
├── pyproject.toml              # Linting, testing config
├── .env.example                # Environment template
│
├── docs/                       # 📚 Comprehensive documentation
│   ├── ARCHITECTURE.md         # System design, data flow
│   ├── PIPELINE.md             # Component details, CLI usage
│   ├── DECISIONS.md            # Model selection rationale + benchmarks
│   ├── RUNBOOK.md              # Clean-clone setup, troubleshooting
│   └── testing.md              # Test suite, coverage guide
│
├── ingestion/                  # Data manifest creation
│   ├── README.md
│   ├── Dockerfile
│   └── src/ingest.py
│
├── preprocess/                 # Face detection + augmentation
│   ├── README.md
│   ├── Dockerfile
│   └── src/preprocess.py
│
├── train/                      # Transfer learning
│   ├── README.md
│   ├── Dockerfile
│   └── src/train.py
│
├── evaluate/                   # Metrics computation
├── export/                     # TorchScript export
├── serve/                      # FastAPI inference API
├── dashboard/                  # Streamlit UI
│
├── tests/                      # Comprehensive test suite
│   ├── unit/                   # Fast, isolated tests
│   ├── integration/            # Multi-service tests
│   ├── e2e/                    # End-to-end workflows
│   └── load/                   # k6 performance tests
│
├── data/                       # Data storage (gitignored)
│   ├── raw/                    # Raw images
│   ├── interim/                # Ingestion output
│   └── processed/              # Train/val/test splits
│
├── artifacts/                  # Model artifacts (gitignored)
│   ├── checkpoints/            # Training checkpoints
│   ├── model/                  # Exported TorchScript
│   └── metrics.json            # Evaluation metrics
│
└── evidence/                   # Testing evidence (gitignored)
    ├── coverage/               # HTML & XML coverage reports
    ├── e2e/                    # E2E test results
    └── logs/                   # Service logs
```

---

## 🎓 Geolocation-First Verification

### Overview

Students must verify physical presence **before** photo verification.

**Providers:**
- **Google Geolocation API**: High accuracy (20-100m), requires API key
- **ip-api.com**: Free tier, moderate accuracy (500-2000m)
- **Mock**: Returns Harvard coordinates for offline testing

### Professor Workflow

**Calibrate classroom location:**
```bash
curl -X POST http://localhost:8000/geo/calibrate \
  -H "Content-Type: application/json" \
  -d '{"lat":42.3770,"lon":-71.1167,"epsilon_m":60}'
```

**Check status:**
```bash
curl http://localhost:8000/geo/status
```

### Student Workflow

**Verify by IP:**
```bash
curl -X POST http://localhost:8000/geo/verify -H "Content-Type: application/json" -d '{}'
```

**Verify with GPS override (mobile apps):**
```bash
curl -X POST http://localhost:8000/geo/verify \
  -H "Content-Type: application/json" \
  -d '{
    "client_gps_lat": 42.37710,
    "client_gps_lon": -71.11660,
    "client_gps_accuracy_m": 15
  }'
```

**See [docs/gps_location_guide.md](./docs/gps_location_guide.md) for detailed geolocation setup.**

---

## 📈 Model Performance

### Benchmarks (Synthetic Dataset)

| Model | Epoch Time (CPU) | Inference (CPU) | Size | Val Accuracy |
|-------|------------------|-----------------|------|--------------|
| **MobileNetV3-Small** | **45s** | **12ms** | **14MB** | **88.9%** |
| EfficientNet-B0 | 78s | 23ms | 21MB | 90.1% |
| ResNet18 | 62s | 18ms | 47MB | 89.5% |

**Winner:** MobileNetV3-Small (fastest, smallest, good accuracy)

**See [docs/DECISIONS.md](./docs/DECISIONS.md) for comprehensive model comparison and rationale.**

### Real Face Dataset Results

- **Training**: 507 images (70% × 5 blur levels)
- **Validation**: 108 images (15%)
- **Test**: 110 images (15%)
- **Accuracy**: 87-89% (robust to distance/blur)

---

## 💻 Development

### Run Individual Components

```bash
# Single component
docker compose run train

# View logs
docker compose logs -f serve

# Rebuild specific service
docker compose build preprocess
```

### Local Development (No Docker)

```bash
cd train/
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m src.train
```

---

## 🚢 Deployment

### Deploy to Google Cloud Run

```bash
# Setup GCP credentials
make gcp-setup

# Full deployment (upload artifacts + deploy API)
make gcp-full-deploy
```

**Configuration:**
- Project: `ac215-475022`
- Region: `us-central1`
- Service: `harv-backend`

**See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment guide.**

---

## 🛠️ Makefile Commands

| Command | Description |
|---------|-------------|
| `make run` | Build + run full pipeline + start services |
| `make test` | Run all tests (unit + integration + e2e) |
| `make verify` | Complete verification (build + test + evidence) |
| `make coverage` | Generate and view HTML coverage report |
| `make down` | Stop services and remove containers |
| `make clean` | Remove artifacts and generated data |
| `make evidence` | Export evidence for milestone submission |
| `make help` | Show all available commands |

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Edit .env
SERVICE_PORT=8080
DASH_PORT=8502
```

### Memory Issues

```yaml
# Edit params.yaml
batch_size: 8  # Reduce from 16
```

### Docker Build Failures

```bash
docker system prune -a
make run
```

**Full troubleshooting guide:** [docs/RUNBOOK.md](./docs/RUNBOOK.md)

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **README.md** (this file) | Quick start, overview |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System design, component diagram, data flow |
| [docs/PIPELINE.md](./docs/PIPELINE.md) | Detailed component docs, CLI usage, examples |
| [docs/DECISIONS.md](./docs/DECISIONS.md) | Model selection rationale, benchmarks, hyperparameters |
| [docs/RUNBOOK.md](./docs/RUNBOOK.md) | Clean-clone setup, troubleshooting, workflows |
| [docs/testing.md](./docs/testing.md) | Test suite, coverage, CI/CD |
| [ingestion/README.md](./ingestion/README.md) | Ingestion component details |
| [preprocess/README.md](./preprocess/README.md) | Preprocessing component details |
| [train/README.md](./train/README.md) | Training component details |

---

## ✅ Grader Quick Start

### Option 1: One-Command Verification

```bash
# Clone and setup
git clone <repository-url>
cd AC215_HLAV
cp .env.example .env

# Complete verification
make verify

# View results
open evidence/coverage/html/index.html
cat evidence/e2e/e2e_results.json
```

### Option 2: Manual Testing

```bash
# Start pipeline
make run

# Test API (in new terminal)
curl http://localhost:8000/healthz

# Test dashboard
open http://localhost:8501

# Run tests
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

---

## 🎯 Milestone 2 Checklist

- [x] Transfer learning vision track (MobileNetV3)
- [x] CPU-only training and inference
- [x] Full Docker containerization
- [x] Basic liveness detection (challenge word)
- [x] Real face dataset support
- [x] Blur augmentation for robustness
- [x] Comprehensive testing (unit, integration, e2e, load)
- [x] ≥50% test coverage
- [x] Geolocation-first verification
- [x] Production API + Dashboard
- [x] GCP Cloud Run deployment
- [x] Complete documentation

---

## 🚀 Future Work (Milestone 3+)

- [ ] MediaPipe blink detection (liveness)
- [ ] GPU acceleration support
- [ ] Model quantization for edge deployment
- [ ] Kubernetes horizontal scaling
- [ ] Prometheus + Grafana monitoring
- [ ] Advanced augmentation (AutoAugment)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

## 👥 Contact

For questions or issues, please open a GitHub issue or contact the HARV team.

---

## 📊 Project Stats

- **Lines of Code**: ~5,000
- **Test Coverage**: 52%
- **Components**: 7 containerized services
- **Documentation**: 10+ markdown files
- **Total Commits**: 100+
- **Contributors**: HARV Team

---

**Built with ❤️ for AC215 - Milestone 2**
