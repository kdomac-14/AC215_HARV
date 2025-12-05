# HARV – Harvard Attendance Recognition and Verification

<p align="center">
  <img src="docs/evidence/harv_banner.png" alt="HARV Banner" width="600">
</p>

> **Milestone 5 Submission** – AC215 Fall 2024

[![CI](https://github.com/kdomac-14/AC215_HARV/actions/workflows/ci.yml/badge.svg)](https://github.com/kdomac-14/AC215_HARV/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Repository Structure](#repository-structure)
5. [Local Development Setup](#local-development-setup)
6. [Cloud Deployment](#cloud-deployment)
7. [CI/CD Overview](#cicd-overview)
8. [ML Workflow](#ml-workflow)
9. [Known Issues & Limitations](#known-issues--limitations)
10. [Contributors & Licensing](#contributors--licensing)

---

## Project Overview

### Problem Statement

Tracking lecture attendance at scale is a persistent challenge for universities. Traditional methods—paper sign-ins, manual roll calls, or simple clicker systems—are prone to fraud (proxy attendance), administrative overhead, and poor scalability across large courses. Instructors spend valuable time on logistics rather than teaching, while students lack a frictionless way to verify their presence.

### The HARV Solution

**HARV** (Harvard Attendance Recognition and Verification) is a mobile-first attendance system that combines **GPS geofencing** with **vision-based face verification** to provide accurate, fraud-resistant attendance tracking.

**How it works:**
1. **GPS-First Verification** – Students check in via the mobile app; if their location falls within the lecture hall's geofence, attendance is recorded instantly.
2. **Vision Fallback** – If GPS is unavailable or inconclusive (e.g., indoor signal issues), students can submit a selfie for face recognition against enrolled profiles.
3. **Professor Override** – Instructors have a dashboard to view real-time attendance, manually override false negatives, and export reports.

### Technology Stack

HARV is built on a modern, cloud-native stack optimized for scalability and reproducibility:

| Layer | Technology |
|-------|------------|
| **Mobile App** | React Native + Expo Router |
| **Backend API** | FastAPI (Python 3.11) |
| **ML Model** | MobileNetV3-Small (PyTorch), transfer learning |
| **Infrastructure** | GCP (GKE, Cloud Storage, Artifact Registry) |
| **IaC** | Pulumi (TypeScript) |
| **Orchestration** | Kubernetes with HPA auto-scaling |
| **CI/CD** | GitHub Actions |
| **Data Versioning** | DVC |

---

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              HARV Architecture                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────┐                                                       │
│   │   Mobile App     │                                                       │
│   │  (React Native)  │                                                       │
│   │                  │                                                       │
│   │  • Student Mode  │                                                       │
│   │  • Professor Mode│                                                       │
│   └────────┬─────────┘                                                       │
│            │ HTTPS                                                           │
│            ▼                                                                 │
│   ┌──────────────────┐         ┌──────────────────────────────────────────┐ │
│   │   GCP Load       │         │           Google Kubernetes Engine        │ │
│   │   Balancer       │────────▶│  ┌──────────────────────────────────────┐│ │
│   │                  │         │  │         FastAPI Backend              ││ │
│   └──────────────────┘         │  │  ┌────────────┬────────────────────┐ ││ │
│                                │  │  │  /checkin  │  /instructor/*     │ ││ │
│                                │  │  │  /verify   │  /health           │ ││ │
│                                │  │  └────────────┴────────────────────┘ ││ │
│                                │  │              │                       ││ │
│                                │  │              ▼                       ││ │
│                                │  │  ┌──────────────────────────────────┐││ │
│                                │  │  │   ML Model (MobileNetV3-Small)  │││ │
│                                │  │  │   • Face verification           │││ │
│                                │  │  │   • TorchScript inference       │││ │
│                                │  │  └──────────────────────────────────┘││ │
│                                │  └──────────────────────────────────────┘│ │
│                                │                    │                      │ │
│                                │  ┌─────────────────┴────────────────────┐│ │
│                                │  │   HPA (Horizontal Pod Autoscaler)    ││ │
│                                │  │   • Min: 2 replicas                  ││ │
│                                │  │   • Max: 5 replicas                  ││ │
│                                │  │   • Target: 80% CPU utilization      ││ │
│                                │  └──────────────────────────────────────┘│ │
│                                └──────────────────────────────────────────┘ │
│                                             │                                │
│            ┌────────────────────────────────┴───────────────────────────┐   │
│            ▼                                                             ▼   │
│   ┌──────────────────┐                                    ┌──────────────┐  │
│   │  Cloud Storage   │                                    │   Firestore  │  │
│   │  (GCS)           │                                    │   Database   │  │
│   │                  │                                    │              │  │
│   │  • Model weights │                                    │  • Students  │  │
│   │  • Training data │                                    │  • Classes   │  │
│   │  • Artifacts     │                                    │  • Check-ins │  │
│   └──────────────────┘                                    └──────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Student Check-In** → Mobile app sends GPS coordinates to Load Balancer
2. **Geofence Validation** → FastAPI backend validates location against lecture hall bounds
3. **Vision Fallback** → If GPS fails, student uploads selfie → ML model verifies identity
4. **Attendance Recording** → Verified check-ins stored in Firestore
5. **Professor Dashboard** → Real-time attendance feed with override capability

---

## Features

### Student Attendance Flow
- **One-tap GPS check-in** with automatic geofence validation
- **Vision fallback** using device camera when GPS is unavailable
- **Enrolled courses view** with class schedules and check-in history
- **Real-time feedback** on attendance status

### Vision Fallback System
- **MobileNetV3-Small** backbone with transfer learning (70% frozen layers)
- **Face detection preprocessing** using OpenCV Haar cascades
- **Blur augmentation** to handle poor lighting/camera shake
- **CPU-optimized inference** (~200ms per image on standard hardware)

### Professor Override Dashboard
- **Real-time attendance roster** per course
- **Manual override** for false negatives/edge cases
- **Student attendance history** with detailed summaries
- **Preset lecture hall locations** (Emerson, Sever, Science Center)

### Deployment Automation
- **Infrastructure as Code** with Pulumi (TypeScript)
- **One-command deployment** via `pulumi up`
- **Automated Docker builds** with multi-stage Dockerfiles
- **Secrets management** via Pulumi config encryption

### ML Retraining Pipeline
- **DVC-tracked stages**: ingest → preprocess → train → evaluate → export
- **Reproducible training** with `params.yaml` configuration
- **Automated metrics export** (accuracy, confusion matrix, ROC-AUC)
- **TorchScript model export** for production serving

### Scalability via HPA
- **Horizontal Pod Autoscaler** configured for 2-5 replicas
- **CPU-based scaling** at 80% utilization threshold
- **Zero-downtime deployments** with rolling updates
- **Node pool auto-repair** and auto-upgrade enabled

---

## Repository Structure

```
AC215_HARV/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── api/               # Route handlers (checkin, instructor)
│   │   ├── config/            # Settings and configuration
│   │   ├── models/            # SQLModel/Pydantic schemas
│   │   └── main.py            # Application entry point
│   ├── ml/                    # Vision model loader for API
│   └── tests/                 # pytest suite (unit + integration)
│
├── frontend/                   # React Native Expo mobile app
│   ├── app/
│   │   ├── student/           # Student mode screens
│   │   └── professor/         # Professor mode screens
│   └── config/                # App configuration (locations.ts)
│
├── ml/                         # ML training scripts and configs
│   ├── configs/               # YAML training configurations
│   ├── scripts/               # Utility scripts
│   └── train_cnn.py           # Legacy training entry point
│
├── infra/                      # Pulumi infrastructure as code
│   ├── index.ts               # GKE cluster + K8s resources
│   ├── Pulumi.yaml            # Project configuration
│   └── screenshots/           # Deployment evidence
│
├── ingestion/                  # Data ingestion component
│   └── src/ingest.py          # Creates manifest CSV from raw images
│
├── preprocess/                 # Data preprocessing component
│   └── src/preprocess.py      # Face detection, augmentation, splits
│
├── train/                      # Model training component
│   └── src/train.py           # Transfer learning with MobileNetV3
│
├── evaluate/                   # Model evaluation component
│   └── src/evaluate.py        # Metrics, confusion matrix, ROC-AUC
│
├── export/                     # Model export component
│   └── src/export.py          # TorchScript conversion
│
├── serve/                      # Production serving API
│   └── src/app.py             # FastAPI with geo + vision endpoints
│
├── services/                   # Microservices (API, RAG, Vision)
│   ├── api/                   # Core API service
│   ├── rag/                   # RAG service (if applicable)
│   └── vision/                # Vision inference service
│
├── scripts/                    # Utility and deployment scripts
│   ├── deploy_to_gcp.sh       # Cloud Run deployment
│   ├── setup_gcp.sh           # Service account setup
│   └── run_tests.sh           # Test runner
│
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md        # Detailed architecture docs
│   ├── evidence/              # Screenshots, metrics, examples
│   └── *.md                   # Various documentation files
│
├── .github/workflows/          # CI/CD pipelines
│   └── ci.yml                 # Lint, test, build workflow
│
├── dvc.yaml                    # DVC pipeline definition
├── params.yaml                 # ML hyperparameters
├── docker-compose.yml          # Local development orchestration
├── Makefile                    # Task automation
├── pyproject.toml              # Python project configuration
└── DEPLOYMENT.md               # Detailed deployment guide
```

---

## Local Development Setup

### Prerequisites

| Tool | Version | Installation |
|------|---------|--------------|
| Python | 3.11+ | `pyenv install 3.11` or [python.org](https://python.org) |
| Node.js | 20.x | `nvm install 20` or [nodejs.org](https://nodejs.org) |
| Docker | 24.0+ | [docker.com](https://docker.com) |
| DVC | 3.x | `pip install dvc` |

### 1. Clone and Setup Environment

```bash
# Clone repository
git clone https://github.com/kdomac-14/AC215_HARV.git
cd AC215_HARV

# Create Python virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies (including dev tools)
pip install --upgrade pip
pip install -e ".[dev]"
```

### 2. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your values:
# - GOOGLE_API_KEY (for geolocation)
# - PROJECT_ID=ac215-475022
# - GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
```

### 3. Run Backend Locally

```bash
# Option A: Using uvicorn directly
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Option B: Using Docker Compose (full stack)
make run
```

The API will be available at `http://localhost:8000`. Key endpoints:
- `GET /health` – Health check with demo course info
- `POST /api/checkin/gps` – GPS-based attendance
- `POST /api/checkin/vision` – Vision fallback
- `GET /api/instructor/attendance` – Attendance roster

### 4. Run Mobile App Locally

```bash
cd frontend
npm install
npm run start
```

This launches Expo DevTools. Scan the QR code with **Expo Go** (iOS/Android) or press `i` for iOS Simulator.

**Configure API URL** (if backend is not on localhost):
```bash
# In frontend/.env
EXPO_PUBLIC_API_URL=http://YOUR_LOCAL_IP:8000
```

### 5. Load Test Data

The backend automatically seeds demo courses on first run. To verify:

```bash
curl http://localhost:8000/health | jq
```

---

## Cloud Deployment

HARV deploys to Google Cloud Platform using Pulumi for infrastructure management. For detailed instructions, see **[DEPLOYMENT.md](DEPLOYMENT.md)**.

### Quick Deployment Summary

```bash
# 1. Build and push backend Docker image
make build-backend-image
make push-backend-image

# 2. Configure Pulumi stack
cd infra
npm install
pulumi stack init prod
pulumi config set gcp:project ac215-475022
pulumi config set gcp:region us-central1
pulumi config set harv:backendImage <your-image-url>

# 3. Deploy infrastructure
pulumi up

# 4. Get Load Balancer URL
pulumi stack output backendExternalUrl
```

### Post-Deployment

1. **Update mobile app** with the Load Balancer URL:
   ```bash
   # In frontend/.env
   EXPO_PUBLIC_API_URL=http://<LOAD_BALANCER_IP>
   ```

2. **Verify deployment**:
   ```bash
   curl http://<LOAD_BALANCER_IP>/health
   ```

---

## CI/CD Overview

### GitHub Actions Workflow

The CI pipeline (`.github/workflows/ci.yml`) runs on every push and PR to `main` and `develop`:

| Job | Description | Triggers |
|-----|-------------|----------|
| **lint** | Ruff + Black formatting checks | All pushes/PRs |
| **backend** | pytest with coverage (≥50% enforced) | After lint passes |
| **frontend** | `npm ci` + ESLint | After backend passes |

### Coverage Enforcement

```yaml
# pytest runs with coverage threshold
pytest --cov --cov-fail-under=50
```

Coverage reports are uploaded as artifacts for each CI run.

### CD Pipeline (Manual Trigger)

For production deployments:

1. **Build Docker image** → Push to Artifact Registry
2. **Update Pulumi config** with new image tag
3. **Run `pulumi up`** → Rolling update on GKE
4. **Verify health endpoint** returns new version

```bash
# Full deployment from local machine
make push-backend-image IMAGE_TAG=$(git rev-parse --short HEAD)
cd infra && pulumi up --yes
```

---

## ML Workflow

### Pipeline Stages

HARV uses a DVC-managed ML pipeline defined in `dvc.yaml`:

```
ingest → preprocess → train → evaluate → export
```

### Running the Pipeline

```bash
# Run full pipeline via Docker Compose
make all

# Or run individual stages
make data        # Ingestion
make preprocess  # Face detection + augmentation
make train_cpu   # MobileNetV3 transfer learning
make evaluate    # Metrics + confusion matrix
make export      # TorchScript conversion
```

### Hyperparameters (`params.yaml`)

```yaml
model_name: mobilenet_v3_small
epochs: 10
batch_size: 32
lr: 0.001
freeze_ratio: 0.7        # Freeze 70% of backbone layers
img_size: 224
train_split: 0.7
val_split: 0.2
test_split: 0.1
```

### Metrics Gating

The evaluation stage outputs `artifacts/metrics.json` with:
- **test_accuracy** – Must exceed threshold for promotion
- **confusion_matrix** – Per-class breakdown
- **roc_auc** – For binary classification tasks

### Model Promotion

1. Train produces `artifacts/checkpoints/best.pt`
2. Evaluate generates metrics + confusion matrix
3. Export converts to `artifacts/model/model.torchscript.pt`
4. Upload to GCS: `gsutil cp artifacts/model/* gs://ac215-475022-assets/artifacts/model/`
5. Serve API loads model from GCS on startup

### Production Model Loading

The serve API loads the TorchScript model at startup:
```python
# serve/src/app.py
model = torch.jit.load("artifacts/model/model.torchscript.pt")
```

In cloud deployment, models are downloaded from GCS to the container.

---

## Known Issues & Limitations

### Current Limitations

| Issue | Impact | Workaround |
|-------|--------|------------|
| **CPU-only training** | Slower training (~10 min for 10 epochs) | Use pre-trained checkpoints or cloud GPUs |
| **Indoor GPS accuracy** | May trigger vision fallback unnecessarily | Calibrate geofence radius per venue |
| **Cold starts on GKE** | 2-3s latency for first request after scale-up | Set `minReplicas: 1` in HPA |
| **No real-time sync** | Professor dashboard requires manual refresh | Planned: WebSocket integration |
| **Single-region deployment** | Higher latency for non-US users | Multi-region deployment not yet implemented |

### Known Bugs

1. **TypeScript warnings in Expo** – IDE shows false positives; app runs correctly with Expo's TypeScript config
2. **SQLite concurrency** – Local dev only; production uses Firestore
3. **Face detection failures** – Haar cascades may miss profiles at extreme angles

### Security Considerations

- **API keys** stored in `.env` (gitignored)
- **Service account JSON** never committed
- **Unauthenticated endpoints** for demo; production should enable IAM auth
- **CORS** configured for specific origins in production

---

## Contributors & Licensing

### Team Members

| Name | Role | Contributions |
|------|------|---------------|
| **HARV Team** | Full Stack | Architecture, ML, Mobile, Infrastructure |

### Course Information

- **Course**: AC215 – MLOps / Machine Learning Systems Design
- **Term**: Fall 2024
- **Institution**: Harvard University

### License

This project is licensed under the **MIT License** – see [LICENSE](LICENSE) for details.

```
MIT License

Copyright (c) 2024 HARV Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## Additional Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** – Detailed GCP deployment guide
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** – System architecture deep dive
- **[docs/MOBILE_APP.md](docs/MOBILE_APP.md)** – Mobile app runbook
- **[docs/model_results.md](docs/model_results.md)** – ML experiment tracking
- **[VERIFICATION.md](VERIFICATION.md)** – Milestone verification checklist

---

<p align="center">
  <b>Built with ❤️ for AC215</b>
</p>
