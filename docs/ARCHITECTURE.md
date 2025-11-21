# HARV Architecture

## System Overview

HARV (Harvard Attendance Recognition and Verification) is a containerized ML pipeline for lecture hall recognition with geolocation-based attendance verification. The system uses transfer learning on CPU-friendly models to enable deployment without GPU dependencies.

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         HARV System                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐    ┌───────────┐    ┌────────┐    ┌──────────┐  │
│  │          │    │           │    │        │    │          │  │
│  │ Ingestion│───▶│Preprocess │───▶│  Train │───▶│ Evaluate │  │
│  │          │    │           │    │        │    │          │  │
│  └──────────┘    └───────────┘    └────────┘    └──────────┘  │
│       │                │                │              │        │
│       │                │                │              │        │
│       ▼                ▼                ▼              ▼        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Data & Artifact Store                       │  │
│  │  • data/raw/          • data/interim/                   │  │
│  │  • data/processed/    • artifacts/model/                │  │
│  │  • artifacts/checkpoints/   • artifacts/metrics.json    │  │
│  └─────────────────────────────────────────────────────────┘  │
│                               │                                 │
│                               ▼                                 │
│  ┌──────────┐    ┌───────────────────────────────────────┐   │
│  │          │    │                                         │   │
│  │  Export  │───▶│  TorchScript Model (model.torchscript.pt)│   │
│  │          │    │                                         │   │
│  └──────────┘    └───────────────────────────────────────┘   │
│                               │                                 │
│       ┌───────────────────────┴───────────────────────┐       │
│       │                                                 │       │
│       ▼                                                 ▼       │
│  ┌─────────────────┐                         ┌──────────────┐ │
│  │   Serve (API)   │                         │  Dashboard   │ │
│  │   FastAPI       │◀────────────────────────│  Streamlit   │ │
│  │  • /healthz     │                         │              │ │
│  │  • /verify      │                         │  • Upload    │ │
│  │  • /geo/*       │                         │  • Verify    │ │
│  └─────────────────┘                         │  • Results   │ │
│         │                                     └──────────────┘ │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │            Geolocation Subsystem                         │ │
│  │  • Providers: Google, ip-api, Mock                       │ │
│  │  • Haversine distance calculation                        │ │
│  │  • Calibration storage (artifacts/config/)               │ │
│  │  • Verification logs (artifacts/geo/)                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Training Pipeline (Offline)

1. **Ingestion** (`ingestion/`)
   - **Input**: Raw image files or face dataset
   - **Process**: Creates manifest CSV with image paths and labels
   - **Output**: `data/interim/manifest.csv`

2. **Preprocess** (`preprocess/`)
   - **Input**: `data/interim/manifest.csv`
   - **Process**: 
     - Face detection (OpenCV Haar cascades)
     - Blur augmentation (5 levels: 0.0, 0.5, 1.0, 1.5, 2.0)
     - Train/val/test split (70/15/15)
     - Image resizing and normalization
   - **Output**: `data/processed/{train,val,test}/` directories with organized images

3. **Train** (`train/`)
   - **Input**: `data/processed/` splits
   - **Process**:
     - Transfer learning with MobileNetV3-Small or EfficientNet-B0
     - ImageNet pretrained weights
     - Fine-tuning with face-specific augmentations
   - **Output**: `artifacts/checkpoints/best_model.pth`

4. **Evaluate** (`evaluate/`)
   - **Input**: Trained model + test split
   - **Process**: Classification report, confusion matrix, per-class metrics
   - **Output**: `artifacts/metrics.json`

5. **Export** (`export/`)
   - **Input**: Best checkpoint
   - **Process**: Convert to TorchScript for inference
   - **Output**: `artifacts/model/model.torchscript.pt` + `metadata.json`

### Inference Pipeline (Online)

6. **Serve** (`serve/`)
   - **Input**: TorchScript model + inference requests
   - **Process**:
     - Image decoding (base64)
     - Preprocessing (resize, normalize)
     - Model inference
     - Geolocation verification (optional)
   - **Output**: JSON response with label, confidence, latency

7. **Dashboard** (`dashboard/`)
   - **Input**: User uploads (images)
   - **Process**: HTTP requests to Serve API
   - **Output**: Visual results display

## Technology Stack

### Core ML
- **PyTorch 2.3**: Training and inference framework
- **Torchvision**: Pretrained models (MobileNetV3, EfficientNet)
- **OpenCV**: Face detection and image processing
- **NumPy**: Numerical operations

### Services
- **FastAPI**: REST API for inference
- **Streamlit**: Interactive dashboard
- **Uvicorn**: ASGI server for FastAPI
- **Docker & Docker Compose**: Containerization

### Development & Testing
- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **ruff**: Linting (replaces flake8, isort)
- **mypy**: Type checking (optional)
- **k6**: Load testing

### Optional
- **Weights & Biases (W&B)**: Experiment tracking
- **DVC**: Data version control
- **Google Geolocation API**: High-accuracy geolocation

## Deployment Architecture

### Local Development
- All services run via `docker-compose.yml`
- Shared volumes for data persistence
- Hot-reload for development

### Cloud Deployment (GCP)
- **Cloud Run**: Serve API deployment
- **Cloud Storage (GCS)**: Artifact storage (models, data)
- **Firestore**: Persistent storage for professors, students, classes, enrollments, and check-ins
- **Service Account**: Secure credential management
- **Configuration**:
  - Project: `ac215-475022`
  - Region: `us-central1`
  - Bucket: `ac215-475022-assets`

## File Storage Layout

```
AC215-HARV/
├── data/
│   ├── raw/              # Raw images (gitignored)
│   ├── interim/          # Ingestion output (gitignored)
│   │   └── manifest.csv
│   ├── processed/        # Train/val/test splits (gitignored)
│   │   ├── train/
│   │   ├── val/
│   │   └── test/
│   └── sample_input/     # Tiny sample for quickstart
│
├── artifacts/
│   ├── checkpoints/      # Training checkpoints (gitignored)
│   │   └── best_model.pth
│   ├── model/            # Exported models (gitignored)
│   │   ├── model.torchscript.pt
│   │   └── metadata.json
│   ├── config/           # Runtime configuration (gitignored)
│   │   └── calibration.json
│   ├── geo/              # Geolocation logs (gitignored)
│   │   └── verify_log.jsonl
│   ├── metrics.json      # Evaluation metrics (gitignored)
│   └── samples/          # Sample API responses (gitignored)
│
├── outputs/              # Logs and sample outputs (gitignored)
│   ├── logs/
│   └── samples/
│
└── evidence/             # Testing evidence (gitignored)
    ├── coverage/
    ├── e2e/
    ├── load/
    └── logs/
```

## Security Considerations

1. **API Keys**: Stored in `.env`, never committed
2. **Service Account**: `service-account.json` gitignored
3. **Geolocation Privacy**: IP addresses logged in verification logs (GDPR compliance required)
4. **Model Access**: TorchScript models are public (no sensitive data in weights)

## Scalability Notes

### Current Limitations
- CPU-only training (suitable for small datasets <10k images)
- Single-instance deployment (no horizontal scaling yet)
- Synchronous inference (no queueing)

### Future Improvements
- GPU support for faster training (CUDA)
- Model quantization for edge deployment
- Redis caching for repeated requests
- Kubernetes deployment for horizontal scaling
- Prometheus + Grafana monitoring

## Dependencies

See `requirements-local.txt` and component-specific `pyproject.toml` files for full dependency lists.

**Key Dependencies**:
- `torch==2.3.0`
- `torchvision==0.18.0`
- `fastapi==0.110.0`
- `streamlit==1.32.0`
- `opencv-python==4.9.0`
- `pillow==10.2.0`
- `pyyaml==6.0.1`
