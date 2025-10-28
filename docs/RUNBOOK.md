# HARV Runbook

Operational guide for running HARV from a clean clone to deployed system.

---

## Prerequisites

### Required Software

| Tool | Version | Check Command | Install |
|------|---------|---------------|---------|
| **Docker** | 24.0+ | `docker --version` | https://docs.docker.com/get-docker/ |
| **Docker Compose** | 2.0+ | `docker compose version` | Included with Docker Desktop |
| **Git** | 2.0+ | `git --version` | https://git-scm.com/downloads |

### Optional Tools

| Tool | Purpose | Install |
|------|---------|---------|
| **k6** | Load testing | `brew install k6` (Mac) / https://k6.io/docs/get-started/installation/ |
| **Python 3.11** | Local development | https://www.python.org/downloads/ |

### System Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 8GB minimum (4GB for Docker, 4GB for system)
- **Disk**: 10GB free space
- **OS**: macOS, Linux, or Windows with WSL2

---

## Clean Clone Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/kdomac-14/AC215_HLAV.git
cd AC215_HLAV
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env (optional)
nano .env
```

**Minimal `.env` (works out-of-box):**
```bash
WANDB_DISABLED=true
SERVICE_PORT=8000
DASH_PORT=8501
CHALLENGE_WORD=orchid
GEO_PROVIDER=mock
GEO_EPSILON_M=60
```

**Optional Enhancements:**
```bash
# For W&B experiment tracking
WANDB_API_KEY=your_key_here
WANDB_DISABLED=false

# For Google Geolocation API (higher accuracy)
GOOGLE_API_KEY=your_google_api_key
GEO_PROVIDER=google

# For GCP deployment
PROJECT_ID=ac215-475022
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
```

### Step 3: Verify Docker

```bash
# Check Docker is running
docker ps

# If not running, start Docker Desktop
# Mac: open -a Docker
# Linux: sudo systemctl start docker

# Test Docker Compose
docker compose version
```

---

## Running the System

### Option 1: Single Command (Recommended)

```bash
make run
```

**What this does:**
1. Builds all Docker images (~5-10 minutes first time)
2. Runs pipeline sequentially: ingestion → preprocess → train → evaluate → export
3. Starts serve and dashboard services
4. Keeps services running for testing

**Expected output:**
```
[+] Building complete (5 services)
[+] Running ingestion... done
[+] Running preprocess... done
[+] Running train... done
[+] Running evaluate... done
[+] Running export... done
[+] Starting serve... running
[+] Starting dashboard... running

Services ready:
- API: http://localhost:8000
- Dashboard: http://localhost:8501
```

**Expected runtime:**
- First run (with build): 15-20 minutes
- Subsequent runs: 2-3 minutes

### Option 2: Step-by-Step

**Build images:**
```bash
docker compose build
```

**Run pipeline components:**
```bash
docker compose run ingestion
docker compose run preprocess
docker compose run train
docker compose run evaluate
docker compose run export
```

**Start services:**
```bash
docker compose up serve dashboard
```

### Option 3: Development Mode

**Run single component:**
```bash
# Just train
docker compose run train

# Just serve (uses existing model)
docker compose up serve
```

**Rebuild single service:**
```bash
docker compose build train
docker compose run train
```

---

## Validating the System

### Health Checks

**API health:**
```bash
curl http://localhost:8000/healthz
```

Expected:
```json
{
  "ok": true,
  "model": "mobilenet_v3_small",
  "num_classes": 2,
  "classes": ["ProfA", "Room1"],
  "geo_provider": "mock"
}
```

**Dashboard:**
Open browser to http://localhost:8501

Expected: Streamlit interface with "Upload Image" button

### Test Inference

**Create test image:**
```bash
python3 -c "
import base64, numpy as np, cv2, json
img = 255 * np.ones((224, 224, 3), dtype=np.uint8)
_, buf = cv2.imencode('.jpg', img)
b64 = base64.b64encode(buf).decode()
payload = {'image_b64': b64, 'challenge_word': 'orchid'}
print(json.dumps(payload))
" > test_payload.json
```

**Send request:**
```bash
curl -X POST http://localhost:8000/verify \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

