#!/bin/bash
# Quick CI status check for PR #15
set -e

PR=15
BRANCH="feat/phase2-smart-onboarding-unified"

echo "========================================"
echo "QUICK CI STATUS CHECK - PR #${PR}"
echo "========================================"
echo ""

# Check if gh is available
if ! command -v gh &> /dev/null; then
    echo "ERROR: GitHub CLI not installed"
    echo "Install with: sudo apt install gh"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "ERROR: Not authenticated with GitHub"
    echo "Run: gh auth login"
    exit 1
fi

echo "1. PR STATUS"
echo "----------------------------------------"
gh pr view ${PR} --json number,title,state,isDraft,statusCheckRollup,mergeable | python3 -m json.tool

echo ""
echo "2. CHECK SUMMARY"
echo "----------------------------------------"
gh pr checks ${PR} || echo "Checks command failed or not available"

echo ""
echo "3. LATEST WORKFLOW RUN"
echo "----------------------------------------"
gh run list --branch ${BRANCH} --limit 3

echo ""
echo "========================================"
echo "Use 'gh pr checks ${PR} --watch' to monitor in real-time"
echo "========================================"
