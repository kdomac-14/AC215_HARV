#!/bin/bash
set -e

echo "=========================================="
echo "Exporting Test Evidence for Milestone 2"
echo "=========================================="

# Ensure evidence directory exists
mkdir -p evidence/{coverage,e2e,load,logs,screenshots}

echo ""
echo "1. Collecting coverage reports..."
if [ -d "evidence/coverage/html" ]; then
    echo "   ✓ Coverage HTML report found"
else
    echo "   ⚠ Coverage HTML report not found (run tests first)"
fi

if [ -f "evidence/coverage/coverage.xml" ]; then
    echo "   ✓ Coverage XML report found"
else
    echo "   ⚠ Coverage XML report not found (run tests first)"
fi

echo ""
echo "2. Collecting E2E results..."
if [ -f "evidence/e2e/e2e_results.json" ]; then
    echo "   ✓ E2E results found"
    cat evidence/e2e/e2e_results.json | head -20
else
    echo "   ⚠ E2E results not found (run E2E tests first)"
fi

echo ""
echo "3. Collecting load test results..."
if [ -f "evidence/load/results.json" ]; then
    echo "   ✓ Load test results found"
else
    echo "   ⚠ Load test results not found (run load tests first)"
fi

echo ""
echo "4. Collecting service logs..."
if command -v docker &> /dev/null; then
    if docker compose ps -q serve &> /dev/null; then
        echo "   Exporting serve logs..."
        docker compose logs serve > evidence/logs/serve.log 2>&1 || true
        echo "   ✓ Serve logs exported"
        
        echo "   Exporting dashboard logs..."
        docker compose logs dashboard > evidence/logs/dashboard.log 2>&1 || true
        echo "   ✓ Dashboard logs exported"
    else
        echo "   ⚠ Services not running (start with 'make run')"
    fi
else
    echo "   ⚠ Docker not available"
fi

echo ""
echo "5. Collecting artifacts..."
if [ -d "artifacts/model" ]; then
    echo "   ✓ Model artifacts found"
    ls -lh artifacts/model/ 2>/dev/null || true
fi

if [ -f "artifacts/metrics.json" ]; then
    echo "   ✓ Metrics found"
    cat artifacts/metrics.json | head -20
fi

echo ""
echo "6. Taking screenshots (if display available)..."
if command -v screencapture &> /dev/null; then
    # macOS screenshot command
    echo "   To take screenshots manually, use:"
    echo "   screencapture -w evidence/screenshots/api_test.png"
    echo "   screencapture -w evidence/screenshots/dashboard.png"
elif command -v scrot &> /dev/null; then
    # Linux screenshot command
    echo "   To take screenshots manually, use:"
    echo "   scrot evidence/screenshots/api_test.png"
fi

echo ""
echo "7. Creating evidence archive..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="milestone2_evidence_${TIMESTAMP}.tar.gz"

tar -czf "${ARCHIVE_NAME}" \
    evidence/ \
    artifacts/ \
    tests/ \
    pytest.ini \
    README.md \
    EVIDENCE.md \
    2>/dev/null || true

if [ -f "${ARCHIVE_NAME}" ]; then
    echo "   ✓ Evidence archive created: ${ARCHIVE_NAME}"
    echo "   Size: $(du -h ${ARCHIVE_NAME} | cut -f1)"
else
    echo "   ⚠ Failed to create archive"
fi

echo ""
echo "=========================================="
echo "Evidence Export Complete!"
echo "=========================================="
echo ""
echo "Evidence location:"
echo "  • Coverage: evidence/coverage/html/index.html"
echo "  • E2E results: evidence/e2e/e2e_results.json"
echo "  • Load tests: evidence/load/"
echo "  • Logs: evidence/logs/"
echo "  • Archive: ${ARCHIVE_NAME}"
echo ""
echo "Next steps:"
echo "  1. Review coverage report: open evidence/coverage/html/index.html"
echo "  2. Check E2E results: cat evidence/e2e/e2e_results.json"
echo "  3. Add screenshots to: evidence/screenshots/"
echo "  4. Submit: ${ARCHIVE_NAME}"
echo ""
