# M01 Git Worktree Workflow

## Overview

For M01 implementation, we're using **git worktrees** to provide isolated working directories for each agent/task while
maintaining integration under a single milestone feature branch.

## Branch Structure

```
main
└── feat/m01-agent-discovery-coordination (milestone branch)
    ├── feat/m01-task-1.1-agent-registry (worktree)
    ├── feat/m01-task-1.11-telemetry (worktree)
    ├── feat/m01-postgres-support (worktree)
    └── ... (additional task worktrees as needed)
```

## Worktree Locations

All worktrees are in `.worktrees/` directory (gitignored):

- **Task 1.1 (Agent Registry)**: `.worktrees/m01-task-1.1-agent-registry/`
- **Task 1.11 (Telemetry)**: `.worktrees/m01-task-1.11-telemetry/`
- **Postgres Support**: `.worktrees/m01-postgres-support/`

## Agent Workflow

### For Agents Working in Worktrees

**IMPORTANT**: All work stays **LOCAL** until the entire milestone is ready. No pushing to remote until Gerald approves
the complete milestone.

**1. Work in Your Assigned Worktree**

```bash
cd /home/gerald/git/mycelium/.worktrees/m01-task-X.Y-description
```

**2. Make Changes & Commit Locally**

```bash
# You're on your own feature branch automatically
git status
git add <files>
git commit -m "feat(task-X.Y): your change description"

# NO git push! Stay local.
```

**3. When Task Complete - Notify Coordinator**

```bash
# Create a summary report in your worktree
cat > TASK_COMPLETE.md << 'EOF'
# Task X.Y Complete

## Summary
[What you implemented]

## Acceptance Criteria
- [x] Criterion 1
- [x] Criterion 2

## Test Results
- Coverage: XX%
- Performance: XXms

## Files Changed
- file1.py
- file2.py

## Validation Instructions
[How Gerald can validate]
EOF

# Commit the report
git add TASK_COMPLETE.md
git commit -m "docs(task-X.Y): completion report"

# Report back in the conversation
```

**4. Coordinator Merges Locally**

```bash
# Gerald will merge your task branch into the milestone branch
cd /home/gerald/git/mycelium
git merge --no-ff feat/m01-task-X.Y-description -m "merge: Task X.Y into M01"
```

**5. Other Agents Can See Your Work**

```bash
# Other agents can pull the milestone branch updates
cd /home/gerald/git/mycelium/.worktrees/m01-task-A.B-other
git fetch /home/gerald/git/mycelium feat/m01-agent-discovery-coordination:refs/remotes/local/milestone
git merge local/milestone
```

### For Coordinator (Gerald/Multi-Agent-Coordinator)

**ALL WORK STAYS LOCAL - No Remote Push Until Milestone Complete**

**1. Monitor Task Completion**

```bash
cd /home/gerald/git/mycelium  # main worktree on milestone branch

# Check agent worktree status
for worktree in .worktrees/m01-*; do
  echo "=== $(basename $worktree) ==="
  git -C "$worktree" log -1 --oneline
  git -C "$worktree" status -s
done
```

**2. Review & Merge Task Branches Locally**

```bash
# When agent reports task complete:
cd /home/gerald/git/mycelium

# Review their work in their worktree
cd .worktrees/m01-task-X.Y-description
less TASK_COMPLETE.md

# Run their validation
./scripts/validate-task-X.Y.sh  # or pytest, etc.

# If approved, merge into milestone branch
cd /home/gerald/git/mycelium
git merge --no-ff feat/m01-task-X.Y-description \
  -m "merge: Task X.Y - [description]

Acceptance criteria:
- Criterion 1
- Criterion 2

Validated by: Gerald
Test coverage: XX%
Performance: validated"
```

**3. Make Updates Available to Other Agents**

```bash
# Other agents working in parallel can pull milestone updates
# (They do this in their own worktrees when needed)
```

**4. When ALL M01 Tasks Complete - Push Everything**

