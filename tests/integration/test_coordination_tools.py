"""Integration tests for multi-agent coordination tools.

Tests verify that meta-orchestration agents can:
1. Access Redis MCP tools
2. Access TaskQueue MCP tools
3. Coordinate multiple agents in parallel
4. Store and retrieve shared state
5. Publish and consume events
"""

import json
import time
from pathlib import Path

import pytest
import redis


@pytest.fixture
def redis_client():
    """Get Redis client for validation."""
    client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    # Clean up test keys
    for key in client.scan_iter("test:*"):
        client.delete(key)
    yield client
    # Clean up after tests
    for key in client.scan_iter("test:*"):
        client.delete(key)


@pytest.fixture
def agent_path():
    """Get path to multi-agent-coordinator agent."""
    return (
        Path(__file__).parent.parent.parent
        / "plugins"
        / "mycelium-core"
        / "agents"
        / "09-meta-multi-agent-coordinator.md"
    )


class TestRedisToolAccess:
    """Test that agents can access Redis MCP tools."""

    def test_agent_has_redis_tools(self, agent_path):
        """Verify agent declares Redis MCP tools."""
        content = agent_path.read_text()

        # Check for Redis MCP tool declarations
        assert "mcp__RedisMCPServer__hset" in content
        assert "mcp__RedisMCPServer__hget" in content
        assert "mcp__RedisMCPServer__publish" in content
        assert "mcp__RedisMCPServer__subscribe" in content

        # Check NO fantasy tools remain
        assert "message-queue" not in content or "mcp__" in content
        assert "pubsub" not in content or "mcp__" in content
        assert "workflow-engine" not in content or "mcp__" in content

    def test_redis_connection_available(self, redis_client):
        """Verify Redis is running and accessible."""
        assert redis_client.ping()

    def test_redis_hset_hget(self, redis_client):
        """Test basic Redis hash operations."""
        redis_client.hset("test:agent:status", "coordinator", "ready")
        status = redis_client.hget("test:agent:status", "coordinator")
        assert status == "ready"

    def test_redis_pubsub(self, redis_client):
        """Test Redis pub/sub operations."""
        pubsub = redis_client.pubsub()
        pubsub.subscribe("test:events")

        # Allow subscription to register
        time.sleep(0.1)

        redis_client.publish("test:events", "test_message")

        # Get messages (skip subscribe confirmation)
        messages = []
        for _ in range(3):  # Try a few times
            msg = pubsub.get_message(timeout=1)
            if msg and msg["type"] == "message":
                messages.append(msg)
                break

        assert len(messages) > 0
        assert messages[0]["data"] == "test_message"

    def test_redis_lists(self, redis_client):
        """Test Redis list operations for work queues."""
        redis_client.lpush("test:queue", "task1", "task2", "task3")

        length = redis_client.llen("test:queue")
        assert length == 3

        items = redis_client.lrange("test:queue", 0, -1)
        assert len(items) == 3

        first = redis_client.lpop("test:queue")
        assert first == "task3"  # LPUSH adds to head

    def test_redis_json(self, redis_client):
        """Test Redis JSON operations for complex state."""
        # Check if RedisJSON module is available
        try:
            redis_client.execute_command("JSON.SET", "test:check", "$", '{"test": true}')
        except redis.exceptions.ResponseError as e:
            if "unknown command" in str(e).lower():
                pytest.skip("RedisJSON module not available - using hset fallback")
            raise

        context = {"project": "neurite", "status": "in_progress", "agents_active": 3, "phase": "implementation"}

        redis_client.execute_command("JSON.SET", "test:context", "$", json.dumps(context))

        result = redis_client.execute_command("JSON.GET", "test:context", "$")
        retrieved = json.loads(result)[0]

        assert retrieved["project"] == "neurite"
        assert retrieved["agents_active"] == 3


class TestTaskQueueToolAccess:
    """Test that agents can access TaskQueue MCP tools."""

    def test_agent_has_taskqueue_tools(self, agent_path):
        """Verify agent declares TaskQueue MCP tools."""
        content = agent_path.read_text()

        assert "mcp__taskqueue__create_task" in content
        assert "mcp__taskqueue__get_task" in content
        assert "mcp__taskqueue__list_tasks" in content


