# HARV Application Design

## A. Solution Architecture

### End-to-End Flow
1. **Ingestion → Preprocess**  
   DVC stages (`dvc.yaml`) pull raw classroom captures into `data/raw/`, clean them, and export curated tensors into `data/interim/` and `data/processed/vision/train|val`.
2. **Train → Evaluate → Export**  
   `ml/train_cnn.py --config ml/configs/harv_vision_v1.yaml` fine-tunes the MobileNet fallback, logs metrics under `artifacts/metrics/`, and writes weights + metadata into `models/harv_cnn_v1/`. The export stage copies bundles into `artifacts/model/` for container builds.
3. **Serve (FastAPI)**  
   The backend loads metadata via `backend/ml/model_loader.py`, keeps a SQLite DB (`backend/harv.db`) for courses + attendance events, and exposes `/health`, `/api/checkin/*`, and `/api/instructor/*`.
4. **Frontend (Expo Router)**  
   Students and professors run the Expo app (`frontend/app/*`). Students submit GPS coordinates first, fall back to the camera-based vision endpoint if required, and instructors review overrides.

### Text Architecture Diagram
```
data/raw ──▶ ingestion/src ──▶ data/interim ──▶ preprocess/src ──▶ data/processed
                                                          │
                                                          ▼
                           ml/train_cnn.py + configs ──▶ models/harv_cnn_v1
                                                          │
                                     artifacts/metrics ◀──┘
                                                          │
                                               backend/ml/model_loader
                                                          │
Student App ──GPS──▶ /api/checkin/gps ──┐
        │                               │
        └─camera(base64)──▶ /api/checkin/vision ──▶ Attendance DB ──▶ /api/instructor/*
                                                                           │
                                                  Professor App ◀──────────┘
```

### GPS-First Attendance
1. Student selects a course in the Expo Student tab (`frontend/app/student/*`).
2. Device GPS or manual coordinates are sent to `POST /api/checkin/gps` with student/course/instructor IDs.
3. `backend/app/services/gps.py` validates the coordinate against the configured Harvard bounding box (`settings.lecture_hall_bounds`). If **inside**, the event is marked `present`; if **near**, the response sets `requires_visual_verification=true`.

### Vision Fallback
1. When GPS is inconclusive, the Expo camera captures a frame and base64-encodes it.
2. `POST /api/checkin/vision` decodes the payload, feeds it through the MobileNet loader, and stores a second event with a confidence score.
3. Events with confidence below the threshold keep `requires_manual_review=True`, enabling professors to make the final call.

### Instructor Oversight
1. Professor tab calls `GET /api/instructor/courses` (filtered by instructor_id).
2. Selecting a course fetches attendance rows via `GET /api/instructor/attendance`.
3. Every record can be overridden with `POST /api/instructor/attendance/{event_id}/override`, which clears manual-review flags and stores instructor notes. The Expo view updates immediately with the returned payload.

## B. Technical Architecture

| Layer | Technologies | Rationale |
| --- | --- | --- |
| **Backend / API** | FastAPI, SQLModel, SQLite, Pydantic v2 | Declarative schemas give automatic docs + type checking, while SQLite keeps onboarding simple yet can be swapped for Postgres. |
| **Frontend** | React Native (Expo Router), Zustand store, Expo camera + location APIs, ESLint flat config | Expo delivers cross-platform GPS + camera access with one JavaScript bundle. Strict linting ensures the student/professor flows stay stable. |
| **ML Stack** | PyTorch 2.x, TorchVision, config-driven MobileNet fine-tuning, deterministic synthetic dataset fallback | Allows reproducible experimentation on CPUs while still supporting future GPU/cloud runs. Config files capture hyperparameters for auditability. |
| **DevOps / Tooling** | DVC, Docker Compose, GitHub Actions, pytest/coverage, Ruff/Black, ESLint | DVC guarantees data lineage, CI enforces ≥50% backend coverage, and Compose can orchestrate ingestion through serve for one-command demos. |

**Local reproducibility.** The repo pins Python 3.11 + Node 20, stores hyperparameters in YAML, and seeds RNGs inside training/testing utilities so results are deterministic on laptops.  
**Single-machine deployment.** `uvicorn backend.app.main:app` + `expo start` already deliver the Milestone 4 experience; Docker Compose wraps the same services for a one-shot `make run`.  
**Future cloud-readiness.** FastAPI + SQLite can be migrated to Postgres with minimal changes, the MobileNet weights can be exported to TorchScript/ONNX, and GitHub Actions artifacts show everything needed for a Milestone 5 container release.

## C. Code Organization Summary

| Path | Purpose |
| --- | --- |
| `backend/app/` | FastAPI routers (`api/routes`), SQLModel schemas (`models`), repositories/services, and database/session helpers. `main.py` wires routes + health checks. |
| `backend/ml/` | Lightweight `VisionModel` loader referenced by the API along with deterministic scoring logic for tests. |
| `backend/tests/` | Pytest suite split into `unit/` (GPS fence, repositories, ML loader) and `integration/` (FastAPI endpoints via TestClient). Coverage artifacts emit to `evidence/coverage/`. |
| `frontend/app/` | Expo Router screens for student + professor modes, camera/GPS workflows, and navigation layout. |
| `frontend/src/` & `frontend/utils/` | Reusable RN components, Zustand store, constants, and the API client that honors `EXPO_PUBLIC_API_URL`. |
| `ml/` | Config-driven training entrypoint, YAML configs, and helper scripts leveraged by the DVC pipeline. |
| `models/harv_cnn_v1/` | Versioned MobileNet weights + metadata consumed by `VisionModel`. |
| `artifacts/metrics/` | JSON metrics exported from the latest training/evaluation runs; attached to CI evidence. |
| `data/` | DVC-tracked datasets (`raw/`, `interim/`, `processed/`). The preprocessing stage emits the exact folders referenced by `ml/train_cnn.py`. |
| `docs/` | Architecture, runbooks, CI evidence, data versioning, and Milestone-4 verification checklist. |
| `.github/workflows/ci.yml` | Enforces lint + backend/frontend tests on push/PR, uploading coverage artifacts for grading. |
