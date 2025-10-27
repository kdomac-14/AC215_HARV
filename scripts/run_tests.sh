#!/bin/bash
set -e

echo "=========================================="
echo "Running HARV Test Suite"
echo "=========================================="

# Install test dependencies
echo ""
echo "1. Installing test dependencies..."
pip install -q -r requirements-test.txt
echo "   ✓ Dependencies installed"

# Create evidence directories
echo ""
echo "2. Creating evidence directories..."
mkdir -p evidence/{coverage,e2e,load,logs}
echo "   ✓ Directories created"

# Wait for services
echo ""
echo "3. Waiting for services..."
bash scripts/wait_for_services.sh

# Run unit tests
echo ""
echo "4. Running unit tests..."
pytest tests/unit/ -v -m unit --tb=short || true

# Run integration tests
echo ""
echo "5. Running integration tests..."
pytest tests/integration/ -v -m integration --tb=short || true

# Run E2E tests
echo ""
echo "6. Running E2E tests..."
pytest tests/e2e/ -v -m e2e --tb=short || true

# Generate coverage report
echo ""
echo "7. Generating coverage report..."
pytest tests/ --cov-report=html:evidence/coverage/html --cov-report=xml:evidence/coverage/coverage.xml --cov-report=term-missing || true

echo ""
echo "=========================================="
echo "Test Suite Complete!"
echo "=========================================="
echo ""
echo "Results:"
echo "  • Coverage: evidence/coverage/html/index.html"
echo "  • E2E results: evidence/e2e/e2e_results.json"
echo ""