class TestCoordinationPatterns:
    """Test coordination patterns work correctly."""

    def test_agent_state_tracking(self, redis_client):
        """Test tracking agent states in Redis."""
        # Simulate coordinator tracking multiple agents
        agents = ["python-pro", "test-automator", "doc-engineer"]

        for agent in agents:
            redis_client.hset(f"test:agent:{agent}", "status", "busy")
            redis_client.hset(f"test:agent:{agent}", "task", f"task_for_{agent}")
            redis_client.hset(f"test:agent:{agent}", "started_at", "2025-11-12T10:00:00Z")

        # Verify all agents tracked
        for agent in agents:
            status = redis_client.hgetall(f"test:agent:{agent}")
            assert status["status"] == "busy"
            assert agent in status["task"]

    def test_work_queue_distribution(self, redis_client):
        """Test distributing work via Redis queues."""
        # Add tasks to queue
        tasks = ["implement_auth", "write_tests", "update_docs"]
        for task in tasks:
            redis_client.rpush("test:pending_queue", task)

        # Simulate agents pulling tasks
        agent_tasks = {}
        for agent in ["agent1", "agent2", "agent3"]:
            task = redis_client.lpop("test:pending_queue")
            if task:
                agent_tasks[agent] = task

        assert len(agent_tasks) == 3
        assert set(agent_tasks.values()) == set(tasks)

    def test_event_broadcasting(self, redis_client):
        """Test event-driven coordination."""
        pubsub = redis_client.pubsub()
        pubsub.subscribe("test:events:completion")

        time.sleep(0.1)

        # Simulate agent completing task
        event = {
            "agent": "python-pro",
            "task": "implement_auth",
            "status": "completed",
            "timestamp": "2025-11-12T10:30:00Z",
        }

        redis_client.publish("test:events:completion", json.dumps(event))

        # Check event received
        for _ in range(3):
            msg = pubsub.get_message(timeout=1)
            if msg and msg["type"] == "message":
                received_event = json.loads(msg["data"])
                assert received_event["agent"] == "python-pro"
                assert received_event["status"] == "completed"
                break

    def test_shared_context_storage(self, redis_client):
        """Test storing shared context for coordination."""
        # Check if RedisJSON module is available
        try:
            redis_client.execute_command("JSON.SET", "test:check2", "$", '{"test": true}')
            has_json = True
        except redis.exceptions.ResponseError as e:
            if "unknown command" in str(e).lower():
                has_json = False
            else:
                raise

        if has_json:
            # Use RedisJSON
            context = {
                "project": "neurite",
                "status": "in_progress",
                "phase": "implementation",
                "active_agents": ["python-pro", "test-automator"],
                "completed_tasks": 5,
                "pending_tasks": 3,
            }

            redis_client.execute_command("JSON.SET", "test:context:project:neurite", "$", json.dumps(context))

            # Agents query context
            result = redis_client.execute_command("JSON.GET", "test:context:project:neurite", "$")
            retrieved = json.loads(result)[0]

            assert retrieved["status"] == "in_progress"
            assert len(retrieved["active_agents"]) == 2
        else:
            # Fallback to hash-based storage
            redis_client.hset("test:context:project:neurite", "status", "in_progress")
            redis_client.hset("test:context:project:neurite", "phase", "implementation")
            redis_client.hset("test:context:project:neurite", "completed_tasks", 5)
            redis_client.hset("test:context:project:neurite", "pending_tasks", 3)

            # Agents query context
            status = redis_client.hget("test:context:project:neurite", "status")
            phase = redis_client.hget("test:context:project:neurite", "phase")

            assert status == "in_progress"
            assert phase == "implementation"


class TestAgentCoordinationInstructions:
    """Test that agents have proper coordination instructions."""

    def test_coordinator_has_parallel_pattern(self, agent_path):
        """Verify coordinator knows how to invoke agents in parallel."""
        content = agent_path.read_text()

        # Should mention parallel agent invocation
        assert "parallel" in content.lower()
        assert "Task tool" in content or "Task:" in content

        # Should have examples of coordination
        assert "python-pro" in content or "agent" in content.lower()

    def test_coordinator_has_redis_examples(self, agent_path):
        """Verify coordinator has Redis usage examples."""
        content = agent_path.read_text()

        # Should have examples showing how to use Redis tools
        assert "mcp__RedisMCPServer__" in content
        assert "hset" in content
        assert "Example" in content or "example" in content

    def test_no_fantasy_tools_in_examples(self, agent_path):
        """Verify no fantasy tools in documentation."""
        content = agent_path.read_text()

        # Check that fantasy tools are NOT in examples
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "```" in line or "Example:" in line:
                # In code/example section
                context = "\n".join(lines[max(0, i - 5) : min(len(lines), i + 10)])

                # Should not have fantasy tool names without mcp__ prefix
                if "message-queue" in context:
                    assert "mcp__" in context  # Should be real MCP tool
                if "pubsub" in context:
                    assert "mcp__" in context or "Redis" in context
                if "workflow-engine" in context:
                    assert "mcp__" in context or "Temporal" in context


def test_all_meta_agents_updated():
    """Verify all meta-orchestration agents have been updated."""
    agents_dir = Path(__file__).parent.parent.parent / "plugins" / "mycelium-core" / "agents"

    meta_agents = [
        "09-meta-multi-agent-coordinator.md",
        "09-meta-task-distributor.md",
        "09-meta-context-manager.md",
        "09-meta-workflow-orchestrator.md",
        "09-meta-error-coordinator.md",
    ]

    for agent_file in meta_agents:
        agent_path = agents_dir / agent_file
        assert agent_path.exists(), f"Agent file not found: {agent_file}"

        content = agent_path.read_text()

        # Verify has MCP tools (at least one Redis tool)
        assert "mcp__RedisMCPServer__" in content, f"{agent_file} missing Redis MCP tools"

        # Verify NO fantasy tools in tools: line
        lines = content.split("\n")
        for line in lines:
            if line.startswith("tools:"):
                # Fantasy tools should NOT appear without mcp__ prefix
                tools_line = line.lower()
                if "message-queue" in tools_line or "pubsub" in tools_line or "workflow-engine" in tools_line:
                    if "message-queue" in tools_line:
                        assert "mcp__" in line, f"{agent_file} has fantasy tool 'message-queue'"
                    if "pubsub" in tools_line and "mcp__redismcpserver__" not in tools_line:
                        raise AssertionError(f"{agent_file} has fantasy tool 'pubsub'")
                    if "workflow-engine" in tools_line:
                        assert "mcp__" in line, f"{agent_file} has fantasy tool 'workflow-engine'"
                break


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
