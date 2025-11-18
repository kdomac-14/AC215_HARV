# HARV - Deployment Guide

## Google Cloud Platform (GCP) Deployment

This guide covers deploying HARV (Harvard Attendance Recognition and Verification) to Google Cloud Platform using Cloud Run.

### GCP Configuration

- **Project ID**: `ac215-475022`
- **Region**: `us-central1`
- **GCS Bucket**: `ac215-475022-assets`
- **Cloud Run Service**: `harv-backend`
- **Service Account**: `harv-service`

## Prerequisites

1. **Google Cloud SDK**: Install gcloud CLI
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Docker**: Required for building images
   ```bash
   docker --version  # Should be 24.0+
   ```

3. **GCP Account**: Ensure you have access to project `ac215-475022`

## Deployment Steps

### 1. Setup GCP Service Account

This creates the service account and downloads credentials to `./service-account.json`:

```bash
make gcp-setup
```

Or manually:
```bash
bash scripts/setup_gcp.sh
```

**What this does:**
- Creates service account `harv-service@ac215-475022.iam.gserviceaccount.com`
- Grants necessary IAM permissions (Storage, AI Platform, Cloud Run)
- Downloads service account key to `./service-account.json`

### 2. Update Environment Variables

Edit your `.env` file (or create from `.env.example`):

```bash
cp .env.example .env
```

Add these variables:
```env
# GCP Configuration
PROJECT_ID=ac215-475022
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
API_URL=  # Will be filled after deployment

# Required for geolocation
GOOGLE_API_KEY=your_google_api_key_here
```

### 3. Train Model Locally (if needed)

Before deploying, ensure you have trained artifacts:

```bash
make run
```

This will:
- Run the full ML pipeline (ingestion → preprocess → train → evaluate → export)
- Generate model artifacts in `./artifacts/`
- Start local API server for testing

### 4. Upload Artifacts to GCS

Upload trained model and artifacts to Google Cloud Storage:

```bash
make gcp-upload-artifacts
```

Or manually:
```bash
bash scripts/upload_artifacts.sh
```

**What this does:**
- Syncs `./artifacts/` directory to `gs://ac215-475022-assets/artifacts/`
- Makes model available for Cloud Run deployment

### 5. Deploy to Cloud Run

Deploy the backend service:

```bash
make gcp-deploy
```

Or manually:
```bash
bash scripts/deploy_to_gcp.sh
```

**What this does:**
- Builds Docker image using `./serve/Dockerfile`
- Pushes to Google Container Registry (GCR)
- Deploys to Cloud Run with:
  - 2 vCPUs, 2GB memory
  - 300s timeout
  - Unauthenticated access (public API)
  - Auto-scaling enabled

**Deployment output:**
```
✅ Deployment Complete!
Service URL: https://harv-backend-xxxxx-uc.a.run.app
API Health Check: https://harv-backend-xxxxx-uc.a.run.app/healthz
```

### 6. Update .env with API URL

After deployment, update your `.env` file with the service URL:

```env
API_URL=https://harv-backend-xxxxx-uc.a.run.app
```

### 7. Test Deployment

Test the deployed API:

```bash
# Health check
curl https://harv-backend-xxxxx-uc.a.run.app/healthz

# Expected response:
# {"ok":true,"model":"mobilenet_v3_small","geo_provider":"GoogleGeoProvider"}
```

Test geo calibration:
```bash
curl -X POST https://harv-backend-xxxxx-uc.a.run.app/geo/calibrate \
  -H "Content-Type: application/json" \
  -d '{"lat": 42.3736, "lon": -71.1097, "epsilon_m": 60}'
```

## Full Deployment (One Command)

To upload artifacts and deploy in one step:

```bash
make gcp-full-deploy
```

This runs:
1. `make gcp-upload-artifacts` - Upload model to GCS
2. `make gcp-deploy` - Deploy to Cloud Run

## Deployment Architecture

```
┌─────────────────────────────────────────┐
│         User (Browser/Mobile)           │
└───────────────┬─────────────────────────┘
                │
                │ HTTPS
                ▼
┌─────────────────────────────────────────┐
│    Cloud Run Service (harv-backend)     │
│  ┌───────────────────────────────────┐  │
│  │   FastAPI Application             │  │
│  │   - /healthz (health check)       │  │
│  │   - /geo/calibrate (setup)        │  │
│  │   - /geo/verify (location auth)   │  │
│  │   - /verify (face recognition)    │  │
│  └───────────────────────────────────┘  │
└───────────────┬─────────────────────────┘
                │
                │ Reads model artifacts
                ▼
┌─────────────────────────────────────────┐
│   Google Cloud Storage (GCS)            │
│   gs://ac215-475022-assets/              │
│   └── artifacts/                         │
│       ├── model/                         │
│       │   ├── model.torchscript.pt       │
│       │   └── metadata.json              │
│       └── samples/                       │
└─────────────────────────────────────────┘
```