```bash
cd /home/gerald/git/mycelium

# Final validation of integrated milestone
pytest tests/integration/test_discovery_coordination.py -v

# Push milestone branch (first time)
git push -u origin feat/m01-agent-discovery-coordination

# Create PR to main
gh pr create \
  --base main \
  --head feat/m01-agent-discovery-coordination \
  --title "feat: M01 Agent Discovery & Coordination Skills" \
  --body "Complete M01 milestone - all 11 tasks integrated and validated"
```

## Key Advantages

✅ **Isolation**: Each agent works in separate directory - no conflicts ✅ **Local Development**: No remote pushes until
milestone ready - saves CI resources ✅ **Integration**: All merge to milestone branch before main ✅ **Review**: Each
task validated locally before merge ✅ **Parallel**: Multiple agents work simultaneously ✅ **Clean History**: Milestone
branch shows integrated progress ✅ **Efficient**: One push per milestone instead of per task

## Common Commands

### List All Worktrees

```bash
git worktree list
```

### Add New Task Worktree

```bash
git worktree add .worktrees/m01-task-X.Y-name -b feat/m01-task-X.Y-name
```

### Remove Completed Worktree (after local merge)

```bash
git worktree remove .worktrees/m01-task-X.Y-name
git branch -d feat/m01-task-X.Y-name  # local cleanup
```

### Sync Between Worktrees (Local Only)

```bash
# In main worktree - merge completed task
cd /home/gerald/git/mycelium
git merge --no-ff feat/m01-task-X.Y-name

# Other worktrees can pull milestone updates if needed
cd .worktrees/m01-task-A.B-other
git merge feat/m01-agent-discovery-coordination  # pull from local main worktree
```

## Worktree Best Practices

### DO:

- ✅ Work exclusively in your assigned worktree
- ✅ Commit frequently with clear messages (locally)
- ✅ Report completion to coordinator when task done
- ✅ Keep worktree focused on single task
- ✅ Create TASK_COMPLETE.md summary when finished

### DON'T:

- ❌ Push to remote (everything stays local until milestone ready)
- ❌ Switch branches in a worktree (defeats the purpose)
- ❌ Create PRs during development (only at milestone completion)
- ❌ Modify files outside your task scope
- ❌ Delete worktree while branch has uncommitted work

## Integration Flow

```
Agent Work (worktree)
  → Commit Locally
  → Report Complete
  → Gerald Reviews & Validates
  → Local Merge to Milestone Branch
  → (Repeat for all tasks)
  → All Tasks Complete & Validated
  → Push Milestone Branch to Remote (first time)
  → Create PR: Milestone → Main
  → M01 Complete!
```

**Benefits of Local-Only Development:**

- 🚀 No CI/CD triggered until milestone ready
- 💰 Saves compute resources
- ⚡ Faster iteration (no wait for remote operations)
- 🔒 Keep WIP private until polished
- 🧹 Cleaner remote history

## Troubleshooting

### "Branch already exists"

```bash
# If worktree creation fails
git worktree remove .worktrees/m01-task-X.Y-name
git branch -D feat/m01-task-X.Y-name
# Then recreate
git worktree add .worktrees/m01-task-X.Y-name -b feat/m01-task-X.Y-name
```

### "Cannot remove worktree - uncommitted changes"

```bash
cd .worktrees/m01-task-X.Y-name
git status
# Either commit or stash changes
git add . && git commit -m "WIP: save progress"
# OR
git stash
```

### "Need to see another agent's work"

```bash
# From your worktree, merge milestone branch
cd .worktrees/m01-task-X.Y-name
git fetch origin
git merge origin/feat/m01-agent-discovery-coordination
```

## Current M01 Worktrees

| Task     | Worktree Path                            | Branch                             | Agent             |
| -------- | ---------------------------------------- | ---------------------------------- | ----------------- |
| 1.1      | `.worktrees/m01-task-1.1-agent-registry` | `feat/m01-task-1.1-agent-registry` | backend-developer |
| 1.11     | `.worktrees/m01-task-1.11-telemetry`     | `feat/m01-task-1.11-telemetry`     | backend-developer |
| Postgres | `.worktrees/m01-postgres-support`        | `feat/m01-postgres-support`        | postgres-pro      |

______________________________________________________________________

**Document Version:** 1.0 **Last Updated:** 2025-10-21 **For:** M01 Agent Discovery & Coordination Skills
