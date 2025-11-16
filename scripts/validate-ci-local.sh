#!/bin/bash
# Local CI Validation Script
# This script runs the exact same checks as GitHub CI to catch issues before pushing
# Usage: ./scripts/validate-ci-local.sh [--fix] [--skip-integration]

set -e  # Exit on any error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SKIP_INTEGRATION=false
FIX_MODE=false
WORKSPACE_ROOT=$(cd "$(dirname "$0")/.." && pwd)

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --fix)
      FIX_MODE=true
      shift
      ;;
    --skip-integration)
      SKIP_INTEGRATION=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --fix                 Auto-fix issues where possible (ruff)"
      echo "  --skip-integration   Skip integration tests (PostgreSQL not required)"
      echo "  --help               Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

cd "$WORKSPACE_ROOT"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Local CI Validation (matches GitHub CI)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Track overall status
OVERALL_STATUS=0

# Function to run a check and track status
run_check() {
  local name=$1
  shift
  echo -e "${BLUE}Running: ${name}${NC}"
  if "$@"; then
    echo -e "${GREEN}✓ ${name} passed${NC}"
    echo ""
    return 0
  else
    echo -e "${RED}✗ ${name} failed${NC}"
    echo ""
    OVERALL_STATUS=1
    return 1
  fi
}

# 1. Ruff Linting (matches ci.yml line 48)
echo -e "${YELLOW}=== Step 1: Ruff Linting ===${NC}"
if [ "$FIX_MODE" = true ]; then
  run_check "Ruff lint (with fixes)" uv run ruff check --fix plugins/ mycelium_onboarding/ tests/
else
  run_check "Ruff lint" uv run ruff check plugins/ mycelium_onboarding/ tests/
fi

# 2. Ruff Format Check (matches ci.yml line 52)
echo -e "${YELLOW}=== Step 2: Ruff Format Check ===${NC}"
if [ "$FIX_MODE" = true ]; then
  run_check "Ruff format (with fixes)" uv run ruff format plugins/ mycelium_onboarding/ tests/
else
  run_check "Ruff format check" uv run ruff format --check plugins/ mycelium_onboarding/ tests/
fi

# 3. Mypy Type Checking (matches ci.yml line 85)
echo -e "${YELLOW}=== Step 3: Mypy Type Checking ===${NC}"
run_check "Mypy type check" uv run mypy plugins/ mycelium_onboarding/

# 4. Unit Tests (matches ci.yml lines 140-146)
echo -e "${YELLOW}=== Step 4: Unit Tests ===${NC}"
run_check "Unit tests" uv run pytest tests/unit/ tests/test_*.py -v \
  -m "not integration and not benchmark and not slow" \
  --tb=short \
  --cov=plugins \
  --cov=mycelium_onboarding \
  --cov-report=xml \
  --cov-report=term

# 5. Integration Tests (matches ci.yml lines 257-263)
if [ "$SKIP_INTEGRATION" = false ]; then
  echo -e "${YELLOW}=== Step 5: Integration Tests ===${NC}"

  # Check if PostgreSQL is available
  if command -v pg_isready >/dev/null 2>&1 && pg_isready -h localhost -p 5432 -U mycelium >/dev/null 2>&1; then
    echo -e "${GREEN}PostgreSQL is available${NC}"

    # Set environment variables for integration tests
    export PYTHONPATH="$WORKSPACE_ROOT"
    export POSTGRES_HOST=localhost
    export POSTGRES_PORT=5432
    export POSTGRES_USER=mycelium
    export POSTGRES_PASSWORD=mycelium_test
    export POSTGRES_DB=mycelium_test
    export DATABASE_URL=postgresql://mycelium:mycelium_test@localhost:5432/mycelium_test

    run_check "Integration tests" uv run pytest tests/integration/ -v \
      -m "integration" \
      --tb=short \
      --cov=plugins \
      --cov=mycelium_onboarding \
      --cov-report=xml \
      --cov-report=term
  else
    echo -e "${YELLOW}PostgreSQL not available, skipping integration tests${NC}"
    echo -e "${YELLOW}Integration tests will run in CI - ensure database is set up correctly${NC}"
    echo ""

    # At least validate that tests can be collected
    run_check "Integration test collection" uv run pytest tests/integration/ --collect-only -q
  fi
else
  echo -e "${YELLOW}=== Step 5: Integration Tests (SKIPPED) ===${NC}"
  echo -e "${YELLOW}Use without --skip-integration to run integration tests${NC}"
  echo ""
fi

# 6. Cross-platform compatibility check (basic)
echo -e "${YELLOW}=== Step 6: Path Compatibility Check ===${NC}"
echo "Checking for platform-specific path usage..."
if grep -r "os\.path\." --include="*.py" plugins/ mycelium_onboarding/ | grep -v "test" | grep -v "\.pyc" > /dev/null; then
  echo -e "${YELLOW}⚠ Found os.path usage - consider using pathlib.Path for cross-platform compatibility${NC}"
  echo "Files with os.path:"
  grep -r "os\.path\." --include="*.py" plugins/ mycelium_onboarding/ | grep -v "test" | grep -v "\.pyc" | head -5
  echo ""
else
  echo -e "${GREEN}✓ No problematic os.path usage found${NC}"
  echo ""
fi

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}========================================${NC}"

if [ $OVERALL_STATUS -eq 0 ]; then
  echo -e "${GREEN}✓ All CI validation checks passed!${NC}"
  echo -e "${GREEN}Your code should pass CI checks on GitHub${NC}"
  exit 0
else
  echo -e "${RED}✗ Some CI validation checks failed${NC}"
  echo -e "${RED}Please fix the issues above before pushing${NC}"
  exit 1
fi