## Service Account Permissions

The `harv-service` service account has these roles:

- `roles/storage.objectViewer` - Read model artifacts from GCS
- `roles/aiplatform.user` - Access AI Platform services
- `roles/run.invoker` - Invoke Cloud Run services

## Environment Variables (Cloud Run)

Set during deployment:

```env
CHALLENGE_WORD=orchid
GEO_PROVIDER=google
GEO_EPSILON_M=60
PROJECT_ID=ac215-475022
```

## Monitoring & Logs

### View Logs

```bash
# Stream logs from Cloud Run
gcloud run services logs read harv-backend \
  --project=ac215-475022 \
  --region=us-central1 \
  --limit=50

# Or in Cloud Console:
# https://console.cloud.google.com/run/detail/us-central1/harv-backend/logs
```

### Monitor Performance

Cloud Run provides automatic monitoring:
- Request count
- Request latency
- Error rate
- Container CPU/Memory utilization

View at: https://console.cloud.google.com/run/detail/us-central1/harv-backend/metrics

## Updating Deployment

To update the deployed service:

1. Make code changes in `./serve/`
2. (Optional) Test locally with `make run`
3. Deploy updates:
   ```bash
   make gcp-deploy
   ```

Cloud Run automatically:
- Builds new Docker image
- Creates new revision
- Routes traffic to new revision
- Keeps previous revisions for rollback

## Rollback

To rollback to a previous revision:

```bash
# List revisions
gcloud run revisions list \
  --service=harv-backend \
  --region=us-central1 \
  --project=ac215-475022

# Rollback to specific revision
gcloud run services update-traffic harv-backend \
  --to-revisions=harv-backend-00001-abc=100 \
  --region=us-central1 \
  --project=ac215-475022
```

## Cost Optimization

Cloud Run pricing:
- **CPU**: $0.00002400/vCPU-second (only while processing requests)
- **Memory**: $0.00000250/GiB-second
- **Requests**: $0.40 per million requests
- **Free Tier**: 2 million requests/month, 360,000 GiB-seconds/month

To reduce costs:
- Set minimum instances to 0 (scales to zero when idle)
- Use smaller CPU/memory if sufficient
- Implement request caching

## Troubleshooting

### Service account key already exists

If you get an error creating keys:

```bash
# List existing keys
gcloud iam service-accounts keys list \
  --iam-account=harv-service@ac215-475022.iam.gserviceaccount.com

# Delete old key
gcloud iam service-accounts keys delete KEY_ID \
  --iam-account=harv-service@ac215-475022.iam.gserviceaccount.com
```

### Deployment fails - insufficient permissions

Ensure you have these IAM roles in the project:
- `roles/run.admin`
- `roles/iam.serviceAccountUser`
- `roles/storage.admin`

### Cold start issues

Cloud Run may have 1-2 second cold starts when scaling from zero. To reduce:
- Set minimum instances to 1 (costs more)
- Optimize Docker image size
- Use Cloud Run's startup CPU boost

### Model not loading

If the model fails to load:
1. Verify artifacts are uploaded: `gsutil ls gs://ac215-475022-assets/artifacts/`
2. Check service account has Storage Object Viewer role
3. Check Cloud Run logs for specific errors

## Security Considerations

1. **Service Account Key**: The `service-account.json` file is gitignored and should never be committed
2. **API Access**: Current deployment allows unauthenticated access. For production:
   ```bash
   # Require authentication
   gcloud run services update harv-backend \
     --no-allow-unauthenticated \
     --region=us-central1
   ```
3. **Environment Variables**: Sensitive values (API keys) should use Secret Manager
4. **CORS**: Configure CORS in FastAPI for production use

## Next Steps

After deployment:
1. Update frontend/dashboard to use new API_URL
2. Test all endpoints (health, geo, verify)
3. Set up monitoring alerts
4. Configure custom domain (optional)
5. Implement CI/CD pipeline for automated deployments

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Container Registry](https://cloud.google.com/container-registry/docs)
- [Service Account Best Practices](https://cloud.google.com/iam/docs/best-practices-service-accounts)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)
