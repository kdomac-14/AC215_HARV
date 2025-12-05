# HARV – Production Deployment Guide

> **Milestone 5** – Complete GKE deployment with Pulumi Infrastructure as Code

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [GCP Project Setup](#3-gcp-project-setup)
4. [Pulumi Setup](#4-pulumi-setup)
5. [Build & Push Backend Docker Image](#5-build--push-backend-docker-image)
6. [Deploy to GKE](#6-deploy-to-gke)
7. [Connecting the Frontend](#7-connecting-the-frontend)
8. [Troubleshooting](#8-troubleshooting)
9. [Cleanup Instructions](#9-cleanup-instructions)

---

## 1. Overview

### Purpose

This document provides step-by-step instructions for deploying the HARV (Harvard Attendance Recognition and Verification) application to Google Cloud Platform. A teaching fellow with no prior knowledge of the project should be able to follow these instructions to achieve a fully functional production deployment.

### What Gets Deployed

| Component | GCP Service | Description |
|-----------|-------------|-------------|
| **Kubernetes Cluster** | Google Kubernetes Engine (GKE) | Managed K8s cluster with auto-scaling node pool |
| **Backend API** | K8s Deployment | FastAPI application serving attendance + vision endpoints |
| **Load Balancer** | K8s Service (type: LoadBalancer) | Public IP for external traffic |
| **Auto-Scaling** | Horizontal Pod Autoscaler (HPA) | 2-5 replicas based on CPU utilization |
| **Container Registry** | Artifact Registry | Docker image storage |
| **Model Storage** | Cloud Storage (GCS) | ML model artifacts |

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HARV Production Architecture                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────┐                                                       │
│   │   Mobile App     │                                                       │
│   │  (Expo/React     │                                                       │
│   │   Native)        │                                                       │
│   └────────┬─────────┘                                                       │
│            │                                                                 │
│            │ HTTPS (port 80)                                                 │
│            ▼                                                                 │
│   ┌──────────────────┐                                                       │
│   │  GCP Load        │  External IP provisioned by K8s Service              │
│   │  Balancer        │  type: LoadBalancer                                   │
│   └────────┬─────────┘                                                       │
│            │                                                                 │
│            ▼                                                                 │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                    Google Kubernetes Engine (GKE)                     │  │
│   │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│   │  │                    harv-backend Deployment                       │ │  │
│   │  │  ┌─────────────┐  ┌─────────────┐       ┌─────────────┐        │ │  │
│   │  │  │   Pod 1     │  │   Pod 2     │  ...  │   Pod N     │        │ │  │
│   │  │  │  (FastAPI)  │  │  (FastAPI)  │       │  (FastAPI)  │        │ │  │
│   │  │  └─────────────┘  └─────────────┘       └─────────────┘        │ │  │
│   │  └─────────────────────────────────────────────────────────────────┘ │  │
│   │                              │                                        │  │
│   │  ┌───────────────────────────┴────────────────────────────────────┐  │  │
│   │  │         Horizontal Pod Autoscaler (HPA)                        │  │  │
│   │  │         • minReplicas: 2                                       │  │  │
│   │  │         • maxReplicas: 5                                       │  │  │
│   │  │         • targetCPUUtilization: 80%                            │  │  │
│   │  └────────────────────────────────────────────────────────────────┘  │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                              │                                               │
│         ┌────────────────────┴────────────────────┐                         │
│         ▼                                          ▼                         │
│   ┌──────────────────┐                    ┌──────────────────┐              │
│   │  Artifact        │                    │  Cloud Storage   │              │
│   │  Registry        │                    │  (GCS)           │              │
│   │                  │                    │                  │              │
│   │  Docker images   │                    │  • Model weights │              │
│   │  for backend     │                    │  • Artifacts     │              │
│   └──────────────────┘                    └──────────────────┘              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Reference Configuration

| Parameter | Value |
|-----------|-------|
| **GCP Project ID** | `ac215-475022` |
| **Region** | `us-central1` |
| **Zone** | `us-central1-a` |
| **GCS Bucket** | `ac215-475022-assets` |
| **Artifact Registry** | `us-central1-docker.pkg.dev/ac215-475022/harv-backend` |
| **Service Account** | `harv-service@ac215-475022.iam.gserviceaccount.com` |

---

## 2. Prerequisites

Install the following tools before proceeding. All commands assume macOS; adjust for Linux/Windows as needed.

### 2.1 Google Cloud SDK (gcloud CLI)

**Required version**: 450.0.0+

```bash
# macOS (Homebrew)
brew install google-cloud-sdk

# Or download installer
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Verify installation
gcloud version
# Google Cloud SDK 450.0.0+
```

**Initialize and authenticate:**

```bash
gcloud init
gcloud auth login
gcloud auth application-default login
```

### 2.2 Docker

**Required version**: 24.0+

```bash
# macOS (Homebrew)
brew install --cask docker

# Start Docker Desktop, then verify
docker --version
# Docker version 24.0.0+

# Verify Docker is running
docker info
```

### 2.3 Pulumi

**Required version**: 3.0+

```bash
# macOS (Homebrew)
brew install pulumi

# Verify installation
pulumi version
# v3.x.x

# Login to Pulumi (use local backend for simplicity)
pulumi login --local
# Or use Pulumi Cloud: pulumi login
```

### 2.4 Node.js + npm

**Required version**: Node 20.x, npm 10.x

```bash
# Using nvm (recommended)
nvm install 20
nvm use 20

# Or Homebrew
brew install node@20

# Verify
node --version   # v20.x.x
npm --version    # 10.x.x
```

### 2.5 Expo CLI (for frontend)

```bash
# Install globally
npm install -g expo-cli

# Verify
expo --version
```

### 2.6 Python + pip

**Required version**: Python 3.11+

```bash
# Using pyenv (recommended)
pyenv install 3.11
pyenv global 3.11

# Or Homebrew
brew install python@3.11

# Verify
python3 --version   # Python 3.11.x
pip3 --version
```

### 2.7 kubectl

```bash
# macOS (Homebrew)
brew install kubectl

# Verify
kubectl version --client
```

### 2.8 GKE Auth Plugin

```bash
# Required for kubectl to authenticate with GKE
gcloud components install gke-gcloud-auth-plugin

# Verify
gke-gcloud-auth-plugin --version
```

---

## 3. GCP Project Setup

### 3.1 Create or Select GCP Project

```bash
# Option A: Create new project
gcloud projects create ac215-475022 --name="HARV AC215"

# Option B: Use existing project
gcloud config set project ac215-475022

# Verify current project
gcloud config get-value project
```

### 3.2 Enable Billing

Ensure billing is enabled for your project:
- Visit: https://console.cloud.google.com/billing/linkedaccount?project=ac215-475022
- Link a billing account

### 3.3 Enable Required APIs

```bash
# Enable all required APIs (run as single command)
gcloud services enable \
  container.googleapis.com \
  artifactregistry.googleapis.com \
  compute.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  storage.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com

# Verify APIs are enabled
gcloud services list --enabled --filter="NAME:(container OR artifactregistry OR compute)"
```

**APIs Enabled:**

| API | Purpose |
|-----|---------|
| `container.googleapis.com` | Google Kubernetes Engine |
| `artifactregistry.googleapis.com` | Docker image storage |
| `compute.googleapis.com` | VM instances for GKE nodes |
| `iam.googleapis.com` | Service account management |
| `cloudresourcemanager.googleapis.com` | Project management |
| `storage.googleapis.com` | Cloud Storage for artifacts |
| `cloudbuild.googleapis.com` | Container builds (optional) |
| `secretmanager.googleapis.com` | Secrets management |

### 3.4 Create Artifact Registry Repository

```bash
# Create Docker repository
gcloud artifacts repositories create harv-backend \
  --repository-format=docker \
  --location=us-central1 \
  --description="HARV backend Docker images"

# Verify creation
gcloud artifacts repositories list --location=us-central1
```

**Expected output:**
```
REPOSITORY     FORMAT  LOCATION      DESCRIPTION
harv-backend   DOCKER  us-central1   HARV backend Docker images
```

### 3.5 Create Service Account for CI/CD and Pulumi

```bash
# Create service account
gcloud iam service-accounts create harv-service \
  --display-name="HARV Service Account" \
  --description="Service account for HARV deployment"

# Assign required roles
PROJECT_ID=ac215-475022
SA_EMAIL=harv-service@${PROJECT_ID}.iam.gserviceaccount.com

# Container/GKE permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/container.admin"

# Artifact Registry permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/artifactregistry.admin"

# Storage permissions (for model artifacts)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/storage.admin"

# Compute permissions (for GKE nodes)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/compute.admin"

# IAM permissions (for workload identity)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/iam.serviceAccountUser"
```

### 3.6 Download Service Account Key

```bash
# Download JSON key (store securely, never commit to git!)
gcloud iam service-accounts keys create ./service-account.json \
  --iam-account=$SA_EMAIL

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/service-account.json"

# Verify key works
gcloud auth activate-service-account --key-file=./service-account.json
gcloud config set account $SA_EMAIL
```

> ⚠️ **Security Warning**: The `service-account.json` file is gitignored and should **never** be committed to version control.

### 3.7 Create Cloud Storage Bucket (for ML artifacts)

```bash
# Create bucket
gsutil mb -l us-central1 gs://ac215-475022-assets

# Upload model artifacts (if they exist)
gsutil -m cp -r ./artifacts/* gs://ac215-475022-assets/artifacts/

# Verify upload
gsutil ls gs://ac215-475022-assets/artifacts/
```

---

## 4. Pulumi Setup

Pulumi manages all Kubernetes infrastructure as code. Configuration is in the `infra/` directory.

### 4.1 Install Pulumi Dependencies

```bash
cd infra
npm install
```

### 4.2 Initialize Pulumi Stack

```bash
# Create a new stack (e.g., "dev" or "prod")
pulumi stack init dev

# Or select existing stack
pulumi stack select dev
```

### 4.3 Configure Pulumi Stack

```bash
# Set GCP project and region (REQUIRED)
pulumi config set gcp:project ac215-475022
pulumi config set gcp:region us-central1
pulumi config set gcp:zone us-central1-a

# Set backend image URI (REQUIRED)
# Format: <region>-docker.pkg.dev/<project>/<repo>/<image>:<tag>
pulumi config set harv:backendImage us-central1-docker.pkg.dev/ac215-475022/harv-backend/backend:latest

# Optional: Customize cluster size
pulumi config set nodeCount 2
pulumi config set nodeMachineType e2-standard-2
pulumi config set backendReplicas 2

# Optional: Set environment variables for backend
pulumi config set harv:backendEnv '{"GEO_PROVIDER":"google","GEO_EPSILON_M":"60"}'

# Optional: Set secrets (encrypted)
pulumi config set --secret harv:backendSecretEnv '{"GOOGLE_API_KEY":"your-api-key"}'
```

### 4.4 View Current Configuration

```bash
# Show all config values
pulumi config

# Expected output:
# KEY                      VALUE
# gcp:project              ac215-475022
# gcp:region               us-central1
# gcp:zone                 us-central1-a
# harv:backendImage        us-central1-docker.pkg.dev/ac215-475022/harv-backend/backend:latest
# nodeCount                2
# nodeMachineType          e2-standard-2
```

### 4.5 Preview Deployment

```bash
# Dry-run to see what will be created
pulumi preview

# Expected resources:
# + gcp:container:Cluster        harv-cluster
# + gcp:container:NodePool       harv-node-pool
# + kubernetes:apps:Deployment   harv-backend
# + kubernetes:core:Service      harv-backend-svc
# + kubernetes:core:Service      harv-backend-lb
# + kubernetes:autoscaling:HorizontalPodAutoscaler harv-backend-hpa
```

---

## 5. Build & Push Backend Docker Image

### 5.1 Local Build

```bash
# From repository root
cd /path/to/AC215_HARV

# Build image for linux/amd64 (required for GKE)
make build-backend-image

# Or manually:
docker build \
  --platform linux/amd64 \
  -f backend/Dockerfile \
  -t us-central1-docker.pkg.dev/ac215-475022/harv-backend/backend:latest \
  .
```

### 5.2 Authenticate Docker to Artifact Registry

```bash
# Configure Docker to use gcloud credentials
gcloud auth configure-docker us-central1-docker.pkg.dev

# Verify authentication
docker pull us-central1-docker.pkg.dev/ac215-475022/harv-backend/backend:latest 2>&1 | head -5
# (Will fail if no image exists yet, but should not show auth errors)
```

### 5.3 Push Image to Artifact Registry

```bash
# Push the image
make push-backend-image

# Or manually:
docker push us-central1-docker.pkg.dev/ac215-475022/harv-backend/backend:latest
```

### 5.4 Verify Image in Artifact Registry

```bash
# List images in repository
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/ac215-475022/harv-backend

# Expected output:
# IMAGE                                                               DIGEST         CREATE_TIME          UPDATE_TIME
# us-central1-docker.pkg.dev/ac215-475022/harv-backend/backend        sha256:abc123  2024-01-01T00:00:00  2024-01-01T00:00:00
```

### 5.5 CI-Based Build (GitHub Actions)

For automated builds, add to `.github/workflows/cd.yml`. Set a repo secret named `GCP_SA_KEY` (or `GCP_CREDENTIALS`) containing the service account JSON; the workflow will use whichever exists.

```yaml
name: Build and Push

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY != '' && secrets.GCP_SA_KEY || secrets.GCP_CREDENTIALS }}
      
      - name: Configure Docker
        run: gcloud auth configure-docker us-central1-docker.pkg.dev
      
      - name: Build and Push
        run: |
          docker build --platform linux/amd64 -f backend/Dockerfile \
            -t us-central1-docker.pkg.dev/ac215-475022/harv-backend/backend:${{ github.sha }} \
            -t us-central1-docker.pkg.dev/ac215-475022/harv-backend/backend:latest .
          docker push us-central1-docker.pkg.dev/ac215-475022/harv-backend/backend:${{ github.sha }}
          docker push us-central1-docker.pkg.dev/ac215-475022/harv-backend/backend:latest
```

---

## 6. Deploy to GKE

### 6.1 Run Pulumi Deployment

```bash
cd infra

# Deploy all resources
pulumi up

# When prompted, review changes and type "yes" to confirm
```

**Expected output:**
```
Updating (dev)

     Type                                      Name                  Status
 +   pulumi:pulumi:Stack                       harv-infra-dev        created
 +   ├─ gcp:container:Cluster                  harv-cluster          created
 +   ├─ gcp:container:NodePool                 harv-node-pool        created
 +   ├─ pulumi:providers:kubernetes            harv-gke-provider     created
 +   ├─ kubernetes:core/v1:Secret              harv-backend-secret   created
 +   ├─ kubernetes:apps/v1:Deployment          harv-backend          created
 +   ├─ kubernetes:core/v1:Service             harv-backend-svc      created
 +   ├─ kubernetes:core/v1:Service             harv-backend-lb       created
 +   └─ kubernetes:autoscaling/v2:HorizontalPodAutoscaler  harv-backend-hpa  created

Outputs:
    backendExternalUrl: "http://34.123.45.67"
    gkeClusterEndpoint: "35.202.123.45"
    gkeClusterName    : "harv-cluster-dev"

Resources:
    + 9 created

Duration: 5m30s
```

### 6.2 Retrieve Outputs

```bash
# Get Load Balancer URL
pulumi stack output backendExternalUrl
# http://34.123.45.67

# Get cluster name
pulumi stack output gkeClusterName
# harv-cluster-dev

# Get kubeconfig (for kubectl access)
pulumi stack output gkeKubeconfig --show-secrets > kubeconfig.yaml
export KUBECONFIG=$(pwd)/kubeconfig.yaml
```

### 6.3 Configure kubectl

```bash
# Option A: Use Pulumi-generated kubeconfig
export KUBECONFIG=$(pwd)/infra/kubeconfig.yaml

# Option B: Use gcloud to configure kubectl
gcloud container clusters get-credentials harv-cluster-dev \
  --zone us-central1-a \
  --project ac215-475022

# Verify connection
kubectl cluster-info
```

### 6.4 Verify Kubernetes Resources

```bash
# Check pods are running
kubectl get pods -l app=harv-backend

# Expected output:
# NAME                            READY   STATUS    RESTARTS   AGE
# harv-backend-6d4f5b7c8d-abc12   1/1     Running   0          2m
# harv-backend-6d4f5b7c8d-def34   1/1     Running   0          2m

# Check services
kubectl get svc

# Expected output:
# NAME               TYPE           CLUSTER-IP     EXTERNAL-IP    PORT(S)        AGE
# harv-backend-lb    LoadBalancer   10.0.0.100     34.123.45.67   80:31234/TCP   3m
# harv-backend-svc   ClusterIP      10.0.0.101     <none>         80/TCP         3m

# Check HPA
kubectl get hpa

# Expected output:
# NAME               REFERENCE                 TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
# harv-backend-hpa   Deployment/harv-backend   5%/80%    2         5         2          3m
```

### 6.5 Test the Deployment

```bash
# Get Load Balancer IP
LB_URL=$(pulumi stack output backendExternalUrl)

# Health check
curl $LB_URL/health

# Expected response:
# {"ok":true,"app":"harv","version":"1.0.0"}

# Test GPS check-in endpoint
curl -X POST $LB_URL/api/checkin/gps \
  -H "Content-Type: application/json" \
  -d '{"student_id":"test123","course_id":"CS50","latitude":42.3736,"longitude":-71.1097}'
```

### 6.6 View Logs

```bash
# Stream logs from all backend pods
kubectl logs -l app=harv-backend -f

# Logs from specific pod
kubectl logs harv-backend-6d4f5b7c8d-abc12

# Previous container logs (if crashed)
kubectl logs harv-backend-6d4f5b7c8d-abc12 --previous
```

### 6.7 HPA Scaling Test

```bash
# Watch HPA in real-time
kubectl get hpa harv-backend-hpa --watch

# In another terminal, generate load
LB_URL=$(cd infra && pulumi stack output backendExternalUrl)
for i in {1..1000}; do
  curl -s $LB_URL/health > /dev/null &
done
wait

# Observe replicas scaling up (may take 1-2 minutes)
kubectl get pods -l app=harv-backend -w
```

---

## 7. Connecting the Frontend

### 7.1 Get the Load Balancer URL

```bash
cd infra
LB_URL=$(pulumi stack output backendExternalUrl)
echo "Backend URL: $LB_URL"
```

### 7.2 Configure Expo Environment

```bash
cd frontend

# Create or update .env file
echo "EXPO_PUBLIC_API_URL=$LB_URL" > .env

# Verify
cat .env
# EXPO_PUBLIC_API_URL=http://34.123.45.67
```

### 7.3 Rebuild and Run Expo App

```bash
# Install dependencies (if not already done)
npm install

# Clear cache and start
npx expo start --clear

# Or for production build
npx expo build:ios    # iOS
npx expo build:android # Android
```

### 7.4 Test Connection

1. Open Expo Go app on your device
2. Scan QR code from terminal
3. Navigate to Student Mode
4. Attempt a GPS check-in
5. Verify response from backend

---

## 8. Troubleshooting

### 8.1 Permission Denied Pulling Image

**Symptom:**
```
Error: ImagePullBackOff
Failed to pull image: permission denied
```

**Solution:**
```bash
# 1. Verify service account has Artifact Registry Reader role
gcloud projects add-iam-policy-binding ac215-475022 \
  --member="serviceAccount:harv-service@ac215-475022.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.reader"

# 2. Verify image exists
gcloud artifacts docker images list us-central1-docker.pkg.dev/ac215-475022/harv-backend

# 3. Verify image name in Pulumi config matches exactly
pulumi config get harv:backendImage
```

### 8.2 Incorrect Pulumi Config

**Symptom:**
```
error: Missing required configuration variable 'harv:backendImage'
```

**Solution:**
```bash
# List all config
pulumi config

# Set missing config
pulumi config set harv:backendImage us-central1-docker.pkg.dev/ac215-475022/harv-backend/backend:latest

# Verify GCP config is set
pulumi config set gcp:project ac215-475022
pulumi config set gcp:region us-central1
```

### 8.3 HPA Not Scaling

**Symptom:**
```
kubectl get hpa
# TARGETS shows <unknown>/80%
```

**Solution:**
```bash
# 1. Verify metrics-server is running
kubectl get pods -n kube-system | grep metrics-server

# 2. Check if resource requests are set in deployment
kubectl describe deployment harv-backend | grep -A5 "Requests"

# 3. Add resource requests to Pulumi config (if missing)
# Edit infra/index.ts to add:
# resources: {
#   requests: { cpu: "100m", memory: "256Mi" },
#   limits: { cpu: "500m", memory: "512Mi" }
# }

# 4. Redeploy
pulumi up
```

### 8.4 Backend 502/503 Errors

**Symptom:**
```
curl: (52) Empty reply from server
# Or: 502 Bad Gateway
```

**Solution:**
```bash
# 1. Check pod status
kubectl get pods -l app=harv-backend
kubectl describe pod <pod-name>

# 2. Check pod logs for errors
kubectl logs -l app=harv-backend --tail=50

# 3. Common causes:
#    - App crashing on startup (check logs)
#    - Port mismatch (should be 8000)
#    - Missing environment variables

# 4. Verify container port matches service
kubectl get svc harv-backend-lb -o yaml | grep targetPort
# Should be 8000

# 5. Test pod directly
kubectl port-forward deployment/harv-backend 8000:8000
curl http://localhost:8000/health
```

### 8.5 GKE Cluster Creation Fails

**Symptom:**
```
error: googleapi: Error 403: Kubernetes Engine API is not enabled
```

**Solution:**
```bash
# Enable required APIs
gcloud services enable container.googleapis.com compute.googleapis.com

# Verify
gcloud services list --enabled | grep container
```

### 8.6 Kubeconfig Authentication Issues

**Symptom:**
```
error: You must be logged in to the server (Unauthorized)
```

**Solution:**
```bash
# Install GKE auth plugin
gcloud components install gke-gcloud-auth-plugin

# Re-authenticate
gcloud auth login
gcloud container clusters get-credentials harv-cluster-dev \
  --zone us-central1-a \
  --project ac215-475022

# Verify
kubectl cluster-info
```

### 8.7 Pulumi State Conflicts

**Symptom:**
```
error: the current deployment has X resources with pending operations
```

**Solution:**
```bash
# Cancel pending operations
pulumi cancel

# Refresh state from cloud
pulumi refresh

# Retry deployment
pulumi up
```

---

## 9. Cleanup Instructions

### 9.1 Destroy Pulumi Resources

```bash
cd infra

# Destroy all Kubernetes and GKE resources
pulumi destroy

# When prompted, type "yes" to confirm

# Expected output:
# - kubernetes:autoscaling:HorizontalPodAutoscaler harv-backend-hpa deleted
# - kubernetes:core:Service harv-backend-lb deleted
# - kubernetes:core:Service harv-backend-svc deleted
# - kubernetes:apps:Deployment harv-backend deleted
# - gcp:container:NodePool harv-node-pool deleted
# - gcp:container:Cluster harv-cluster deleted
```

### 9.2 Delete Artifact Registry Images

```bash
# List all images
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/ac215-475022/harv-backend

# Delete specific image
gcloud artifacts docker images delete \
  us-central1-docker.pkg.dev/ac215-475022/harv-backend/backend:latest \
  --delete-tags --quiet

# Delete entire repository (removes all images)
gcloud artifacts repositories delete harv-backend \
  --location=us-central1 \
  --quiet
```

### 9.3 Delete Cloud Storage Bucket

```bash
# Remove all objects and bucket
gsutil rm -r gs://ac215-475022-assets

# Or just remove artifacts folder
gsutil rm -r gs://ac215-475022-assets/artifacts/
```

### 9.4 Delete Service Account

```bash
# Delete service account
gcloud iam service-accounts delete \
  harv-service@ac215-475022.iam.gserviceaccount.com \
  --quiet

# Remove local key file
rm -f service-account.json
```

### 9.5 Delete GCP Project (Optional - Removes Everything)

> ⚠️ **Warning**: This permanently deletes the entire project and all resources. Use with caution.

```bash
# Delete project
gcloud projects delete ac215-475022

# This will prompt for confirmation
```

### 9.6 Remove Pulumi Stack

```bash
cd infra

# Remove stack (after resources are destroyed)
pulumi stack rm dev

# Confirm by typing stack name
```

---

## Additional Resources

- **[README.md](README.md)** – Project overview and local development
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** – Detailed system architecture
- **[Pulumi GKE Documentation](https://www.pulumi.com/registry/packages/gcp/api-docs/container/cluster/)**
- **[GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)**
- **[Artifact Registry Documentation](https://cloud.google.com/artifact-registry/docs)**

---

## Quick Reference Commands

```bash
# === Build & Push ===
make build-backend-image          # Build Docker image
make push-backend-image           # Push to Artifact Registry

# === Pulumi ===
cd infra && pulumi up             # Deploy infrastructure
cd infra && pulumi destroy        # Tear down infrastructure
cd infra && pulumi stack output   # View outputs

# === Kubernetes ===
kubectl get pods                  # List pods
kubectl get svc                   # List services
kubectl get hpa                   # List autoscalers
kubectl logs -l app=harv-backend  # View logs

# === Testing ===
curl $LB_URL/health              # Health check
kubectl port-forward deployment/harv-backend 8000:8000  # Local access
```