Expected:
```json
{
  "ok": true,
  "label": "ProfA",
  "confidence": 0.52,
  "latency_ms": 15
}
```

### Run Tests

**All tests:**
```bash
make test
```

Expected: All tests pass (unit, integration, e2e)

**Coverage report:**
```bash
make coverage
```

Expected: Opens HTML report showing ≥50% coverage

---

## Common Workflows

### Complete Verification (Grader Path)

```bash
# Complete build + test + evidence generation
make verify

# View results
open evidence/coverage/html/index.html
cat evidence/e2e/e2e_results.json
```

**Expected outcome:**
- ✅ All services build successfully
- ✅ All tests pass
- ✅ Coverage ≥50%
- ✅ Evidence archive created: `milestone2_evidence_*.tar.gz`

### Retraining with New Data

```bash
# 1. Add images to data/raw/
mkdir -p data/raw/ProfA data/raw/Room1
cp /path/to/your/images/*.jpg data/raw/ProfA/

# 2. Enable real data in params.yaml
sed -i '' 's/use_real_faces: false/use_real_faces: true/' params.yaml

# 3. Run pipeline
make run
```

### Changing Model

```bash
# Edit params.yaml
nano params.yaml

# Change model_name
# model_name: efficientnet_b0  # or mobilenet_v3_small

# Retrain
docker compose run train
docker compose run evaluate
docker compose run export

# Restart serve
docker compose restart serve
```

### Clean Restart

```bash
# Stop services and remove volumes
make down

# Remove artifacts
make clean

# Fresh run
make run
```

---

## Troubleshooting

### Issue: Port Already in Use

**Error:**
```
Error starting userland proxy: listen tcp4 0.0.0.0:8000: bind: address already in use
```

**Solution 1: Change ports in .env**
```bash
echo "SERVICE_PORT=8080" >> .env
echo "DASH_PORT=8502" >> .env
docker compose up serve dashboard
```

**Solution 2: Kill process on port**
```bash
# Find process
lsof -i :8000

# Kill it
kill -9 <PID>
```

### Issue: Docker Build Fails

**Error:**
```
failed to solve: process "/bin/sh -c pip install ..." did not complete successfully
```

**Solution:**
```bash
# Clear Docker cache
docker system prune -a

# Rebuild
docker compose build --no-cache
```

### Issue: CUDA Out of Memory

**Error:**
```
RuntimeError: CUDA out of memory. Tried to allocate X.XX GiB
```

**Solution:**
```bash
# Reduce batch size in params.yaml
nano params.yaml
# Change: batch_size: 8  # or 4

# Rerun
docker compose run train
```

### Issue: Low Accuracy

**Symptom:** Model accuracy <50%

**Possible causes:**
1. Insufficient training data
2. Too few epochs
3. Wrong learning rate

**Solution:**
```bash
# Check params.yaml
cat params.yaml

# Increase epochs
# epochs: 10  # from 3

# Add more data to data/raw/

# Retrain
docker compose run train
```

### Issue: Services Not Ready

**Error:**
```
requests.exceptions.ConnectionError: ('Connection aborted.', RemoteDisconnected(...))
```

**Solution:**
```bash
# Wait for services to start
bash scripts/wait_for_services.sh

# Or manually check logs
docker compose logs serve | grep "Application startup complete"
```

### Issue: Test Failures

**Error:**
```
AssertionError: assert 0.45 > 0.50
```

**Solution:**
```bash
# Check if pipeline completed successfully
ls artifacts/model/model.torchscript.pt

# Check metrics
cat artifacts/metrics.json

# If model missing, run pipeline first
make run

# Then rerun tests
make test
```

### Issue: Permission Denied (Linux)

**Error:**
```
Got permission denied while trying to connect to the Docker daemon socket
```

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or:
newgrp docker

