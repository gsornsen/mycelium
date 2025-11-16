#!/bin/bash
################################################################################
# QUICK CI STATUS CHECK FOR PR #15
# Execute this script to get immediate CI status
################################################################################

set -e

PR=15
REPO="gsornsen/mycelium"
BRANCH="feat/phase2-smart-onboarding-unified"

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                   CI STATUS CHECK - PR #15                                 ║"
echo "║              Phase 2 Smart Onboarding (Unified)                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Repository: ${REPO}"
echo "Branch: ${BRANCH}"
echo "PR: https://github.com/${REPO}/pull/${PR}"
echo "Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "❌ ERROR: GitHub CLI (gh) is not installed"
    echo ""
    echo "Install with:"
    echo "  sudo apt install gh"
    echo ""
    echo "Or visit: https://cli.github.com/"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "ALTERNATIVE: Check via web browser"
    echo "  https://github.com/${REPO}/pull/${PR}"
    echo ""
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "❌ ERROR: Not authenticated with GitHub"
    echo ""
    echo "Authenticate with:"
    echo "  gh auth login"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "ALTERNATIVE: Check via web browser"
    echo "  https://github.com/${REPO}/pull/${PR}"
    echo ""
    exit 1
fi

echo ""
echo "┌────────────────────────────────────────────────────────────────────────────┐"
echo "│ CURRENT CHECK STATUS                                                       │"
echo "└────────────────────────────────────────────────────────────────────────────┘"
echo ""

# Get PR checks - store output and check for errors
if ! CHECKS_OUTPUT=$(gh pr checks ${PR} 2>&1); then
    echo "⚠️  Could not retrieve checks (PR may be very new or checks not started)"
    echo ""
    echo "Raw output:"
    echo "$CHECKS_OUTPUT"
    echo ""
else
    echo "$CHECKS_OUTPUT"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "┌────────────────────────────────────────────────────────────────────────────┐"
echo "│ RECENT WORKFLOW RUNS                                                       │"
echo "└────────────────────────────────────────────────────────────────────────────┘"
echo ""

gh run list --branch ${BRANCH} --limit 5 2>/dev/null || echo "No workflow runs found"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "┌────────────────────────────────────────────────────────────────────────────┐"
echo "│ QUICK ANALYSIS                                                             │"
echo "└────────────────────────────────────────────────────────────────────────────┘"
echo ""

# Try to get detailed status
if gh pr view ${PR} --json statusCheckRollup &> /dev/null; then
    STATUS_JSON=$(gh pr view ${PR} --json statusCheckRollup)

    # Count checks
    TOTAL_CHECKS=$(echo "$STATUS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('statusCheckRollup', [])))" 2>/dev/null || echo "0")

    if [ "$TOTAL_CHECKS" -gt 0 ]; then
        echo "Total checks: $TOTAL_CHECKS"

        # Try to count by status (may not work on all systems)
        PASSING=$(echo "$STATUS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(sum(1 for c in data.get('statusCheckRollup', []) if c.get('conclusion') == 'success'))" 2>/dev/null || echo "?")
        FAILING=$(echo "$STATUS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(sum(1 for c in data.get('statusCheckRollup', []) if c.get('conclusion') in ['failure', 'timed_out', 'cancelled']))" 2>/dev/null || echo "?")
        IN_PROGRESS=$(echo "$STATUS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(sum(1 for c in data.get('statusCheckRollup', []) if c.get('status') == 'in_progress'))" 2>/dev/null || echo "?")

        echo "  ✓ Passing: $PASSING"
        echo "  ✗ Failing: $FAILING"
        echo "  ⟳ In Progress: $IN_PROGRESS"
        echo ""

        if [ "$FAILING" != "0" ] && [ "$FAILING" != "?" ]; then
            echo "⚠️  FAILURES DETECTED"
            echo ""
            echo "Next steps:"
            echo "  1. Run detailed analyzer:"
            echo "     cd /home/gerald/git/mycelium"
            echo "     python3 scripts/ci_status_analyzer.py"
            echo ""
            echo "  2. Get failure logs:"
            echo "     RUN_ID=\$(gh run list --branch ${BRANCH} --limit 1 --json databaseId --jq '.[0].databaseId')"
            echo "     gh run view \$RUN_ID --log-failed"
            echo ""
        elif [ "$PASSING" = "$TOTAL_CHECKS" ]; then
            echo "✅ ALL CHECKS PASSING!"
            echo ""
            echo "PR #15 is READY TO MERGE"
            echo ""
        elif [ "$IN_PROGRESS" != "0" ] && [ "$IN_PROGRESS" != "?" ]; then
            echo "⏳ CHECKS IN PROGRESS"
            echo ""
            echo "Monitor in real-time:"
            echo "  gh pr checks ${PR} --watch --interval 10"
            echo ""
            echo "Expected completion: ~12-15 minutes from start"
            echo ""
        fi
    else
        echo "No checks found yet - CI may not have started"
        echo ""
        echo "Check again in 1-2 minutes or visit:"
        echo "  https://github.com/${REPO}/pull/${PR}"
        echo ""
    fi
else
    echo "Could not retrieve detailed status"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "┌────────────────────────────────────────────────────────────────────────────┐"
echo "│ AVAILABLE TOOLS                                                            │"
echo "└────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "📊 Detailed Analysis:"
echo "   python3 /home/gerald/git/mycelium/scripts/ci_status_analyzer.py"
echo ""
echo "👁  Real-time Monitoring:"
echo "   gh pr checks ${PR} --watch --interval 10"
echo ""
echo "📝 View Failure Logs:"
echo "   RUN_ID=\$(gh run list --branch ${BRANCH} --limit 1 --json databaseId --jq '.[0].databaseId')"
echo "   gh run view \$RUN_ID --log-failed"
echo ""
echo "🔄 Re-run Failed Jobs:"
echo "   RUN_ID=\$(gh run list --branch ${BRANCH} --limit 1 --json databaseId --jq '.[0].databaseId')"
echo "   gh run rerun \$RUN_ID --failed"
echo ""
echo "📖 Full Documentation:"
echo "   cat /home/gerald/git/mycelium/docs/CI_STATUS_REPORT_PR15.md"
echo ""
echo "🌐 Web Interface:"
echo "   https://github.com/${REPO}/pull/${PR}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ CI Status Check Complete"
echo ""
