#!/bin/bash
# CI Validation Script - Mirrors GitHub CI checks exactly
# Run this before pushing to ensure CI will pass

set -e

echo "========================================="
echo "CI Validation Script"
echo "Mirrors GitHub CI workflow checks"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# 1. Ruff Lint Check
echo "Step 1: Ruff Lint Check"
echo "Command: uv run ruff check plugins/ mycelium_onboarding/ tests/"
if uv run ruff check plugins/ mycelium_onboarding/ tests/; then
    echo -e "${GREEN}✓ Ruff lint passed${NC}"
else
    echo -e "${RED}✗ Ruff lint failed${NC}"
    FAILED=1
fi
echo ""

# 2. Ruff Format Check
echo "Step 2: Ruff Format Check"
echo "Command: uv run ruff format --check plugins/ mycelium_onboarding/ tests/"
if uv run ruff format --check plugins/ mycelium_onboarding/ tests/; then
    echo -e "${GREEN}✓ Ruff format passed${NC}"
else
    echo -e "${RED}✗ Ruff format failed${NC}"
    FAILED=1
fi
echo ""

# 3. Mypy Type Check
echo "Step 3: Mypy Type Check"
echo "Command: uv run mypy plugins/ mycelium_onboarding/"
if uv run mypy plugins/ mycelium_onboarding/; then
    echo -e "${GREEN}✓ Mypy passed${NC}"
else
    echo -e "${RED}✗ Mypy failed${NC}"
    FAILED=1
fi
echo ""

# 4. Unit Tests
echo "Step 4: Unit Tests"
echo "Command: uv run pytest tests/unit/ tests/test_*.py -v -m 'not integration and not benchmark and not slow'"
if uv run pytest tests/unit/ tests/test_*.py -v -m "not integration and not benchmark and not slow" --tb=short; then
    echo -e "${GREEN}✓ Unit tests passed${NC}"
else
    echo -e "${RED}✗ Unit tests failed${NC}"
    FAILED=1
fi
echo ""

# Summary
echo "========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All CI checks passed! ✓${NC}"
    echo "Safe to push to GitHub"
    exit 0
else
    echo -e "${RED}Some CI checks failed ✗${NC}"
    echo "Fix errors before pushing"
    exit 1
fi
