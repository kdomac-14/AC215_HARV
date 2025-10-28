# Repository Inventory - Pre-Cleanup

Created: 2025-10-28
Branch: docs-and-cleanup/m2-feedback-remediation

## Current Top-Level Structure

```
AC215-HARV/
├── README.md (21KB - comprehensive but needs reorganization)
├── Makefile (2.9KB - has most workflows)
├── pytest.ini (620B)
├── docker-compose.yml
├── params.yaml (ML hyperparameters)
├── dvc.yaml
├── .env, .env.example
├── .gitignore (needs tightening)
│
├── Markdown Documentation (scattered, needs consolidation)
│   ├── DEPLOYMENT.md
│   ├── EVIDENCE.md
│   ├── FACE_RECOGNITION_SETUP.md
│   ├── GCP_QUICK_START.md
│   ├── GOOGLE_API_SETUP_SUMMARY.md
│   ├── IMPLEMENTATION_COMPLETE.md
│   ├── MILESTONE2_SUBMISSION_CHECKLIST.md
│   ├── REFACTOR_SUMMARY.md
│   ├── SETUP_DEPENDENCIES.md
│   ├── TESTING_FIXES_APPLIED.md
│   ├── TESTING_QUICKSTART.md
│   └── .testing-infrastructure-summary.md
│
├── docs/ (sparse, needs expansion)
│   ├── env_setup.md (1B - empty)
│   ├── google_geolocation_setup.md (5.8KB)
│   ├── gps_location_guide.md (7.9KB)
│   ├── pipeline.md (1B - empty)
│   ├── rag.md (1B - empty)
│   └── testing.md (10.9KB)
│
├── Pipeline Components (Dockerized)
│   ├── ingestion/ (Dockerfile + pyproject.toml + src/ingest.py)
│   ├── preprocess/ (Dockerfile + pyproject.toml + src/preprocess.py)
│   ├── train/ (Dockerfile + pyproject.toml + src/train.py)
│   ├── evaluate/ (Dockerfile + pyproject.toml + src/)
│   ├── export/ (Dockerfile + pyproject.toml + src/)
│   ├── serve/ (FastAPI service)
│   └── dashboard/ (Streamlit UI)
│
├── tests/ (comprehensive)
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── load/
│
├── data/
├── artifacts/
├── evidence/ (gitignored)
├── infra/
├── scripts/
└── services/

## Artifacts to Clean/Archive

### Python Cache (__pycache__)
- serve/src/__pycache__/
- tests/__pycache__/
- tests/e2e/__pycache__/
- tests/integration/__pycache__/
- tests/unit/__pycache__/

### Log Files
- evidence/logs/dashboard.log
- evidence/logs/serve.log

### Build Artifacts
- .DS_Store (top-level)
- .coverage (53KB)
- .pytest_cache/
- milestone2_evidence_20251013_165253.tar.gz (11.6MB)

### Cruft/Typos
- Madefile (1B - typo for Makefile)

## Components with Missing Documentation

### Missing README.md
- ingestion/ (needs README explaining purpose, CLI, I/O)
- preprocess/ (needs README explaining purpose, CLI, I/O)
- train/ (needs README explaining purpose, CLI, I/O)

### Missing Docstrings/Type Hints
- ingestion/src/ingest.py (no module docstring, no type hints)
- preprocess/src/preprocess.py (some function docs, no type hints)
- train/src/train.py (no module docstring, no type hints)

## Documentation to Consolidate

### To Archive (historical/process docs)
- IMPLEMENTATION_COMPLETE.md
- REFACTOR_SUMMARY.md
- TESTING_FIXES_APPLIED.md
- MILESTONE2_SUBMISSION_CHECKLIST.md
- .testing-infrastructure-summary.md

### To Keep & Enhance
- README.md (reorganize, link to docs/)
- DEPLOYMENT.md (move to docs/ or keep at root with link)
- EVIDENCE.md (keep at root for graders)

### To Create in docs/
- ARCHITECTURE.md (system diagram, components, data flow)
- PIPELINE.md (detailed ingestion → preprocess → train flow)
- DECISIONS.md (MobileNetV3 justification, geolocation choices)
- TESTING.md (consolidate from existing testing.md + EVIDENCE.md)
- RUNBOOK.md (clean-clone instructions, troubleshooting)

## Current Strengths

✅ Comprehensive testing (unit, integration, e2e, load)
✅ Good Makefile with workflows
✅ Docker containerization working
✅ CI/CD with GitHub Actions
✅ Coverage reporting (50%+)
✅ Real face dataset integration

## Action Items (per plan)

0. ✅ Branch created: docs-and-cleanup/m2-feedback-remediation
1. [ ] Clean __pycache__, .DS_Store, old tarballs, logs
2. [ ] Create archive/ for historical docs
3. [ ] Tighten .gitignore
4. [ ] Standardize to src/ structure (already mostly there)
5. [ ] Create comprehensive docs/ (ARCHITECTURE, PIPELINE, DECISIONS, TESTING, RUNBOOK)
6. [ ] Add per-component READMEs
7. [ ] Add module docstrings + type hints + pyproject.toml config
8. [ ] Enhance Makefile
9. [ ] Add sample results
10. [ ] Verify all links and commands
