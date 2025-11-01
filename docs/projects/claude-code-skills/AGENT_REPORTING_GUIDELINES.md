# Agent Reporting Guidelines

## Overview

This document defines how agents should report their work during milestone implementation to maintain a clean repository
while providing comprehensive session reports.

## Guiding Principle

**Reports are for session communication, not permanent documentation.**

Temporary reports help coordinate work during a session but lose value quickly. They should not clutter the repository.

## Report Storage Locations

### Use /tmp/ for Session Reports

**Store in `/tmp/` directory**:

- Task completion reports
- Validation results
- Status updates
- Session summaries
- Temporary analysis documents

**Examples**:

```bash
# Good - temporary session reports
/tmp/m01-task-1.1-completion.md
/tmp/m01-week1-status.md
/tmp/validation-results.md
/tmp/agent-analysis.md

# Bad - clutters repository
TASK_1.1_COMPLETION_REPORT.md
VALIDATION_RESULTS.md
M01_WEEK1_STATUS.md
```

### Use Repository for Permanent Documentation

**Store in repository** (these have lasting value):

- Technical documentation (API docs, guides)
- Architecture documentation
- Test documentation
- User guides
- README files
- Migration guides

**Examples**:

```bash
# Good - permanent value
docs/api/registry-api.md
docs/testing/TEST_QUALITY_STANDARDS.md
plugins/mycelium-core/registry/README.md
docs/guides/discovery-quickstart.md

# Also good - project tracking
docs/projects/claude-code-skills/milestones/M01_*.md
```

## Report Types and Storage

### Task Completion Reports

**Purpose**: Inform coordinator that task is complete **Storage**: `/tmp/task-<id>-completion.md` **Lifetime**: Single
session **Content**:

- Summary of implementation
- Test results
- Acceptance criteria checklist
- Validation instructions

**Example**:

```bash
/tmp/m01-task-1.1-completion.md
/tmp/m01-task-1.11-completion.md
```

### Validation Reports

**Purpose**: Document validation results **Storage**: `/tmp/validation-<task>.md` **Lifetime**: Single session
**Content**:

- Test execution results
- Performance benchmarks
- Coverage reports
- Issues found

**Example**:

```bash
/tmp/validation-task-1.1.md
/tmp/validation-integration-tests.md
```

### Session Status Reports

**Purpose**: Overall session or milestone status **Storage**: `/tmp/<milestone>-status.md` **Lifetime**: Single session
or milestone **Content**:

- Overall progress
- Completed tasks
- Blockers
- Next steps

**Example**:

```bash
/tmp/m01-week1-status.md
/tmp/m01-final-status.md
```

### Temporary Scripts

**Purpose**: One-time validation or setup **Storage**: `/tmp/validate-*.sh` or `/tmp/setup-*.sh` **Lifetime**: Single
session **Content**:

- Validation scripts
- Setup automation
- One-time checks

**Example**:

```bash
/tmp/validate-task-1.1.sh
/tmp/setup-test-db.sh
```

## Agent Workflow

### During Task Implementation

```bash
# 1. Work in your worktree
cd /path/to/worktree

# 2. When complete, create report in /tmp/
cat > /tmp/task-X.Y-completion.md << 'EOF'
# Task X.Y Complete

## Summary
[Implementation summary]

## Test Results
- Tests passing: X/Y
- Coverage: Z%

## Validation
[How to validate]
EOF

# 3. Report to coordinator
echo "Task X.Y complete. Report: /tmp/task-X.Y-completion.md"

# 4. Commit work (NOT the report)
git add <implementation files>
git commit -m "feat(task-X.Y): implement feature"
```

### For Session Summaries

```bash
# Create summary in /tmp/
cat > /tmp/session-summary.md << 'EOF'
# Session Summary

[What was accomplished]
EOF

# Display to user
cat /tmp/session-summary.md
```

## What NOT to Commit

❌ **Never commit these**:

- `TASK_*_COMPLETION_REPORT.md`
- `VALIDATION_RESULTS.md`
- `*_STATUS.md` (unless permanent project tracking)
- `validate-task-*.sh` (temporary validation scripts)
- Analysis dumps and temporary notes
- Session logs and debug output

## What TO Commit

✅ **Always commit these**:

- Implementation code
- Tests
- API documentation
- User guides
- README files
- Architecture documentation
- Migration guides
- Permanent validation scripts (in proper location)

## Repository Hygiene

### Before Creating PR

```bash
# Check for temporary files
git status | grep -E "(TASK_|VALIDATION|STATUS|COMPLETE|REPORT)"

# If found, remove them
git rm <temporary-files>
git commit -m "cleanup: remove temporary report files"
```

### Cleaning Up /tmp/

```bash
# /tmp/ is automatically cleaned on reboot
# Or manually clean old reports:
find /tmp/ -name "*-completion.md" -mtime +7 -delete
find /tmp/ -name "*-status.md" -mtime +7 -delete
```

## Examples

### Good Pattern

```bash
# Agent working on Task 1.1
cd .worktrees/m01-task-1.1-agent-registry

# Implement feature
# ... write code ...

# Create completion report in /tmp/
cat > /tmp/m01-task-1.1-completion.md << 'EOF'
# Task 1.1 Complete

Implementation finished, all tests passing.
See /tmp/m01-task-1.1-completion.md for details.
EOF

# Commit only the code
git add plugins/ tests/ docs/api/
git commit -m "feat(task-1.1): implement agent registry"

# Report to user
cat /tmp/m01-task-1.1-completion.md
```

### Bad Pattern

```bash
# Agent working on Task 1.1
cd .worktrees/m01-task-1.1-agent-registry

# Implement feature
# ... write code ...

# Create completion report IN REPO (bad!)
cat > TASK_1.1_COMPLETION_REPORT.md << 'EOF'
...
EOF

# Commit the report (bad!)
git add TASK_1.1_COMPLETION_REPORT.md
git commit -m "docs: add completion report"

# Now the repo is cluttered
```

## Exception: Milestone Tracking

**Project tracking documents** can live in the repository if they have lasting value:

**Acceptable**:

```
docs/projects/claude-code-skills/
├── milestones/
│   ├── M01_AGENT_DISCOVERY_SKILLS.md  ✓ (permanent)
│   ├── M02_SKILL_INFRASTRUCTURE.md    ✓ (permanent)
│   └── M03_TOKEN_OPTIMIZATION.md      ✓ (permanent)
├── architecture.md                     ✓ (permanent)
└── PROJECT_SUMMARY.md                  ✓ (permanent)
```

**Not Acceptable**:

```
docs/projects/claude-code-skills/
├── M01_WEEK1_STATUS.md                 ✗ (temporary)
├── M01_VALIDATION_RESULTS.md           ✗ (temporary)
└── TASK_1.1_COMPLETION.md              ✗ (temporary)
```

## Summary

**Remember**:

- 📁 `/tmp/` for session reports
- 📚 Repository for permanent documentation
- 🧹 Clean before PR
- ✅ Commit code, tests, and docs
- ❌ Don't commit reports

This keeps the repository clean and focused on code and permanent documentation while still enabling effective agent
coordination during sessions.

______________________________________________________________________

**Document Version**: 1.0 **Last Updated**: 2025-10-21 **Status**: Active
