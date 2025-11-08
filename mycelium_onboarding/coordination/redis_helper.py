"""Redis coordination helper with JSON serialization and datetime handling.

This module provides a high-level interface for storing and retrieving
agent coordination data in Redis with automatic JSON serialization,
datetime conversion, and error handling with markdown fallback.
"""

from __future__ import annotations

import contextlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RedisCoordinationHelper:
    """Helper for Redis-based agent coordination with JSON serialization.

    This class handles:
    - Automatic JSON serialization/deserialization
    - Datetime field conversion (to/from ISO format)
    - Error handling with markdown file fallback
    - Agent status tracking
    - Workload management
    - Heartbeat monitoring

    Example:
        ```python
        helper = RedisCoordinationHelper(redis_client)

        # Store agent status
        await helper.set_agent_status("ai-engineer", {
            "status": "busy",
            "workload": 85,
            "current_task": {"id": "task-123", "progress": 50},
            "started_at": datetime.now()
        })

        # Retrieve with datetime restored
        status = await helper.get_agent_status("ai-engineer")
        print(status["started_at"])  # Returns datetime object
        ```
    """

    def __init__(self, redis_client: Any, fallback_dir: Path | None = None) -> None:
        """Initialize coordination helper.

        Args:
            redis_client: Redis client instance (sync or async)
            fallback_dir: Directory for markdown fallback files (default: .claude/coordination/)
        """
        self.redis = redis_client
        self.fallback_dir = fallback_dir or Path(".claude/coordination")
        self.fallback_dir.mkdir(parents=True, exist_ok=True)

    def _serialize_for_redis(self, data: dict[str, Any]) -> str:
        """Serialize dict to JSON string with datetime handling.

        Converts datetime objects to ISO format strings for JSON compatibility.

        Args:
            data: Dictionary to serialize

        Returns:
            JSON string ready for Redis storage
        """

        def datetime_handler(obj: Any) -> str:
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        return json.dumps(data, default=datetime_handler)

    def _deserialize_from_redis(self, data: str) -> dict[str, Any]:
        """Deserialize JSON string with datetime restoration.

        Automatically converts ISO format strings back to datetime objects
        for fields ending in '_at' or containing 'timestamp'.

        Args:
            data: JSON string from Redis

        Returns:
            Dictionary with datetime objects restored
        """
        parsed = json.loads(data)

        # If parsed value is not a dict (e.g., plain number or string),
        # wrap it in a dict for consistent return type
        if not isinstance(parsed, dict):
            return {"value": parsed}

        # Restore datetime fields
        for key, value in parsed.items():
            if isinstance(value, str) and (key.endswith("_at") or "timestamp" in key.lower()):
                with contextlib.suppress(ValueError):
                    parsed[key] = datetime.fromisoformat(value)

        return parsed

    async def set_agent_status(
        self, agent_type: str, status_data: dict[str, Any], expire_seconds: int | None = 3600
    ) -> bool:
        """Store agent status with automatic JSON serialization.

        Args:
            agent_type: Agent identifier (e.g., "mycelium-core:ai-engineer")
            status_data: Status dictionary (can include datetime objects)
            expire_seconds: TTL for the status (default: 1 hour)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            success = await helper.set_agent_status("ai-engineer", {
                "status": "busy",
                "workload": 85,
                "current_task": {"id": "train-model", "progress": 35},
                "started_at": datetime.now()
            })
            ```
        """
        try:
            serialized = self._serialize_for_redis(status_data)

            # Use MCP hset tool
            await self.redis.hset(name="agents:status", key=agent_type, value=serialized)

            # Set expiration if specified
            if expire_seconds:
                await self.redis.expire(name="agents:status", expire_seconds=expire_seconds)

            logger.debug(f"Stored status for {agent_type}")
            return True

        except Exception as e:
            logger.warning(f"Redis set_agent_status failed: {e}, falling back to markdown")
            return self._write_markdown_status(agent_type, status_data)

    async def get_agent_status(self, agent_type: str) -> dict[str, Any] | None:
        """Retrieve agent status with automatic JSON parsing.

        Args:
            agent_type: Agent identifier

        Returns:
            Status dictionary with datetime objects restored, or None if not found

        Example:
            ```python
            status = await helper.get_agent_status("ai-engineer")
            if status:
                print(f"Agent workload: {status['workload']}%")
                print(f"Started at: {status['started_at']}")
            ```
        """
        try:
            raw_data = await self.redis.hget(name="agents:status", key=agent_type)

            if not raw_data:
                return None

            return self._deserialize_from_redis(raw_data)

        except Exception as e:
            logger.warning(f"Redis get_agent_status failed: {e}, trying markdown fallback")
            return self._read_markdown_status(agent_type)

    async def set_agent_workload(self, agent_type: str, workload: int, tasks: list[dict[str, Any]]) -> bool:
        """Store agent workload and active tasks.

        Args:
            agent_type: Agent identifier
            workload: Workload percentage (0-100)
            tasks: List of active task dictionaries

        Returns:
            True if successful
        """
        workload_data = {
            "workload": workload,
            "task_count": len(tasks),
            "tasks": tasks,
            "updated_at": datetime.now(),
        }

        return await self.set_agent_status(agent_type, workload_data)

    async def get_all_agents(self) -> dict[str, dict[str, Any]]:
        """Get status of all agents.

        Returns:
            Dictionary mapping agent_type to status data

        Example:
            ```python
            agents = await helper.get_all_agents()
            for agent_type, status in agents.items():
                print(f"{agent_type}: {status['workload']}% busy")
            ```
        """
        try:
            all_data = await self.redis.hgetall(name="agents:status")

            result = {}
            for agent_type, raw_data in all_data.items():
                try:
                    result[agent_type] = self._deserialize_from_redis(raw_data)
                except (json.JSONDecodeError, TypeError):
                    # Handle plain string values (legacy data) or invalid JSON
                    result[agent_type] = {"value": raw_data}

            return result

        except Exception as e:
            logger.warning(f"Redis get_all_agents failed: {e}")
            return {}

    async def update_heartbeat(self, agent_type: str) -> bool:
        """Update agent heartbeat timestamp.

        Args:
            agent_type: Agent identifier

        Returns:
            True if successful
        """
        heartbeat_data = {"agent_type": agent_type, "timestamp": datetime.now()}

        try:
            serialized = self._serialize_for_redis(heartbeat_data)
            await self.redis.hset(name="agents:heartbeat", key=agent_type, value=serialized)
            return True
        except Exception as e:
            logger.warning(f"Heartbeat update failed for {agent_type}: {e}")
            return False

    async def check_heartbeat_freshness(self, agent_type: str, max_age_seconds: int = 3600) -> bool:
        """Check if agent heartbeat is fresh.

        Args:
            agent_type: Agent identifier
            max_age_seconds: Maximum acceptable age (default: 1 hour)

        Returns:
            True if heartbeat is fresh, False if stale or missing
        """
        try:
            raw_data = await self.redis.hget(name="agents:heartbeat", key=agent_type)

            if not raw_data:
                return False

            heartbeat = self._deserialize_from_redis(raw_data)
            timestamp = heartbeat.get("timestamp")

            if not isinstance(timestamp, datetime):
                return False

            age = (datetime.now() - timestamp).total_seconds()
            return age <= max_age_seconds

        except Exception:
            return False

    def _write_markdown_status(self, agent_type: str, status_data: dict[str, Any]) -> bool:
        """Fallback: Write status to markdown file.

        Args:
            agent_type: Agent identifier
            status_data: Status data to write

        Returns:
            True if successful
        """
        try:
            file_path = self.fallback_dir / f"agent-{agent_type}.md"

            # Convert datetime objects for markdown
            serializable_data = {}
            for key, value in status_data.items():
                if isinstance(value, datetime):
                    serializable_data[key] = value.isoformat()
                else:
                    serializable_data[key] = value

            content = f"# Agent: {agent_type}\n\n"
            content += f"**Last Updated**: {datetime.now().isoformat()}\n\n"
            content += "## Status Data\n\n"
            content += "```json\n"
            content += json.dumps(serializable_data, indent=2)
            content += "\n```\n"

            file_path.write_text(content)
            logger.info(f"Wrote markdown fallback for {agent_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to write markdown fallback: {e}")
            return False

    def _read_markdown_status(self, agent_type: str) -> dict[str, Any] | None:
        """Fallback: Read status from markdown file.

        Args:
            agent_type: Agent identifier

        Returns:
            Status data or None
        """
        try:
            file_path = self.fallback_dir / f"agent-{agent_type}.md"

            if not file_path.exists():
                return None

            content = file_path.read_text()

            # Extract JSON from code block
            json_match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)

            if json_match:
                return json.loads(json_match.group(1))

            return None

        except Exception as e:
            logger.error(f"Failed to read markdown fallback: {e}")
            return None
