#!/bin/bash
# CI Status Check Script for PR #15
# Multi-Agent Coordinator: DevOps Incident Response

set -e

PR_NUMBER=15
BRANCH="feat/phase2-smart-onboarding-unified"

echo "========================================"
echo "CI STATUS CHECK FOR PR #${PR_NUMBER}"
echo "Branch: ${BRANCH}"
echo "========================================"
echo ""

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "ERROR: GitHub CLI (gh) is not installed"
    exit 1
fi

# Check PR status
echo "1. CHECKING PR STATUS..."
echo "----------------------------------------"
gh pr view ${PR_NUMBER} --json number,title,state,isDraft,mergeable,statusCheckRollup

echo ""
echo "2. CHECKING CI RUNS..."
echo "----------------------------------------"
gh pr checks ${PR_NUMBER} --watch --interval 10

echo ""
echo "3. GETTING DETAILED STATUS..."
echo "----------------------------------------"
gh pr checks ${PR_NUMBER}

# Get the latest workflow run
echo ""
echo "4. GETTING LATEST WORKFLOW RUN..."
echo "----------------------------------------"
LATEST_RUN=$(gh run list --branch ${BRANCH} --limit 1 --json databaseId --jq '.[0].databaseId')

if [ -n "$LATEST_RUN" ]; then
    echo "Latest workflow run ID: ${LATEST_RUN}"
    echo ""
    echo "5. WORKFLOW RUN DETAILS..."
    echo "----------------------------------------"
    gh run view ${LATEST_RUN}

    echo ""
    echo "6. CHECKING FOR FAILURES..."
    echo "----------------------------------------"
    gh run view ${LATEST_RUN} --log-failed > /tmp/ci_failures.log 2>&1 || true

    if [ -s /tmp/ci_failures.log ]; then
        echo "FAILURES DETECTED - Logs saved to /tmp/ci_failures.log"
        cat /tmp/ci_failures.log
    else
        echo "No failures detected or run still in progress"
    fi
else
    echo "No workflow runs found for branch ${BRANCH}"
fi

echo ""
echo "========================================"
echo "CI STATUS CHECK COMPLETE"
echo "========================================"
