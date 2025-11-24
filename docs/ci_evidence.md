## Continuous Integration Evidence

- Workflow file: `.github/workflows/ci.yml`
- Jobs:
  - `lint` runs Ruff + Black to keep backend/ml Python tidy.
  - `backend` installs the package via `pip install ".[dev]"`, runs `pytest` with coverage, and uploads the HTML + XML report from `evidence/coverage`.
  - `frontend` installs Expo dependencies on Node 20 and runs `npm run lint`.
- Screenshot to capture: GitHub Actions run showing all three jobs green with the coverage artifact attached (expand the run for the `backend` job so the coverage percentage is visible in the logs).
