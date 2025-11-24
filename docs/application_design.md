# HARV Application Design

## Solution Architecture

| Component | Description |
| --- | --- |
| **Mobile (Expo) client** | React Native / Expo Router app in `frontend/` providing a student tab for GPS + vision check-ins and a professor tab for reviewing/overriding attendance. |
| **Backend API** | FastAPI service (see `backend/app`) exposing `/health`, `/api/checkin/*`, and `/api/instructor/*` routes. Persisted with SQLite/SQLModel. |
| **ML Service** | Lightweight MobileNet-based verifier packaged inside the backend (`backend/ml`). Model metadata lives in `models/harv_cnn_v1`. |
| **Database** | SQLite file (`backend/harv.db`) created automatically. Tables defined with SQLModel for courses + attendance events. |
| **Data & Artifacts** | `data/` is tracked by DVC stages (`dvc.yaml`). Model checkpoints go to `models/harv_cnn_v1` and metrics to `artifacts/metrics/`. |
| **Docs & CI** | Documentation under `docs/`. GitHub Actions workflow `.github/workflows/ci.yml` enforces lint/tests on every push. |

### Student Flow
1. Student selects a course inside the Expo client. The mobile app collects GPS coordinates (or allows manual entry).
2. The app calls `POST /api/checkin/gps` with student/course IDs and lat/lon.
3. Backend validates against the configured Harvard lecture hall bounding box. If location is inside, the event is marked `present`. If near-but-outside, the response includes `requires_visual_verification=true`.
4. When vision fallback is requested, the mobile app captures a photo, base64-encodes it, and calls `POST /api/checkin/vision`.
5. The backend loads the MobileNet weights via `backend/ml/model_loader.py`, runs inference, and stores the event with a confidence score.
6. Attendance entries can be reviewed in the professor dashboard.

### Instructor Flow
1. Instructor opens the professor tab in the Expo app which calls `GET /api/instructor/courses`.
2. Selecting a course fetches attendance entries via `GET /api/instructor/attendance?course_id=...`.
3. Entries that are `pending` or flagged can be overridden by tapping them, which issues `POST /api/instructor/attendance/{event_id}/override`.

### Data Flow Overview
```
Student App → FastAPI Check-in service → SQLite attendance table
     ↓                                       ↑
Vision fallback (MobileNet) ——→ stored confidence + method
     ↓
Professor App ←—— GET course + attendance feeds
```

## Technical Architecture

### Repository Layout
```
backend/
  app/           # FastAPI routers, models, services
  ml/            # Deterministic model loader used by API
  tests/         # pytest suite (unit + integration)
docs/
frontend/
  app/           # Expo route definitions
  src/           # Shared RN components/modules
  public/        # Static assets / placeholders
ml/
  configs/       # YAML configs for training
  train_cnn.py   # Vision fine-tuning entrypoint
models/
  harv_cnn_v1/   # Versioned model metadata + weights
.github/workflows/
  ci.yml         # GitHub Actions workflow
```

### Tech Stack Choices
- **API**: FastAPI + SQLModel for async-ready HTTP services with declarative models.
- **Database**: SQLite stored in `backend/harv.db` (auto-created). SQLModel enables easy migration to Postgres later.
- **Mobile**: Expo Router (React Native) for an easily demoable cross-platform client with camera + GPS.
- **ML**: PyTorch MobileNet fine-tuning script with deterministic fallback when data is missing.
- **Tooling**: DVC for data lineage, pytest + coverage for backend validation, ESLint/Prettier for React Native, Ruff/Black for Python.

### Container/Runtime Considerations
- Local development uses Python virtual environments + Expo CLI.
- Docker Compose from prior milestones can still wrap ingestion/training services if needed; however Milestone 4 emphasizes local developer experience, so `uvicorn`/`expo start` commands are the default.
- ML artifacts created via `ml/train_cnn.py --config ml/configs/harv_vision_v1.yaml` are stored on disk and referenced by the FastAPI loader.

### Module-Level Notes
- `backend/app`: Routers have inline docstrings describing `/checkin` vs `/instructor`. Services contain the GPS/vision orchestration logic.
- `backend/ml/model_loader.py`: No heavy GPU dependency; loads JSON metadata + weights, producing deterministic confidences for tests.
- `frontend/src/components`: Shared RN UI primitives (e.g., status pill) so Expo router files remain thin.
- `ml/train_cnn.py`: Documented pipeline that supports ImageFolder datasets, augmentation, metrics logging, and latency estimation.
