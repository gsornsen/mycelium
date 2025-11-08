"""Unit tests for RedisCoordinationHelper."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from mycelium_onboarding.coordination import RedisCoordinationHelper


@pytest.fixture
def mock_redis() -> Mock:
    """Mock Redis client."""
    redis = Mock()
    redis.hset = AsyncMock(return_value={"result": "success"})
    redis.hget = AsyncMock(return_value=None)
    redis.hgetall = AsyncMock(return_value={})
    redis.expire = AsyncMock(return_value={"result": "success"})
    return redis


@pytest.fixture
def helper(mock_redis: Mock, tmp_path: pytest.TempPathFactory) -> RedisCoordinationHelper:
    """Create helper with mocked Redis."""
    return RedisCoordinationHelper(mock_redis, fallback_dir=tmp_path)


class TestSerializationDeserialization:
    """Tests for JSON serialization and deserialization."""

    @pytest.mark.asyncio
    async def test_set_agent_status_with_datetime(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test storing agent status with datetime fields."""
        now = datetime.now()
        status_data = {"status": "busy", "workload": 85, "started_at": now}

        result = await helper.set_agent_status("ai-engineer", status_data)

        assert result is True
        mock_redis.hset.assert_called_once()

        # Verify JSON serialization
        call_args = mock_redis.hset.call_args
        assert call_args.kwargs["name"] == "agents:status"
        assert call_args.kwargs["key"] == "ai-engineer"

        # Verify datetime was serialized
        value = call_args.kwargs["value"]
        assert now.isoformat() in value

    @pytest.mark.asyncio
    async def test_get_agent_status_restores_datetime(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test retrieving agent status restores datetime objects."""
        now = datetime.now()
        stored_data = {"status": "busy", "workload": 85, "started_at": now.isoformat()}

        mock_redis.hget.return_value = helper._serialize_for_redis(stored_data)

        result = await helper.get_agent_status("ai-engineer")

        assert result is not None
        assert result["status"] == "busy"
        assert result["workload"] == 85
        assert isinstance(result["started_at"], datetime)
        assert result["started_at"].isoformat() == now.isoformat()

    def test_serialize_for_redis(self, helper: RedisCoordinationHelper) -> None:
        """Test JSON serialization with datetime objects."""
        now = datetime.now()
        data = {"status": "busy", "started_at": now, "workload": 85}

        serialized = helper._serialize_for_redis(data)

        # Should be valid JSON
        parsed = json.loads(serialized)
        assert parsed["status"] == "busy"
        assert parsed["workload"] == 85
        assert parsed["started_at"] == now.isoformat()

    def test_deserialize_from_redis(self, helper: RedisCoordinationHelper) -> None:
        """Test JSON deserialization with datetime restoration."""
        now = datetime.now()
        data = {"status": "busy", "started_at": now.isoformat(), "updated_at": now.isoformat()}

        json_str = json.dumps(data)
        deserialized = helper._deserialize_from_redis(json_str)

        assert deserialized["status"] == "busy"
        assert isinstance(deserialized["started_at"], datetime)
        assert isinstance(deserialized["updated_at"], datetime)

    def test_deserialize_preserves_non_datetime_strings(self, helper: RedisCoordinationHelper) -> None:
        """Test that non-datetime strings are preserved."""
        data = {"status": "busy", "name": "test-agent", "description": "A timestamp_value here"}

        json_str = json.dumps(data)
        deserialized = helper._deserialize_from_redis(json_str)

        assert deserialized["status"] == "busy"
        assert isinstance(deserialized["name"], str)
        assert isinstance(deserialized["description"], str)


class TestAgentStatus:
    """Tests for agent status operations."""

    @pytest.mark.asyncio
    async def test_set_agent_status_success(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test successful agent status storage."""
        status_data = {"status": "busy", "workload": 85}

        result = await helper.set_agent_status("ai-engineer", status_data)

        assert result is True
        mock_redis.hset.assert_called_once()
        mock_redis.expire.assert_called_once_with(name="agents:status", expire_seconds=3600)

    @pytest.mark.asyncio
    async def test_set_agent_status_custom_expiry(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test agent status storage with custom expiry."""
        status_data = {"status": "busy"}

        result = await helper.set_agent_status("ai-engineer", status_data, expire_seconds=7200)

        assert result is True
        mock_redis.expire.assert_called_once_with(name="agents:status", expire_seconds=7200)

    @pytest.mark.asyncio
    async def test_set_agent_status_no_expiry(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test agent status storage without expiry."""
        status_data = {"status": "busy"}

        result = await helper.set_agent_status("ai-engineer", status_data, expire_seconds=None)

        assert result is True
        mock_redis.expire.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_agent_status_not_found(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test retrieving non-existent agent status."""
        mock_redis.hget.return_value = None

        result = await helper.get_agent_status("ai-engineer")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_agent_status_success(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test successful agent status retrieval."""
        status_data = {"status": "idle", "workload": 0}
        mock_redis.hget.return_value = json.dumps(status_data)

        result = await helper.get_agent_status("ai-engineer")

        assert result is not None
        assert result["status"] == "idle"
        assert result["workload"] == 0


class TestWorkloadManagement:
    """Tests for workload management operations."""

    @pytest.mark.asyncio
    async def test_set_agent_workload(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test storing agent workload with tasks."""
        tasks = [{"id": "task-1", "progress": 50}, {"id": "task-2", "progress": 75}]

        result = await helper.set_agent_workload("ai-engineer", 85, tasks)

        assert result is True
        mock_redis.hset.assert_called_once()

        # Verify stored data structure
        call_args = mock_redis.hset.call_args
        stored_value = json.loads(call_args.kwargs["value"])
        assert stored_value["workload"] == 85
        assert stored_value["task_count"] == 2
        assert len(stored_value["tasks"]) == 2
        assert "updated_at" in stored_value

    @pytest.mark.asyncio
    async def test_set_agent_workload_empty_tasks(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test storing agent workload with empty task list."""
        result = await helper.set_agent_workload("ai-engineer", 0, [])

        assert result is True
        call_args = mock_redis.hset.call_args
        stored_value = json.loads(call_args.kwargs["value"])
        assert stored_value["workload"] == 0
        assert stored_value["task_count"] == 0
        assert stored_value["tasks"] == []


class TestMultiAgentOperations:
    """Tests for multi-agent operations."""

    @pytest.mark.asyncio
    async def test_get_all_agents_handles_mixed_data(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test getting all agents handles both JSON and plain strings."""
        mock_redis.hgetall.return_value = {
            "ai-engineer": '{"status": "busy", "workload": 85}',
            "data-engineer": "100",  # Legacy plain string
        }

        result = await helper.get_all_agents()

        assert len(result) == 2
        assert result["ai-engineer"]["status"] == "busy"
        assert result["data-engineer"]["value"] == 100

    @pytest.mark.asyncio
    async def test_get_all_agents_empty(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test getting all agents when none exist."""
        mock_redis.hgetall.return_value = {}

        result = await helper.get_all_agents()

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_all_agents_redis_error(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test getting all agents when Redis fails."""
        mock_redis.hgetall.side_effect = Exception("Redis error")

        result = await helper.get_all_agents()

        assert result == {}


class TestHeartbeat:
    """Tests for heartbeat operations."""

    @pytest.mark.asyncio
    async def test_heartbeat_update(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test heartbeat update."""
        result = await helper.update_heartbeat("ai-engineer")

        assert result is True
        mock_redis.hset.assert_called_once()

        # Verify heartbeat data structure
        call_args = mock_redis.hset.call_args
        assert call_args.kwargs["name"] == "agents:heartbeat"
        assert call_args.kwargs["key"] == "ai-engineer"

        stored_value = json.loads(call_args.kwargs["value"])
        assert stored_value["agent_type"] == "ai-engineer"
        assert "timestamp" in stored_value

    @pytest.mark.asyncio
    async def test_heartbeat_update_failure(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test heartbeat update failure."""
        mock_redis.hset.side_effect = Exception("Redis error")

        result = await helper.update_heartbeat("ai-engineer")

        assert result is False

    @pytest.mark.asyncio
    async def test_check_heartbeat_freshness_fresh(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test heartbeat freshness check with fresh heartbeat."""
        now = datetime.now()
        heartbeat_data = {"agent_type": "ai-engineer", "timestamp": now.isoformat()}

        mock_redis.hget.return_value = helper._serialize_for_redis(heartbeat_data)

        result = await helper.check_heartbeat_freshness("ai-engineer", max_age_seconds=3600)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_heartbeat_freshness_stale(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test heartbeat freshness check with stale heartbeat."""
        old_time = datetime.now() - timedelta(hours=2)
        heartbeat_data = {"agent_type": "ai-engineer", "timestamp": old_time.isoformat()}

        mock_redis.hget.return_value = helper._serialize_for_redis(heartbeat_data)

        result = await helper.check_heartbeat_freshness("ai-engineer", max_age_seconds=3600)

        assert result is False

    @pytest.mark.asyncio
    async def test_check_heartbeat_freshness_missing(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test heartbeat freshness check when heartbeat is missing."""
        mock_redis.hget.return_value = None

        result = await helper.check_heartbeat_freshness("ai-engineer")

        assert result is False

    @pytest.mark.asyncio
    async def test_check_heartbeat_freshness_invalid_data(
        self, helper: RedisCoordinationHelper, mock_redis: Mock
    ) -> None:
        """Test heartbeat freshness check with invalid timestamp."""
        heartbeat_data = {"agent_type": "ai-engineer", "timestamp": "not-a-datetime"}

        mock_redis.hget.return_value = json.dumps(heartbeat_data)

        result = await helper.check_heartbeat_freshness("ai-engineer")

        assert result is False


class TestMarkdownFallback:
    """Tests for markdown fallback functionality."""

    @pytest.mark.asyncio
    async def test_markdown_fallback_on_redis_failure(
        self, helper: RedisCoordinationHelper, mock_redis: Mock, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Test markdown fallback when Redis fails."""
        mock_redis.hset.side_effect = Exception("Redis error")

        status_data = {"status": "busy", "workload": 85}
        result = await helper.set_agent_status("ai-engineer", status_data)

        # Should still succeed via fallback
        assert result is True

        # Verify markdown file created
        md_file = tmp_path / "agent-ai-engineer.md"
        assert md_file.exists()

        # Read back from markdown (simulate Redis still failing)
        mock_redis.hget.side_effect = Exception("Redis error")
        retrieved = await helper.get_agent_status("ai-engineer")
        assert retrieved is not None
        assert retrieved["status"] == "busy"

    def test_write_markdown_status(self, helper: RedisCoordinationHelper, tmp_path: pytest.TempPathFactory) -> None:
        """Test writing status to markdown file."""
        status_data = {"status": "busy", "workload": 85, "started_at": datetime.now()}

        result = helper._write_markdown_status("ai-engineer", status_data)

        assert result is True
        md_file = tmp_path / "agent-ai-engineer.md"
        assert md_file.exists()

        content = md_file.read_text()
        assert "# Agent: ai-engineer" in content
        assert "## Status Data" in content
        assert "```json" in content

    def test_read_markdown_status(self, helper: RedisCoordinationHelper, tmp_path: pytest.TempPathFactory) -> None:
        """Test reading status from markdown file."""
        status_data = {"status": "busy", "workload": 85}
        helper._write_markdown_status("ai-engineer", status_data)

        result = helper._read_markdown_status("ai-engineer")

        assert result is not None
        assert result["status"] == "busy"
        assert result["workload"] == 85

    def test_read_markdown_status_not_found(
        self, helper: RedisCoordinationHelper, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Test reading non-existent markdown file."""
        result = helper._read_markdown_status("non-existent-agent")

        assert result is None


class TestComplexData:
    """Tests for complex nested data structures."""

    @pytest.mark.asyncio
    async def test_complex_nested_data(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test with complex nested data structures."""
        complex_data = {
            "status": "busy",
            "workload": 85,
            "current_task": {
                "id": "task-123",
                "name": "Train model",
                "progress": 35,
                "steps": {"total": 10000, "completed": 3500},
                "started_at": datetime.now(),
            },
            "metrics": {
                "success_rate": 98.5,
                "avg_duration": 3600,
                "last_success_at": datetime.now() - timedelta(hours=2),
            },
        }

        result = await helper.set_agent_status("ai-engineer", complex_data)
        assert result is True

        # Verify serialization worked
        call_args = mock_redis.hset.call_args
        value = call_args.kwargs["value"]

        # Should be valid JSON
        parsed = json.loads(value)
        assert parsed["workload"] == 85
        assert "started_at" in str(value)

    @pytest.mark.asyncio
    async def test_list_of_tasks_with_timestamps(self, helper: RedisCoordinationHelper, mock_redis: Mock) -> None:
        """Test storing list of tasks with timestamp fields."""
        tasks = [
            {"id": "task-1", "started_at": datetime.now(), "progress": 50},
            {"id": "task-2", "started_at": datetime.now() - timedelta(hours=1), "progress": 75},
        ]

        result = await helper.set_agent_workload("ai-engineer", 85, tasks)
        assert result is True

        # Verify all timestamps serialized
        call_args = mock_redis.hset.call_args
        value = call_args.kwargs["value"]
        parsed = json.loads(value)

        # Check nested datetime objects were serialized
        for task in parsed["tasks"]:
            assert isinstance(task["started_at"], str)  # Should be ISO string
