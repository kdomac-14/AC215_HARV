#!/bin/bash
# HARV - GCP Setup Script
# Creates service account and downloads credentials

set -e

# GCP Configuration
PROJECT_ID="ac215-475022"
SA_NAME="harv-service"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
KEY_FILE="./service-account.json"

echo "=================================="
echo "HARV - GCP Service Account Setup"
echo "=================================="
echo "Project ID: ${PROJECT_ID}"
echo "Service Account: ${SA_NAME}"
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

# Create service account if it doesn't exist
echo "Checking service account..."
if ! gcloud iam service-accounts describe ${SA_EMAIL} --project=${PROJECT_ID} &> /dev/null; then
    echo "Creating service account: ${SA_NAME}"
    gcloud iam service-accounts create ${SA_NAME} \
        --display-name="HARV Service Account" \
        --project=${PROJECT_ID}
    
    # Grant necessary permissions
    echo "Granting permissions..."
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/storage.objectViewer"
    
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/aiplatform.user"
    
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/run.invoker"
else
    echo "Service account already exists: ${SA_NAME}"
fi

# Download service account key
echo "Downloading service account key..."
if [ -f "${KEY_FILE}" ]; then
    echo "Warning: ${KEY_FILE} already exists. Creating backup..."
    cp ${KEY_FILE} ${KEY_FILE}.backup.$(date +%Y%m%d_%H%M%S)
fi

gcloud iam service-accounts keys create ${KEY_FILE} \
    --iam-account=${SA_EMAIL} \
    --project=${PROJECT_ID}

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo "Service account key saved to: ${KEY_FILE}"
echo ""
echo "Next steps:"
echo "1. Update your .env file:"
echo "   PROJECT_ID=${PROJECT_ID}"
echo "   GOOGLE_APPLICATION_CREDENTIALS=./service-account.json"
echo ""
echo "2. Deploy to Cloud Run:"
echo "   bash scripts/deploy_to_gcp.sh"
echo "=================================="
