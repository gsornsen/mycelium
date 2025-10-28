---
allowed-tools: Bash(gh:*), Bash(glab:*), Bash(git:*), Bash(ls:*), Bash(cat:*), Read, Glob, mcp__github__*, mcp__temporal-mcp__*
description: CI/CD pipeline status checker. Shows build, test, and deployment status. Configurable for GitHub Actions, GitLab CI, Jenkins, or custom pipelines via .pipeline-status.sh.
argument-hint: [--detailed] [--watch]
---

# CI/CD Pipeline Status

Check the status of CI/CD pipelines for the current project.

## Context

**Command arguments**: $ARGS

**Supported Pipeline Systems** (auto-detect):

1. GitHub Actions - `.github/workflows/`
1. GitLab CI - `.gitlab-ci.yml`
1. Jenkins - `Jenkinsfile`
1. Custom - `.pipeline-status.sh`
1. Temporal - Workflow executions

**Repository Info** - Detect git branch, commit, and remote URL to contextualize pipeline runs.

## Your Task

Provide pipeline status using the appropriate method for the detected CI/CD system:

### Method 1: GitHub Actions

Use GitHub CLI to query workflow runs:

```bash
# Check if gh CLI is installed and authenticated
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) not installed"
    echo "Install: https://cli.github.com/"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub"
    echo "Run: gh auth login"
    exit 1
fi

# Get latest workflow runs
gh run list --limit 10 --json status,name,conclusion,createdAt,headBranch,databaseId

# For detailed view, show specific workflow
if [ -n "$1" ]; then
    gh run view "$1"
fi
```

**Output format**:

```
=== CI/CD Pipeline Status ===
System: GitHub Actions
Branch: main
Commit: abc1234

Recent Workflow Runs:

✅ CI (main)                    Success    2m ago     #1234
✅ Tests (main)                 Success    2m ago     #1235
🟡 Deploy to Staging (main)    Running    1m ago     #1236
❌ Lint (feature/new)          Failed     15m ago    #1237

Latest on current branch (main):
  Status: ✅ All checks passed
  Duration: 3m 45s
  Started: 2025-10-12 14:25:00

Failed Jobs:
  Lint (feature/new):
    - Step: Run ruff check
    - Error: Linting errors found in module.py:45
    - View: gh run view 1237
```

### Method 2: GitLab CI

Use GitLab API or CLI:

```bash
# Check for GitLab CLI (glab)
if command -v glab &> /dev/null; then
    # Get pipeline status for current branch
    glab ci list --status=running,success,failed
    glab ci status
else
    echo "⚠️  GitLab CLI not installed, using API..."

    # Extract project info from git remote
    GITLAB_REMOTE=$(git config --get remote.origin.url)
    # Parse and call API
fi
```

**Output format**:

```
=== CI/CD Pipeline Status ===
System: GitLab CI
Branch: main
Commit: abc1234

Pipeline #5678 (running):
  ✅ build      Success   (2m 15s)
  ✅ test       Success   (1m 45s)
  🟡 deploy     Running   (45s elapsed)

Recent Pipelines:
  #5678 (main)    Running    2m ago
  #5677 (main)    Success    1h ago
  #5676 (dev)     Failed     3h ago

View details: glab ci view 5678
```

### Method 3: Jenkins

Query Jenkins API:

```bash
# Check for Jenkins CLI or use curl
JENKINS_URL="${JENKINS_URL:-http://localhost:8080}"
JOB_NAME="${JENKINS_JOB_NAME:-$(basename $(pwd))}"

if [ -n "$JENKINS_API_TOKEN" ] && [ -n "$JENKINS_USER" ]; then
    # Query job status via API
    curl -s -u "$JENKINS_USER:$JENKINS_API_TOKEN" \
        "$JENKINS_URL/job/$JOB_NAME/lastBuild/api/json" | jq .
else
    echo "⚠️  Jenkins credentials not configured"
    echo "Set: JENKINS_URL, JENKINS_USER, JENKINS_API_TOKEN"
fi
```

**Output format**:

```
=== CI/CD Pipeline Status ===
System: Jenkins
Job: podcast-pipeline
Build: #42

Current Build (#42):
  Status: 🟡 Running
  Started: 3m 45s ago
  ETA: 2m remaining

Stages:
  ✅ Checkout        Complete   (15s)
  ✅ Dependencies    Complete   (45s)
  ✅ Build           Complete   (1m 30s)
  🟡 Test            Running    (1m 15s)
  ⏸️  Deploy          Pending

Recent Builds:
  #42 (main)    Running    3m ago
  #41 (main)    Success    2h ago
  #40 (dev)     Failed     1d ago

View: $JENKINS_URL/job/$JOB_NAME/42/
```

### Method 4: Custom Pipeline Script

If `.pipeline-status.sh` exists, execute it:

```bash
if [ -f ".pipeline-status.sh" ]; then
    echo "=== CI/CD Pipeline Status ==="
    echo "System: Custom"
    echo ""

    # Source and execute custom script
    source .pipeline-status.sh

    if declare -f get_pipeline_status > /dev/null; then
        get_pipeline_status "$@"
    else
        echo "❌ .pipeline-status.sh must define get_pipeline_status() function"
        exit 1
    fi
fi
```

**Custom script format** (`.pipeline-status.sh`):

