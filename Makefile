SHELL := /bin/bash
.PHONY: run down logs clean test test-unit test-integration test-e2e test-load verify coverage evidence help

run: ## Build and run full pipeline + API + dashboard
	docker compose up --build

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

coverage: ## Generate and view coverage report
	pytest tests/ --cov-report=html:evidence/coverage/html --cov-report=term-missing
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

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
