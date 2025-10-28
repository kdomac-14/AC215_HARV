# HARV - GCP Quick Start Guide

## TL;DR - Deploy in 3 Commands

```bash
# 1. Setup service account
make gcp-setup

# 2. Train model locally (if not done)
make run

# 3. Deploy to Cloud Run
make gcp-full-deploy
```

## Configuration Constants

```bash
PROJECT_NAME=HARV
PROJECT_ID=ac215-475022
REGION=us-central1
GCS_BUCKET=ac215-475022-assets
CLOUD_RUN_SERVICE=harv-backend
SERVICE_ACCOUNT=harv-service
```

## Environment Setup

### 1. Create `.env` file

```bash
cp .env.example .env
```

### 2. Add required variables to `.env`

```env
# Google API (for geolocation)
GOOGLE_API_KEY=your_actual_api_key_here

# GCP Configuration
PROJECT_ID=ac215-475022
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json

# Will be filled after deployment
API_URL=
```

## Deployment Workflow

### First Time Setup

```bash
# 1. Install gcloud CLI (if not installed)
brew install google-cloud-sdk

# 2. Authenticate with GCP
gcloud auth login

# 3. Set up service account and download credentials
make gcp-setup
```

### Deploy Backend

```bash
# Option A: Full deployment (uploads artifacts + deploys)
make gcp-full-deploy

# Option B: Step by step
make gcp-upload-artifacts  # Upload model to GCS
make gcp-deploy           # Deploy to Cloud Run
```

### After Deployment

1. Copy the service URL from deployment output
2. Update `.env`:
   ```env
   API_URL=https://harv-backend-xxxxx-uc.a.run.app
   ```

## Testing Deployment

```bash
# Set your service URL
export API_URL="https://harv-backend-xxxxx-uc.a.run.app"

# Health check
curl $API_URL/healthz

# Geo calibration (Harvard coordinates)
curl -X POST $API_URL/geo/calibrate \
  -H "Content-Type: application/json" \
  -d '{"lat": 42.3736, "lon": -71.1097, "epsilon_m": 60}'

# Check geo status
curl $API_URL/geo/status

# Test geo verification (will use IP geolocation)
curl -X POST $API_URL/geo/verify \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Local Development

```bash
# Run complete pipeline locally
make run

# Services will be available at:
# API: http://localhost:8000
# Dashboard: http://localhost:8501
```

## Makefile Targets

### Local Development
- `make run` - Build and run full pipeline + API + dashboard
- `make down` - Stop all containers
- `make logs` - View container logs
- `make clean` - Remove artifacts and data
- `make test` - Run all tests

### GCP Deployment
- `make gcp-setup` - Setup service account and credentials
- `make gcp-upload-artifacts` - Upload artifacts to GCS
- `make gcp-deploy` - Deploy backend to Cloud Run
- `make gcp-full-deploy` - Upload + deploy in one command

## Troubleshooting

### "gcloud: command not found"
```bash
brew install google-cloud-sdk
# Then restart terminal
```

### "Permission denied" errors
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

### "Service account already exists"
- This is normal, the script will reuse existing account
- If you need new credentials, delete old keys in GCP Console

### "Insufficient permissions"
Ensure you have these roles in GCP project:
- Cloud Run Admin
- Service Account User
- Storage Admin
- Cloud Build Editor

### Model not loading in Cloud Run
```bash
# Verify artifacts are uploaded
gsutil ls -r gs://ac215-475022-assets/artifacts/

# Check Cloud Run logs
gcloud run services logs read harv-backend \
  --project=ac215-475022 \
  --region=us-central1 \
  --limit=20
```

## File Structure

```
AC215-HARV/
├── .env                           # Environment variables (create from .env.example)
├── service-account.json          # GCP credentials (created by gcp-setup)
├── DEPLOYMENT.md                 # Detailed deployment guide
├── GCP_QUICK_START.md           # This file
├── Makefile                      # One-command orchestration
├── docker-compose.yml            # Local development
├── serve/
│   ├── Dockerfile               # Local development
│   ├── Dockerfile.cloudrun      # Production Cloud Run
│   └── src/
│       └── app.py               # FastAPI application
└── scripts/
    ├── setup_gcp.sh             # Service account setup
    ├── deploy_to_gcp.sh         # Cloud Run deployment
    └── upload_artifacts.sh      # Upload to GCS
```

## Key Differences: Local vs Production

| Feature | Local (Docker Compose) | Production (Cloud Run) |
|---------|------------------------|------------------------|
| Container | `serve/Dockerfile` | `serve/Dockerfile.cloudrun` |
| Port | 8000 (fixed) | $PORT (dynamic) |
| Artifacts | `./artifacts` volume | GCS bucket |
| Scaling | Single container | Auto-scales 0-1000 |
| Cost | Free (local) | Pay per request |
| URL | localhost:8000 | *.run.app domain |

## Security Notes

⚠️ **Never commit these files:**
- `.env` (contains API keys)
- `service-account.json` (GCP credentials)

✅ **Safe to commit:**
- `.env.example` (template)
- `DEPLOYMENT.md` (documentation)
- `scripts/*.sh` (deployment scripts)

## Next Steps After Deployment

1. ✅ Test all API endpoints
2. ✅ Update frontend with new API_URL
3. ✅ Configure custom domain (optional)
4. ✅ Set up monitoring/alerts
5. ✅ Implement CI/CD pipeline
6. ✅ Add authentication for production

## Cost Estimates

**Cloud Run** (with 2 vCPU, 2GB memory):
- Idle: $0/month (scales to zero)
- 1000 requests/day: ~$0.50/month
- 10,000 requests/day: ~$5/month

**Cloud Storage**:
- ~100MB artifacts: ~$0.02/month

**Total estimated cost**: ~$0.50-5/month for light usage

## Support

- Full documentation: `DEPLOYMENT.md`
- Issues: Check Cloud Run logs
- Questions: Review [Cloud Run docs](https://cloud.google.com/run/docs)
