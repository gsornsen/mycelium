"""Redis-backed agent registry client.

Manages agent discovery, registration, and heartbeat tracking.
Uses Redis for coordination per user instructions.
"""

import json
from typing import Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from mycelium.errors import RegistryError


@dataclass
class AgentInfo:
    """Agent registration information."""

    name: str
    category: str
    status: str  # "healthy", "unhealthy", "starting", "stopping"
    pid: Optional[int] = None
    port: Optional[int] = None
    description: Optional[str] = None
    last_heartbeat: Optional[str] = None
    started_at: Optional[str] = None

    def to_dict(self) -> dict[str, str | int | None]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, str | int | None]) -> "AgentInfo":
        """Create from dictionary."""
        pid_val = data.get("pid")
        port_val = data.get("port")
        return cls(
            name=str(data.get("name", "")),
            category=str(data.get("category", "")),
            status=str(data.get("status", "unknown")),
            pid=int(pid_val) if pid_val is not None else None,
            port=int(port_val) if port_val is not None else None,
            description=str(data["description"]) if data.get("description") else None,
            last_heartbeat=str(data["last_heartbeat"]) if data.get("last_heartbeat") else None,
            started_at=str(data["started_at"]) if data.get("started_at") else None,
        )


class RegistryClient:
    """Client for interacting with agent registry.

    Uses Redis for storage and coordination via MCP tools.
    Follows DX requirements: zero-friction start, clear errors.

    Storage schema:
    - Agent data: mycelium:agents:{name} (hash with all fields)
    - Agent list: mycelium:agent_names (set of agent names)
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize registry client.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self._redis_client: Optional["redis.Redis[str]"] = None
        self._connected = False

    def _ensure_connection(self) -> None:
        """Ensure Redis connection is established."""
        if self._connected and self._redis_client:
            return

        if not REDIS_AVAILABLE:
            raise RegistryError(
                "Redis library not available",
                suggestion="Install redis: uv add redis",
                docs_url="https://docs.mycelium.dev/setup/redis",
            )

        try:
            self._redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
            )
            # Test connection
            self._redis_client.ping()
            self._connected = True
        except Exception as e:
            raise RegistryError(
                "Failed to connect to agent registry",
                suggestion="Ensure Redis is running: redis-cli ping",
                docs_url="https://docs.mycelium.dev/setup/redis",
                debug_info={"redis_url": self.redis_url, "error": str(e)}
            )

    def register_agent(
        self,
        name: str,
        category: str,
        pid: Optional[int] = None,
        port: Optional[int] = None,
        description: Optional[str] = None,
    ) -> AgentInfo:
        """Register an agent in the registry.

        Stores agent data in Redis hash at mycelium:agents:{name}
        and adds name to mycelium:agent_names set.

        Args:
            name: Agent name
            category: Agent category
            pid: Process ID
            port: Port number
            description: Agent description

        Returns:
            Registered agent info
        """
        self._ensure_connection()

        agent = AgentInfo(
            name=name,
            category=category,
            status="starting",
            pid=pid,
            port=port,
            description=description,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        # Store agent data in Redis hash
        # In actual usage, this would call MCP tools:
        # from antml.invoke import mcp__RedisMCPServer__hset
        # For each field in agent.to_dict():
        #   mcp__RedisMCPServer__hset(f"mycelium:agents:{name}", field, value)
        #
        # For Phase 0.5, we implement a placeholder that can be wired up
        # when MCP tools are available in the runtime context

        agent_key = f"mycelium:agents:{name}"
        agent_data = agent.to_dict()

        # Store each field (would use MCP in production)
        # This is a marker for where MCP integration happens
        self._redis_store_hash(agent_key, agent_data)
        self._redis_add_to_set("mycelium:agent_names", name)

        return agent

    def update_heartbeat(self, name: str) -> None:
        """Update agent heartbeat timestamp.

        Args:
            name: Agent name
        """
        self._ensure_connection()

        timestamp = datetime.now(timezone.utc).isoformat()
        agent_key = f"mycelium:agents:{name}"

        # Update last_heartbeat field in Redis
        # mcp__RedisMCPServer__hset(agent_key, "last_heartbeat", timestamp)
        self._redis_update_field(agent_key, "last_heartbeat", timestamp)

    def get_agent(self, name: str) -> Optional[AgentInfo]:
        """Get agent information.

        Args:
            name: Agent name

        Returns:
            Agent info or None if not found
        """
        self._ensure_connection()

        agent_key = f"mycelium:agents:{name}"

        # Retrieve from Redis
        # data = mcp__RedisMCPServer__hgetall(agent_key)
        data = self._redis_get_hash(agent_key)

        if not data or not data.get("name"):
            return None

        return AgentInfo.from_dict(data)

    def list_agents(self, category: Optional[str] = None) -> list[AgentInfo]:
        """List registered agents.

        Args:
            category: Optional category filter

        Returns:
            List of agent info
        """
        self._ensure_connection()

        # Get all agent names from set
        # agent_names = mcp__RedisMCPServer__smembers("mycelium:agent_names")
        agent_names = self._redis_get_set_members("mycelium:agent_names")

        agents = []
        for name in agent_names:
            agent = self.get_agent(name)
            if agent:
                # Filter by category if specified
                if category is None or agent.category == category:
                    agents.append(agent)

        return agents

    def unregister_agent(self, name: str) -> None:
        """Unregister an agent.

        Args:
            name: Agent name
        """
        self._ensure_connection()

        agent_key = f"mycelium:agents:{name}"

        # Remove from Redis
        # mcp__RedisMCPServer__delete(agent_key)
        # mcp__RedisMCPServer__srem("mycelium:agent_names", name)
        self._redis_delete_key(agent_key)
        self._redis_remove_from_set("mycelium:agent_names", name)

    def health_check(self) -> bool:
        """Check if registry is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            self._ensure_connection()
            # Ping Redis via MCP
            # For Phase 0.5, we'll check if we can read the agent_names set
            self._redis_get_set_members("mycelium:agent_names")
            return True
        except Exception:
            return False

    def get_stats(self) -> dict[str, int]:
        """Get registry statistics.

        Returns:
            Statistics dictionary
        """
        self._ensure_connection()

        agents = self.list_agents()
        active = [a for a in agents if a.status == "healthy"]

        return {
            "agent_count": len(agents),
            "active_count": len(active),
        }

    # Internal Redis operation wrappers

    def _redis_store_hash(self, key: str, data: dict[str, str | int | None]) -> None:
        """Store hash data in Redis."""
        if not self._redis_client:
            return
        # Convert None values to empty strings for Redis
        clean_data: dict[str, str | int] = {
            k: ("" if v is None else v) for k, v in data.items()
        }
        self._redis_client.hset(key, mapping=clean_data)

    def _redis_update_field(self, key: str, field: str, value: str) -> None:
        """Update single field in Redis hash."""
        if not self._redis_client:
            return
        self._redis_client.hset(key, field, value)

    def _redis_get_hash(self, key: str) -> dict[str, str | int | None]:
        """Get hash from Redis."""
        if not self._redis_client:
            return {}
        data = self._redis_client.hgetall(key)
        # Convert empty strings back to None for optional fields
        result: dict[str, str | int | None] = {}
        for k, v in data.items():
            if v == "":
                result[k] = None
            elif k in ("pid", "port") and v.isdigit():
                result[k] = int(v)
            else:
                result[k] = v
        return result

    def _redis_add_to_set(self, key: str, value: str) -> None:
        """Add to Redis set."""
        if not self._redis_client:
            return
        self._redis_client.sadd(key, value)

    def _redis_get_set_members(self, key: str) -> list[str]:
        """Get set members from Redis."""
        if not self._redis_client:
            return []
        members = self._redis_client.smembers(key)
        return list(members) if members else []

    def _redis_remove_from_set(self, key: str, value: str) -> None:
        """Remove from Redis set."""
        if not self._redis_client:
            return
        self._redis_client.srem(key, value)

    def _redis_delete_key(self, key: str) -> None:
        """Delete key from Redis."""
        if not self._redis_client:
            return
        self._redis_client.delete(key)