```bash
#!/bin/bash

# Custom pipeline status function
get_pipeline_status() {
    local detailed="${1:-false}"

    echo "Branch: $(git rev-parse --abbrev-ref HEAD)"
    echo "Commit: $(git rev-parse --short HEAD)"
    echo ""

    # Check local test status
    echo "Local Tests:"
    if [ -f ".test-results/last-run.json" ]; then
        jq -r '.summary' .test-results/last-run.json
    else
        echo "  No recent test results"
    fi

    # Check build artifacts
    echo ""
    echo "Build Artifacts:"
    if [ -d "dist/" ]; then
        echo "  ✅ Found: dist/ ($(du -sh dist/ | cut -f1))"
    else
        echo "  ❌ Missing: dist/"
    fi

    # Check deployment status (custom logic)
    echo ""
    echo "Deployment:"
    if curl -sf http://localhost:8000/health > /dev/null; then
        echo "  ✅ Local server running"
    else
        echo "  ❌ Local server not running"
    fi
}
```

### Method 5: No CI/CD Detected

Provide guidance for setup:

```
=== CI/CD Pipeline Status ===

⚠️  No CI/CD system detected

To enable pipeline status tracking:

Option 1: GitHub Actions
  Create: .github/workflows/ci.yml
  Install: gh (GitHub CLI)
  Docs: https://docs.github.com/actions

Option 2: GitLab CI
  Create: .gitlab-ci.yml
  Install: glab (GitLab CLI)
  Docs: https://docs.gitlab.com/ee/ci/

Option 3: Custom Script
  Create: .pipeline-status.sh
  Define: get_pipeline_status() function

Option 4: Local Checks Only
  Run: pytest, ruff, mypy locally
  No CI/CD required for development
```

## Watch Mode (Optional)

If `--watch` flag is provided, poll for updates:

```bash
if [[ "$*" == *"--watch"* ]]; then
    echo "👀 Watching pipeline status (Ctrl+C to stop)..."
    echo ""

    while true; do
        clear
        # Run status check
        get_pipeline_status

        echo ""
        echo "Refreshing in 30 seconds..."
        sleep 30
    done
fi
```

## Detailed Mode

If `--detailed` flag is provided, include:

- Full job logs (last 50 lines)
- Artifact download URLs
- Test coverage reports
- Performance metrics
- Deployment URLs

```bash
if [[ "$*" == *"--detailed"* ]]; then
    echo ""
    echo "=== Detailed Pipeline Information ==="
    echo ""

    # Show recent logs
    echo "Recent Logs (last 50 lines):"
    if command -v gh &> /dev/null; then
        gh run view --log | tail -50
    fi

    # Show test coverage
    if [ -f "coverage.xml" ]; then
        echo ""
        echo "Test Coverage:"
        # Parse coverage report
    fi

    # Show artifacts
    echo ""
    echo "Build Artifacts:"
    if command -v gh &> /dev/null; then
        gh run view --json artifacts
    fi
fi
```

## Integration with Coordination Systems

If Redis MCP is available, cache pipeline status:

```javascript
// Store pipeline status for monitoring
await mcp__RedisMCPServer__json_set({
  name: "pipeline:status:current",
  path: "$",
  value: {
    system: "github",
    branch: "main",
    commit: "abc1234",
    status: "running",
    started_at: "2025-10-12T14:25:00Z",
    workflows: [
      {name: "CI", status: "success"},
      {name: "Tests", status: "success"},
      {name: "Deploy", status: "running"}
    ]
  }
});

// Set TTL (expire after 1 hour)
await mcp__RedisMCPServer__expire({
  name: "pipeline:status:current",
  expire_seconds: 3600
});
```

If TaskQueue MCP is available, create tasks for failed pipelines:

```javascript
// On pipeline failure, create recovery task
if (pipelineStatus === "failed") {
  await mcp__taskqueue__create_task({
    projectId: "ci-cd",
    title: "Investigate pipeline failure",
    description: `Pipeline #${buildNumber} failed on ${branch}

Failed Jobs:
- ${failedJobs.join('\n- ')}

View logs: ${logsUrl}`
  });
}
```

## Configuration File

Create `.pipeline-status.json` for custom settings:

```json
{
  "system": "github",
  "watch_interval_seconds": 30,
  "notification": {
    "enabled": true,
    "on_failure": true,
    "on_success": false
  },
  "filters": {
    "branches": ["main", "develop"],
    "workflows": ["CI", "Tests"]
  },
  "output": {
    "format": "standard",
    "show_logs": false
  }
}
```

## Error Handling

- Gracefully handle API authentication failures
- Provide helpful error messages with setup instructions
- Fall back to git log if CI/CD unavailable
- Suggest local test commands if no CI/CD configured

## Common Use Cases

**Before pushing code**:

```bash
/pipeline-status
# Check current status before pushing changes
```

**Monitoring long-running builds**:

```bash
/pipeline-status --watch
# Monitor build progress in real-time
```

**Debugging failures**:

```bash
/pipeline-status --detailed
# Get full logs and error details
```

**Integration with pre-push hook**:

```bash
# .git/hooks/pre-push
#!/bin/bash
if ! /pipeline-status | grep -q "All checks passed"; then
    echo "⚠️  Warning: Previous pipeline failed"
    read -p "Continue push? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
```

## Best Practices

1. **Cache API responses** to avoid rate limits
1. **Use CLI tools** (gh, glab) over direct API calls when available
1. **Implement retries** for transient API failures
1. **Store credentials securely** (use environment variables, not config files)
1. **Filter noise** - focus on current branch and recent runs
1. **Link to web UI** for detailed investigation
1. **Integrate with notifications** for critical failures
