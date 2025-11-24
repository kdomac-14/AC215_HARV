## Continuous Integration Evidence

**Workflow:** `.github/workflows/ci.yml` (runs on every push + pull request to `main` and `develop`).  
**Environment pins:** Python 3.11, Node 20. Coverage gate enforced via `pytest.ini` (`--cov-fail-under=50`).

### Jobs
1. **`lint`**
   - Checks out the repo, installs Ruff + Black, and runs `ruff check backend ml` followed by `black --check backend ml`.
   - Keeps backend + ML scripts code-styled before running heavier jobs.
2. **`backend`**
   - Installs the project with extras via `pip install ".[dev]"`.
   - Executes `pytest` using the repo-level `pytest.ini` configuration which already includes coverage flags (term + HTML + XML outputs).
   - Uploads `evidence/coverage/` (HTML + XML) using `actions/upload-artifact`. Inspect `backend` job logs to verify the ≥50% coverage line.
3. **`frontend`**
   - Runs inside `frontend/`, executes `npm ci --no-audit --no-fund`, and finishes with `npm run lint` (Expo + ESLint flat config).

### Artifacts & Coverage
- Coverage report location: `evidence/coverage/html/index.html` and `evidence/coverage/coverage.xml`.
- Artifact name: `backend-coverage-${{ github.sha }}`. Downloading it yields the entire `evidence/coverage/` directory for grading.

### Evidence to Capture
- Attach a screenshot in Canvas (or the milestone submission) showing the GitHub Actions run with all jobs green.
- Expand the `backend` job log to the coverage summary lines; include that snippet or cite the artifact to demonstrate ≥50% coverage was enforced.
