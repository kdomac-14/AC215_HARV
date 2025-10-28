SHELL := /bin/bash
.PHONY: run down logs clean test test-unit test-integration test-e2e test-load verify coverage evidence help setup-faces fine-tune-blurry data preprocess train_cpu all

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
	pytest

coverage-html: ## Generate HTML coverage report and open in browser
	pytest --cov-report=html
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

# GCP deployment targets
gcp-setup: ## Setup GCP service account and download credentials
	bash scripts/setup_gcp.sh

gcp-deploy: ## Deploy backend service to Cloud Run
	bash scripts/deploy_to_gcp.sh

gcp-upload-artifacts: ## Upload artifacts to GCS bucket
	bash scripts/upload_artifacts.sh

gcp-full-deploy: gcp-upload-artifacts gcp-deploy ## Upload artifacts and deploy to Cloud Run

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
