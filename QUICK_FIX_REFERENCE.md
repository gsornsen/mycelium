# Multi-Agent Coordination - Quick Fix Reference

**Problem:** Coordinator declares fantasy tools\
**Solution:** Update 5 YAML files\
**Time:** 5 minutes\
**Impact:**
Unlock parallel coordination

## The Fix

Edit line 4 in these 5 files:\
`~/.claude/plugins/marketplaces/mycelium/plugins/mycelium-core/agents/`

1. `09-meta-multi-agent-coordinator.md`
1. `09-meta-context-manager.md`
1. `09-meta-task-distributor.md`
1. `09-meta-workflow-orchestrator.md`
1. `09-meta-error-coordinator.md`

Replace with real MCP tool names (see full docs for exact strings).

## Test

```bash
claude --agents multi-agent-coordinator -p "Store in Redis: hset test:fix status working"
redis-cli hget test:fix status  # Should return "working"
```

## Full Docs

See `/home/gerald/git/mycelium/`:

- INVESTIGATION_MULTI_AGENT_COORDINATOR.md (why)
- IMPLEMENTATION_PLAN_COORDINATION.md (how)
- COORDINATION_FIX_SUMMARY.md (overview)
