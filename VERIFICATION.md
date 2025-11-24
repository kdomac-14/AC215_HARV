# Milestone 4 Verification Checklist

The following checklist ties directly to the AC215 Milestone 4 rubric. Each item references the repository artifact that proves completion.

## 1. Application Design & Architecture
- [x] `docs/application_design.md` captures the ingestion → preprocess → train → evaluate → export → serve → Expo flow and includes an ASCII component diagram.
- [x] README “Repository Map” + linked docs summarize the backend, frontend, ML, and data directories.
- [x] Architecture decisions (GPS-first, MobileNet fallback, SQLite persistence) are documented alongside their trade-offs.

## 2. Backend APIs & Services
- [x] FastAPI entry point (`backend/app/main.py`) wires `/health`, `/api/checkin/*`, and `/api/instructor/*`.
- [x] `/health` returns `{ok, app, version, lecture_hall_bounds, demo_courses}` for smoke testing.
- [x] Student endpoints: `/api/checkin/gps` + `/api/checkin/vision` validate payloads, hit services, and persist via `AttendanceRepository`.
- [x] Instructor endpoints: `/api/instructor/courses`, `/api/instructor/attendance`, `/api/instructor/attendance/{event_id}/override` power professor UI flows.
- [x] Request/response models live under `backend/app/schemas/*` with inline docstrings to keep API docs accurate.

## 3. Frontend Integration
- [x] Expo Router screens (`frontend/app/student/*`, `frontend/app/professor/*`) call the backend through `frontend/utils/api.ts`.
- [x] Student Mode enforces a GPS-first workflow with optional manual coords plus Camera fallback for `/api/checkin/vision`.
- [x] Professor Mode lists instructor courses, displays attendance events, and issues overrides (status toggle before tap).
- [x] API base URL configurable via `EXPO_PUBLIC_API_URL` (see `frontend/.env.example` instructions in README).

## 4. CI, Testing, and Coverage
- [x] `pytest.ini` + `pyproject.toml` enforce `--cov-fail-under=50` with HTML/XML outputs saved to `evidence/coverage/`.
- [x] Backend tests: unit coverage for GPS/vision/repository plus integration coverage via FastAPI `TestClient`.
- [x] GitHub Actions (`.github/workflows/ci.yml`) runs Ruff/Black, pytest (with artifacts), and Expo lint on every push/PR.
- [x] README + `docs/ci_evidence.md` explain how to capture proof (screenshot of green workflow + coverage logs).
- [x] `TESTING_QUICKSTART.md` documents local pytest + Expo lint commands for teammates.

## 5. Data Versioning & Reproducibility
- [x] `dvc.yaml` declares ingestion → preprocess → train → evaluate → export stages with dependencies/outs that match repo layout.
- [x] `docs/data_versioning.md` explains how to `dvc pull`, re-run the pipeline, and manage DVC remotes/artifacts.
- [x] `params.yaml` + `ml/configs/harv_vision_v1.yaml` store hyperparameters; README references them in the ML pipeline section.
- [x] Synthetic dataset fallback described for CI-only runs; collaborators know where to store LLM/synthetic prompts if introduced.

## 6. Model Training / Fine-Tuning
- [x] `ml/train_cnn.py` loads YAML config, seeds RNGs, logs metrics, exports weights, and benchmarks latency.
- [x] Metrics + metadata live under `artifacts/metrics/harv_cnn_v1.json` and `models/harv_cnn_v1/metadata.json`.
- [x] `docs/model_training_summary.md` records architecture rationale, config snapshot, metrics, and deployment implications.

## 7. Deployment Readiness (Local)
- [x] `README.md` includes backend/front-end setup instructions, environment prerequisites, and a “Full E2E Test (Local)” walkthrough.
- [x] `docker-compose.yml` + `Makefile` still orchestrate ingestion → serve for one-command demos (`make run`).
- [x] `.env` / `frontend/.env` patterns documented; no secrets committed beyond placeholders/dummy keys.

## 8. Evidence & Submission Artifacts
- [x] `docs/ci_evidence.md` enumerates jobs, coverage artifacts, and screenshot expectations.
- [x] `docs/application_design.md`, `docs/data_versioning.md`, and `docs/model_training_summary.md` are linked from README for graders.
- [x] This checklist (`VERIFICATION.md`) lives at the repo root so graders can confirm Milestone 4 completion quickly.

### Suggested Verification Steps
1. `python -m venv .venv && source .venv/bin/activate && pip install ".[dev]"`.
2. `pytest` (expects coverage ≥ 50% and reports saved under `evidence/coverage/`).
3. `cd frontend && npm install && npm run lint`.
4. Start backend (`uvicorn backend.app.main:app --reload --port 8000`) and Expo client (`npm run start`), then walk through the README “Full E2E Test (Local)” scenario.
