#!/bin/bash
# HARV - Upload artifacts to GCS
# Uploads trained models and artifacts to Google Cloud Storage

set -e

# GCP Configuration
PROJECT_ID="ac215-475022"
GCS_BUCKET="ac215-475022-assets"
ARTIFACTS_DIR="./artifacts"

echo "=================================="
echo "HARV - Upload Artifacts to GCS"
echo "=================================="
echo "Project ID: ${PROJECT_ID}"
echo "Bucket: gs://${GCS_BUCKET}"
echo "Source: ${ARTIFACTS_DIR}"
echo "=================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI not found. Please install it first."
    exit 1
fi

# Check if artifacts exist
if [ ! -d "${ARTIFACTS_DIR}" ]; then
    echo "Error: Artifacts directory not found: ${ARTIFACTS_DIR}"
    echo "Please run the training pipeline first: make run"
    exit 1
fi

# Set project
echo "Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# Upload artifacts
echo "Uploading artifacts to GCS..."
gsutil -m rsync -r ${ARTIFACTS_DIR} gs://${GCS_BUCKET}/artifacts/

echo ""
echo "=================================="
echo "✅ Upload Complete!"
echo "=================================="
echo "Artifacts location: gs://${GCS_BUCKET}/artifacts/"
echo ""
echo "To list uploaded files:"
echo "gsutil ls -r gs://${GCS_BUCKET}/artifacts/"
echo "=================================="