# Test
docker ps
```

### Issue: Disk Space Full

**Error:**
```
OSError: [Errno 28] No space left on device
```

**Solution:**
```bash
# Check disk space
df -h

# Clean Docker artifacts
docker system prune -a --volumes

# Remove old evidence
rm -rf evidence/*.tar.gz

# Clean Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
```

---

## Performance Tuning

### Faster Training (CPU)

```yaml
# params.yaml
batch_size: 32      # Increase (if RAM allows)
epochs: 3           # Keep minimal for testing
freeze_ratio: 0.8   # Freeze more layers
```

### Smaller Model Size

```yaml
# params.yaml
model_name: mobilenet_v3_small  # Smaller than efficientnet_b0
```

### Faster Inference

```bash
# Use smaller batch size for dashboard
# dashboard/app/app.py
# Reduce timeout in API calls
```

---

## Deployment

### Deploy to GCP Cloud Run

```bash
# 1. Setup GCP credentials
make gcp-setup

# 2. Deploy
make gcp-full-deploy

# Expected output:
# Service URL: https://harv-backend-xyz-uc.a.run.app
```

See `DEPLOYMENT.md` for detailed deployment guide.

### Environment Variables for Production

```bash
# .env (production)
WANDB_DISABLED=true
GEO_PROVIDER=google
GOOGLE_API_KEY=your_production_key
GEO_EPSILON_M=60
PROJECT_ID=ac215-475022
```

---

## Monitoring

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f serve
docker compose logs -f train

# Last 100 lines
docker compose logs --tail=100 serve
```

### Check Artifacts

```bash
# Model exists
ls -lh artifacts/model/model.torchscript.pt

# Metrics
cat artifacts/metrics.json | jq .

# Checkpoints
ls -lh artifacts/checkpoints/
```

### Resource Usage

```bash
# Docker stats
docker stats

# Disk usage
docker system df
```

---

## Cleanup

### Stop Services

```bash
# Stop but keep containers
docker compose stop

# Stop and remove containers
docker compose down

# Stop and remove volumes
docker compose down -v
```

### Remove Artifacts

```bash
# Clean generated files
make clean

# Removes:
# - artifacts/
# - data/processed/
# - data/interim/
# - evidence/
```

### Complete Reset

```bash
# Remove everything
docker compose down -v
docker system prune -a
make clean

# Fresh start
make run
```

---

## Development Tips

### Hot Reload for Serve

```bash
# Edit serve/src/app.py
# Restart only serve service
docker compose restart serve
```

### Local Python Environment

```bash
# For IDE development (no Docker)
cd train/
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Run locally
python -m src.train
```

### Debugging

```bash
# Interactive shell in container
docker compose run --rm train /bin/bash

# Check environment
docker compose run --rm train env

# Test script
docker compose run --rm train python -c "import torch; print(torch.__version__)"
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `make run` | Build + run full pipeline + start services |
| `make test` | Run all tests |
| `make verify` | Complete verification (build + test + evidence) |
| `make coverage` | Generate and view coverage report |
| `make down` | Stop services and remove containers |
| `make clean` | Remove artifacts and generated data |
| `make logs` | Follow logs from all services |
| `make evidence` | Export evidence for submission |
| `docker compose build` | Build all images |
| `docker compose up serve` | Start only serve service |
| `docker compose logs -f train` | View train logs |
| `docker compose run train` | Run train component once |

---

## Next Steps

After successful setup:

1. **Test API**: `curl http://localhost:8000/healthz`
2. **Test Dashboard**: Open http://localhost:8501
3. **Run Tests**: `make test`
4. **Generate Evidence**: `make evidence`
5. **Deploy (optional)**: `make gcp-full-deploy`

For detailed component docs, see:
- `docs/PIPELINE.md` - Pipeline details
- `docs/ARCHITECTURE.md` - System architecture
- `docs/DECISIONS.md` - Design rationale
- `docs/testing.md` - Testing guide
