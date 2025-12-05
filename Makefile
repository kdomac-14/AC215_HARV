SHELL := /bin/bash
COV_TARGETS := serve/src ingestion/src preprocess/src train/src evaluate/src export/src
PYTEST_COV := $(foreach target,$(COV_TARGETS),--cov=$(target))
IMAGE_TAG ?= latest
GCP_PROJECT_ID ?= ac215-475022
REGION ?= us-central1
ARTIFACT_REPO ?= harv-backend
BACKEND_IMAGE ?= $(REGION)-docker.pkg.dev/$(GCP_PROJECT_ID)/$(ARTIFACT_REPO)/backend:$(IMAGE_TAG)

.PHONY: run down logs clean test test-unit test-integration test-e2e test-load verify coverage evidence help setup-faces fine-tune-blurry data preprocess train_cpu all build-backend-image push-backend-image

run: ## Build and run full pipeline + API + dashboard
	docker compose up --build

# Individual component targets (for development/debugging)
data: ## Run ingestion component only
	docker compose run --rm ingestion

preprocess: ## Run preprocessing component only
	docker compose run --rm preprocess

train_cpu: ## Run training component only (CPU mode)
	docker compose run --rm train

evaluate: ## Run evaluation component only
	docker compose run --rm evaluate

export: ## Run export component only
	docker compose run --rm export

all: data preprocess train_cpu evaluate export ## Run complete pipeline sequentially

setup-faces: ## Setup real face dataset from Kaggle
	python scripts/simple_face_setup.py

fine-tune-blurry: ## Fine-tune model for blurry face recognition
	python scripts/fine_tune_blurry_faces.py

test-setup: ## Test face setup dependencies and configuration
	python scripts/test_setup.py

check-dataset: ## Check if real photos are in the dataset
	python scripts/check_dataset.py

download-faces: ## Download real face dataset from Kaggle
	python scripts/download_real_faces.py

down:
	docker compose down -v

logs:
	docker compose logs -f

clean:
	rm -rf artifacts/* data/interim/* data/processed/* infra/logs/*

# Testing targets
test: ## Run all tests (requires services running)
	@echo "Running full test suite..."
	bash scripts/run_tests.sh

test-unit: ## Run unit tests only
	pytest tests/unit/ -v -m unit

test-integration: ## Run integration tests (requires services)
	pytest tests/integration/ -v -m integration

test-e2e: ## Run end-to-end tests (requires services)
	pytest tests/e2e/ -v -m e2e

test-load: ## Run load tests with k6 (requires k6 installed)
	@if command -v k6 &> /dev/null; then \
		k6 run tests/load/load_test.js --out json=evidence/load/results.json; \
	else \
		echo "Error: k6 not installed. Install with: brew install k6"; \
		exit 1; \
	fi

verify: ## Verify complete system (start services, run tests, generate evidence)
	@echo "Starting verification workflow..."
	docker compose up -d --build
	@echo "Waiting for services..."
	bash scripts/wait_for_services.sh
	@echo "Running tests..."
	$(MAKE) test
	@echo "Generating evidence..."
	bash scripts/export_evidence.sh

coverage: ## Run tests with coverage (terminal output)
	pytest $(PYTEST_COV) \
		--cov-report=term-missing \
		--cov-report=xml:evidence/coverage/coverage.xml \
		--cov-report=html:evidence/coverage/html \
		--cov-fail-under=50

coverage-html: ## Generate HTML coverage report and open in browser
	pytest $(PYTEST_COV) \
		--cov-report=term-missing \
		--cov-report=xml:evidence/coverage/coverage.xml \
		--cov-report=html:evidence/coverage/html \
		--cov-fail-under=50
	@echo "Opening coverage report..."
	@if command -v open &> /dev/null; then \
		open evidence/coverage/html/index.html; \
	elif command -v xdg-open &> /dev/null; then \
		xdg-open evidence/coverage/html/index.html; \
	else \
		echo "Coverage report: evidence/coverage/html/index.html"; \
	fi

evidence: ## Export all evidence for submission
	bash scripts/export_evidence.sh

# Linting and formatting targets
fmt: ## Format code with ruff
	ruff format .

lint: ## Lint code with ruff
	ruff check .

typecheck: ## Type check with mypy
	mypy ingestion/src preprocess/src train/src serve/src --ignore-missing-imports

linkcheck: ## Check Markdown links in README and docs
	@echo "Checking Markdown links..."
	@if command -v markdown-link-check &> /dev/null; then \
		markdown-link-check README.md --quiet --config .markdown-link-check.json || true; \
		find docs -name "*.md" -exec markdown-link-check {} --quiet --config .markdown-link-check.json \; || true; \
		echo "Link check complete"; \
	else \
		echo "Warning: markdown-link-check not installed"; \
		echo "Install with: npm install -g markdown-link-check"; \
		echo "Skipping link check..."; \
	fi

# GCP deployment targets
gcp-setup: ## Setup GCP service account and download credentials
	bash scripts/setup_gcp.sh

gcp-deploy: ## Deploy backend service to Cloud Run
	bash scripts/deploy_to_gcp.sh

gcp-upload-artifacts: ## Upload artifacts to GCS bucket
	bash scripts/upload_artifacts.sh

gcp-full-deploy: gcp-upload-artifacts gcp-deploy ## Upload artifacts and deploy to Cloud Run

build-backend-image: ## Build backend container image for Artifact Registry
	@test -n "$(GCP_PROJECT_ID)" || (echo "GCP_PROJECT_ID is required" && exit 1)
	@test -n "$(ARTIFACT_REPO)" || (echo "ARTIFACT_REPO is required" && exit 1)
	docker build --platform linux/amd64 -f backend/Dockerfile -t $(BACKEND_IMAGE) .

push-backend-image: build-backend-image ## Push backend image to Artifact Registry
	gcloud auth configure-docker $(REGION)-docker.pkg.dev
	docker push $(BACKEND_IMAGE)

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
