# HARV – Harvard Lecture Attendance Verifier

HARV validates lecture attendance with a GPS-first workflow and a MobileNet vision fallback. Students use the Expo mobile app to check in; instructors review/override entries via the same client. The FastAPI backend stores attendance events and exposes course feeds for dashboards. All ML + data assets are tracked for Milestone 4 reproducibility.

![Architecture](docs/application_design.md)

## Repository Map
```
backend/                 FastAPI app (routers, services, SQLModel models)
  ml/                    Vision model loader consumed by the API
  tests/                 pytest suite (unit + integration)
frontend/                Expo Router mobile client (student + professor tabs)
  app/                   Screens wired to Expo router
  src/                   Shared RN components/utilities
  public/                Static placeholders
ml/                      Training configs + scripts for MobileNet fallback
models/harv_cnn_v1/      Versioned model weights + metadata
artifacts/metrics/       JSON metrics exported from training
.github/workflows/ci.yml GitHub Actions (lint, backend tests, frontend lint)
docs/                    Architecture, runbooks, CI evidence, etc.
```

## Prerequisites
| Tool | Version | Notes |
| --- | --- | --- |
| Python | 3.11 | `pyenv` or Conda recommended |
| Node.js | 20.x | Required for Expo CLI + ESLint |
| npm | 10.x | Installed with Node |
| DVC | 3.x | Optional but recommended for pulling data snapshots |

## Backend Setup
1. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install ".[dev]"
   ```
2. Start the API:
   ```bash
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Binding to `0.0.0.0` exposes the service to simulators and physical devices running the Expo client on the same network.
3. Copy `.env.example` → `.env` if you need to override defaults. SQLite database (`backend/harv.db`) is created automatically along with demo courses.

### Key Endpoints
- `GET /health` – status + configured lecture hall bounds.
- `POST /api/checkin/gps` – student_id, course_id, instructor_id, latitude, longitude.
- `POST /api/checkin/vision` – fallback with `image_b64`.
- `GET /api/instructor/courses?instructor_id=...`
- `GET /api/instructor/attendance?course_id=...`
- `POST /api/instructor/attendance/{event_id}/override`

## Frontend (Expo) Setup
```bash
cd frontend
npm install
npm run lint     # optional sanity check
npm run start    # launches Expo DevTools
```
The mobile client automatically points to the dev machine that served the Expo bundle (Android emulators fall back to `http://10.0.2.2:8000`). If you host the API somewhere else, set `EXPO_PUBLIC_API_URL` in `frontend/.env` before starting Expo. Use the Expo Go app or iOS Simulator to open the project.

### Student Demo Flow
1. Launch Expo app → “Student Mode”.
2. Enter a student ID (any string).
3. Tap a course (e.g., “CS50 – Computer Science”).
4. Press “Send GPS Check” using either the live GPS coordinate or the editable fields.
5. If the backend responds with `requires_visual_verification`, grant camera access and upload a scan via “Upload Vision Scan”.
6. Observe success/failure message and return to the course list.

### Instructor Demo Flow
1. “Professor Mode” lists seeded courses (`settings.default_courses`).
2. Tap a course to load attendance events.
3. Use the override toggle (Present/Absent) then tap a record to call the override endpoint.

## Testing & Quality Gates
### Backend
```bash
pytest
```
This runs unit + integration tests (FastAPI TestClient) with coverage saved under `evidence/coverage/`.

### Frontend
```bash
cd frontend
npm run lint
```
Expo Router currently uses the ESLint config in `frontend/.eslintrc.js`. Node 20 is required (local Node 14 will fail).

## ML Training Pipeline
1. (Optional) Pull/prepare datasets with DVC:
   ```bash
   dvc pull data/interim data/processed
   ```
2. Run the MobileNet fine-tuning script:
   ```bash
   python ml/train_cnn.py --config ml/configs/harv_vision_v1.yaml
   ```
   - Synthetic samples kick in automatically if `data/processed/vision/*` is empty.
   - Outputs: `models/harv_cnn_v1/weights.pt`, updated `metadata.json`, and metrics at `artifacts/metrics/harv_cnn_v1.json`.
3. Update `docs/model_results.md` with new metrics.

## Full E2E Test (Local)
1. `uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000`
2. `cd frontend && npm run start`
3. Open Expo app → Student Mode → send GPS/vision check.
4. Confirm entry in Expo → Professor Mode (attendance list updates automatically because SQLite is shared).
5. Optionally hit API via curl:
   ```bash
   curl -X POST http://localhost:8000/api/instructor/attendance/1/override \
     -H "Content-Type: application/json" \
     -d '{"status": "present", "notes": "verified in lab"}'
   ```

## CI / CD
- GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push/PR:
  1. `lint` job → Ruff + Black.
  2. `backend` job → pytest + coverage artifact.
  3. `frontend` job → `npm ci` + ESLint.
- Capture a screenshot of the Actions run with all jobs green and coverage summary for Milestone evidence (see `docs/ci_evidence.md`).

## Additional Documentation
- [Application design](docs/application_design.md)
- [Data versioning strategy](docs/data_versioning.md)
- [Model results](docs/model_results.md)
- [Model training summary](docs/model_training_summary.md)
- [Runbook / troubleshooting](docs/RUNBOOK.md`, `docs/MOBILE_APP.md`)
