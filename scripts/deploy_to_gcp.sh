#!/bin/bash
# HARV - Deploy to GCP Cloud Run
# This script builds and deploys the backend service to Google Cloud Run

set -e

# GCP Configuration
PROJECT_ID="ac215-475022"
REGION="us-central1"
SERVICE_NAME="harv-backend"
GCS_BUCKET="ac215-475022-assets"
SA_NAME="harv-service"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=================================="
echo "HARV - GCP Cloud Run Deployment"
echo "=================================="
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo "=================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI not found. Please install it first."
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if logged in
echo "Checking GCP authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "Please log in to GCP:"
    gcloud auth login
fi

# Set project
echo "Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "Enabling required GCP APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    storage.googleapis.com \
    --project=${PROJECT_ID}

# Create service account if it doesn't exist
echo "Checking service account..."
if ! gcloud iam service-accounts describe ${SA_EMAIL} --project=${PROJECT_ID} &> /dev/null; then
    echo "Creating service account: ${SA_NAME}"
    gcloud iam service-accounts create ${SA_NAME} \
        --display-name="HARV Service Account" \
        --project=${PROJECT_ID}
    
    # Grant necessary permissions
    echo "Granting permissions to service account..."
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/storage.objectViewer"
    
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/aiplatform.user"
else
    echo "Service account already exists: ${SA_NAME}"
fi

# Create GCS bucket if it doesn't exist
echo "Checking GCS bucket..."
if ! gsutil ls -b gs://${GCS_BUCKET} &> /dev/null; then
    echo "Creating GCS bucket: ${GCS_BUCKET}"
    gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${GCS_BUCKET}
else
    echo "GCS bucket already exists: ${GCS_BUCKET}"
fi

# Build and push Docker image
echo "Building Docker image..."
IMAGE_URI="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

gcloud builds submit ./serve \
    --tag=${IMAGE_URI} \
    --project=${PROJECT_ID}

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_URI} \
    --platform=managed \
    --region=${REGION} \
    --allow-unauthenticated \
    --service-account=${SA_EMAIL} \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --set-env-vars="CHALLENGE_WORD=${CHALLENGE_WORD:-orchid}" \
    --set-env-vars="GEO_PROVIDER=google" \
    --set-env-vars="GEO_EPSILON_M=60" \
    --set-env-vars="PROJECT_ID=${PROJECT_ID}" \
    --project=${PROJECT_ID}

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --platform=managed \
    --region=${REGION} \
    --format='value(status.url)' \
    --project=${PROJECT_ID})

echo ""
echo "=================================="
echo "✅ Deployment Complete!"
echo "=================================="
echo "Service URL: ${SERVICE_URL}"
echo "API Health Check: ${SERVICE_URL}/healthz"
echo ""
echo "Update your .env file with:"
echo "API_URL=${SERVICE_URL}"
echo "=================================="
