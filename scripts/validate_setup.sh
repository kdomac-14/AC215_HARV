#!/bin/bash
set -e

echo "=========================================="
echo "Testing Infrastructure Validation"
echo "=========================================="
echo ""

ERRORS=0

# Check test files exist
echo "1. Checking test files..."
TEST_FILES=(
    "pytest.ini"
    "requirements-test.txt"
    "tests/conftest.py"
    "tests/unit/test_geo.py"
    "tests/integration/test_api.py"
    "tests/e2e/test_full_pipeline.py"
    "tests/load/load_test.js"
)

for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file - MISSING"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check scripts exist and are executable
echo ""
echo "2. Checking scripts..."
SCRIPTS=(
    "scripts/run_tests.sh"
    "scripts/wait_for_services.sh"
    "scripts/export_evidence.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            echo "   ✓ $script (executable)"
        else
            echo "   ⚠ $script (not executable)"
            chmod +x "$script"
            echo "     Fixed: made executable"
        fi
    else
        echo "   ✗ $script - MISSING"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check documentation
echo ""
echo "3. Checking documentation..."
DOCS=(
    "EVIDENCE.md"
    "TESTING_QUICKSTART.md"
    "docs/testing.md"
    "IMPLEMENTATION_COMPLETE.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo "   ✓ $doc"
    else
        echo "   ✗ $doc - MISSING"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check Makefile targets
echo ""
echo "4. Checking Makefile targets..."
TARGETS=(
    "test"
    "test-unit"
    "test-integration"
    "test-e2e"
    "test-load"
    "verify"
    "coverage"
    "evidence"
)

for target in "${TARGETS[@]}"; do
    if grep -q "^${target}:" Makefile; then
        echo "   ✓ make $target"
    else
        echo "   ✗ make $target - MISSING"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check CI/CD
echo ""
echo "5. Checking CI/CD workflow..."
if [ -f ".github/workflows/ci.yml" ]; then
    echo "   ✓ .github/workflows/ci.yml"
    if grep -q "pytest" .github/workflows/ci.yml; then
        echo "   ✓ Contains pytest tests"
    else
        echo "   ⚠ Missing pytest integration"
    fi
    if grep -q "coverage" .github/workflows/ci.yml; then
        echo "   ✓ Contains coverage reporting"
    else
        echo "   ⚠ Missing coverage reporting"
    fi
else
    echo "   ✗ .github/workflows/ci.yml - MISSING"
    ERRORS=$((ERRORS + 1))
fi

# Check Python dependencies
echo ""
echo "6. Checking Python test dependencies..."
if [ -f "requirements-test.txt" ]; then
    DEPS=("pytest" "pytest-cov" "requests")
    for dep in "${DEPS[@]}"; do
        if grep -q "$dep" requirements-test.txt; then
            echo "   ✓ $dep"
        else
            echo "   ⚠ $dep - not in requirements-test.txt"
        fi
    done
fi

# Check directory structure
echo ""
echo "7. Checking directory structure..."
DIRS=(
    "tests"
    "tests/unit"
    "tests/integration"
    "tests/e2e"
    "tests/load"
    "scripts"
    "docs"
)

for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "   ✓ $dir/"
    else
        echo "   ✗ $dir/ - MISSING"
        ERRORS=$((ERRORS + 1))
    fi
done

# Summary
echo ""
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ Validation PASSED - All checks successful!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "  1. Install dependencies: pip install -r requirements-test.txt"
    echo "  2. Start services: make run"
    echo "  3. Run tests: make test"
    echo "  4. Or run complete verification: make verify"
    echo ""
    exit 0
else
    echo "❌ Validation FAILED - $ERRORS error(s) found"
    echo "=========================================="
    echo ""
    echo "Please fix the errors above and run again."
    echo ""
    exit 1
fi
