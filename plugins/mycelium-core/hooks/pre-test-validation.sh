#!/bin/bash
#
# Generalized pre-test validation hook for Claude Code
#
# This script validates infrastructure before running tests.
# It can be customized per-project via .pre-test-checks.sh in the project root.
#
# Exit codes:
#   0 - All checks passed, tests can proceed
#   1 - Infrastructure check failed, tests should not run
#   2 - Tests explicitly skipped/blocked
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"

echo "🔍 Validating infrastructure before tests..."
echo ""

# Check for project-specific pre-test checks
if [ -f "$PROJECT_ROOT/.pre-test-checks.sh" ]; then
    echo "📄 Found project-specific checks: .pre-test-checks.sh"
    source "$PROJECT_ROOT/.pre-test-checks.sh"

    if declare -f project_pre_test_checks > /dev/null; then
        if ! project_pre_test_checks; then
            echo ""
            echo "❌ Project-specific checks failed!"
            exit 1
        fi
    fi
    echo ""
fi

# Check for infra-check configuration
if [ -f "$PROJECT_ROOT/.infra-check.json" ] || [ -f "$HOME/.infra-check.json" ]; then
    echo "🏗️  Running infrastructure health check..."

    # Use the /infra-check slash command if available
    # Otherwise, run a basic check

    # Try to use Claude Code slash command (if in interactive session)
    # For non-interactive (CI/CD), run checks directly

    if [ -f "$PROJECT_ROOT/.infra-check.json" ]; then
        CONFIG_FILE="$PROJECT_ROOT/.infra-check.json"
    else
        CONFIG_FILE="$HOME/.infra-check.json"
    fi

    # Parse config and run basic checks
    echo "📋 Using config: $CONFIG_FILE"

    # Check if jq is available for parsing JSON
    if command -v jq &> /dev/null; then
        # Parse enabled checks from config
        REDIS_ENABLED=$(jq -r '.checks.redis.enabled // false' "$CONFIG_FILE")
        TEMPORAL_ENABLED=$(jq -r '.checks.temporal.enabled // false' "$CONFIG_FILE")
        TASKQUEUE_ENABLED=$(jq -r '.checks.taskqueue.enabled // false' "$CONFIG_FILE")
        POSTGRES_ENABLED=$(jq -r '.checks.postgresql.enabled // false' "$CONFIG_FILE")

        CHECKS_FAILED=0

        # Redis check
        if [ "$REDIS_ENABLED" = "true" ]; then
            REDIS_URL=$(jq -r '.checks.redis.url // "redis://localhost:6379"' "$CONFIG_FILE")
            echo -n "  Checking Redis ($REDIS_URL)... "

            if command -v redis-cli &> /dev/null; then
                if redis-cli -u "$REDIS_URL" ping &> /dev/null; then
                    echo "✅ OK"
                else
                    echo "❌ FAILED"
                    CHECKS_FAILED=$((CHECKS_FAILED + 1))
                fi
            else
                echo "⚠️  redis-cli not installed (skipped)"
            fi
        fi

        # Temporal check
        if [ "$TEMPORAL_ENABLED" = "true" ]; then
            TEMPORAL_HOST=$(jq -r '.checks.temporal.host // "localhost:7233"' "$CONFIG_FILE")
            echo -n "  Checking Temporal ($TEMPORAL_HOST)... "

            if command -v temporal &> /dev/null; then
                if temporal workflow list --limit 1 &> /dev/null; then
                    echo "✅ OK"
                else
                    echo "❌ FAILED"
                    CHECKS_FAILED=$((CHECKS_FAILED + 1))
                fi
            else
                echo "⚠️  temporal CLI not installed (skipped)"
            fi
        fi

        # TaskQueue check
        if [ "$TASKQUEUE_ENABLED" = "true" ]; then
            echo -n "  Checking TaskQueue (npx)... "

            if command -v npx &> /dev/null; then
                echo "✅ OK"
            else
                echo "❌ FAILED (npx not found)"
                CHECKS_FAILED=$((CHECKS_FAILED + 1))
            fi
        fi

        # PostgreSQL check
        if [ "$POSTGRES_ENABLED" = "true" ]; then
            POSTGRES_URL=$(jq -r '.checks.postgresql.connection_string // ""' "$CONFIG_FILE")
            if [ -n "$POSTGRES_URL" ]; then
                echo -n "  Checking PostgreSQL... "

                if command -v psql &> /dev/null; then
                    if psql "$POSTGRES_URL" -c "SELECT 1;" &> /dev/null; then
                        echo "✅ OK"
                    else
                        echo "❌ FAILED"
                        CHECKS_FAILED=$((CHECKS_FAILED + 1))
                    fi
                else
                    echo "⚠️  psql not installed (skipped)"
                fi
            fi
        fi

        echo ""

        if [ $CHECKS_FAILED -gt 0 ]; then
            echo "❌ $CHECKS_FAILED infrastructure check(s) failed!"
            echo ""
            echo "To fix, ensure required services are running:"

            if [ "$REDIS_ENABLED" = "true" ]; then
                echo "  - Redis: docker run -d -p 6379:6379 redis:latest"
            fi

            if [ "$TEMPORAL_ENABLED" = "true" ]; then
                echo "  - Temporal: temporal server start-dev"
            fi

            echo ""
            exit 1
        fi

    else
        echo "⚠️  jq not installed, skipping config parsing"
        echo "   Install jq to enable infrastructure checks: sudo apt install jq"
        echo ""
    fi
else
    echo "ℹ️  No infrastructure check configuration found"
    echo "   Create .infra-check.json to enable pre-test validation"
    echo ""
fi

# Run any additional custom validation
if declare -f custom_validation > /dev/null; then
    echo "🔧 Running custom validation..."
    if ! custom_validation; then
        echo ""
        echo "❌ Custom validation failed!"
        exit 1
    fi
    echo ""
fi

echo "✅ All validations passed!"
echo ""
exit 0
