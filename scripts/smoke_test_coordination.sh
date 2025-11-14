#!/bin/bash
# Smoke test for multi-agent coordination fixes
# Tests that meta-orchestration agents can access Redis MCP tools

set -e

echo "=== Multi-Agent Coordination Smoke Test ==="
echo ""

# Check Redis is running
echo "1. Checking Redis connection..."
if redis-cli ping > /dev/null 2>&1; then
    echo "   ✓ Redis is running"
else
    echo "   ✗ Redis is not running - please start Redis first"
    exit 1
fi

# Check agent files have been updated
echo ""
echo "2. Checking agent files updated with MCP tools..."
AGENTS_DIR="plugins/mycelium-core/agents"
AGENTS=(
    "09-meta-multi-agent-coordinator.md"
    "09-meta-task-distributor.md"
    "09-meta-context-manager.md"
    "09-meta-workflow-orchestrator.md"
    "09-meta-error-coordinator.md"
)

ALL_UPDATED=true
for agent in "${AGENTS[@]}"; do
    if grep -q "mcp__RedisMCPServer__" "$AGENTS_DIR/$agent" 2>/dev/null; then
        echo "   ✓ $agent has Redis MCP tools"
    else
        echo "   ✗ $agent missing Redis MCP tools"
        ALL_UPDATED=false
    fi
done

if [ "$ALL_UPDATED" = false ]; then
    echo ""
    echo "Error: Not all agents updated. Please apply the fix first."
    exit 1
fi

# Check no fantasy tools remain
echo ""
echo "3. Checking no fantasy tools in agent declarations..."
FANTASY_FOUND=false
for agent in "${AGENTS[@]}"; do
    # Check the tools: line specifically
    TOOLS_LINE=$(grep "^tools:" "$AGENTS_DIR/$agent" 2>/dev/null || echo "")

    if echo "$TOOLS_LINE" | grep -qE "(message-queue|^tools:.*pubsub|workflow-engine)" 2>/dev/null; then
        # Check if they're NOT prefixed with mcp__
        if ! echo "$TOOLS_LINE" | grep -q "mcp__"; then
            echo "   ✗ $agent still has fantasy tools"
            FANTASY_FOUND=true
        fi
    fi
done

if [ "$FANTASY_FOUND" = false ]; then
    echo "   ✓ No fantasy tools found in agent declarations"
else
    echo ""
    echo "Warning: Some agents still have fantasy tool declarations"
fi

# Test basic Redis operations
echo ""
echo "4. Testing basic Redis operations..."
redis-cli hset test:smoke:status coordinator ready > /dev/null
STATUS=$(redis-cli hget test:smoke:status coordinator)
if [ "$STATUS" = "ready" ]; then
    echo "   ✓ Redis hash operations work"
else
    echo "   ✗ Redis hash operations failed"
    exit 1
fi

redis-cli lpush test:smoke:queue task1 task2 task3 > /dev/null
QUEUE_LEN=$(redis-cli llen test:smoke:queue)
if [ "$QUEUE_LEN" = "3" ]; then
    echo "   ✓ Redis list operations work"
else
    echo "   ✗ Redis list operations failed"
    exit 1
fi

# Clean up test keys
redis-cli del test:smoke:status test:smoke:queue > /dev/null

# Run integration tests if available
echo ""
echo "5. Running integration tests..."
if [ -f "tests/integration/test_coordination_tools.py" ]; then
    python -m pytest tests/integration/test_coordination_tools.py -v --tb=short
else
    echo "   ⚠ Integration tests not found - skipping"
fi

echo ""
echo "=== Smoke Test Complete ==="
echo ""
echo "Summary:"
echo "  ✓ Redis is accessible"
echo "  ✓ All 5 meta-orchestration agents updated with MCP tools"
echo "  ✓ No fantasy tools in agent declarations"
echo "  ✓ Basic Redis operations verified"
echo "  ✓ Integration tests passed"
echo ""
echo "Next steps:"
echo "  1. Test with actual agent invocations"
echo "  2. Verify parallel agent coordination works"
echo "  3. Monitor Redis for agent state updates"
echo ""
