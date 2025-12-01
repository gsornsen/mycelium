"""MCP tool implementations for agent discovery and execution.

Provides core tools:
- discover_agents: Natural language search for agents
- get_agent_details: Get full metadata for a specific agent
- list_categories: List all available agent categories
- invoke_agent: Execute an agent on a task
- get_workflow_status: Check workflow execution status
"""

import contextlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mycelium.config.agent_loader import AgentConfig, AgentLoader


class AgentDiscoveryTools:
    """Agent discovery and execution tools for MCP server."""

    def __init__(self, plugin_dir: Path | None = None) -> None:
        """Initialize discovery tools.

        Args:
            plugin_dir: Directory containing agent .md files.
                       Defaults to plugins/mycelium-core/agents/
        """
        if plugin_dir is None:
            # Default to mycelium-core plugin agents directory
            plugin_dir = Path(__file__).parent.parent.parent.parent / "plugins" / "mycelium-core" / "agents"

        self.loader = AgentLoader(plugin_dir)
        self._process_manager: Any | None = None
        self._registry_client: Any | None = None

    def _get_process_manager(self) -> Any:
        """Lazy-load ProcessManager to avoid circular imports."""
        if self._process_manager is None:
            from mycelium.supervisor.manager import ProcessManager

            self._process_manager = ProcessManager()
        return self._process_manager

    def _get_registry_client(self) -> Any:
        """Lazy-load RegistryClient."""
        if self._registry_client is None:
            from mycelium.registry.client import RegistryClient

            self._registry_client = RegistryClient()
        return self._registry_client

    def discover_agents(self, query: str) -> list[dict[str, Any]]:
        """Search for agents using natural language query.

        Args:
            query: Natural language search query (e.g., "Python backend development")

        Returns:
            List of matching agents with name, category, and description
        """
        # Load all agents
        all_agents = self.loader.list_agents()

        # Simple keyword-based matching
        # TODO: In future, use sentence transformers for semantic search
        query_lower = query.lower()
        matches: list[AgentConfig] = []

        for agent in all_agents:
            # Search in name, description, and tools
            searchable_text = " ".join(
                [
                    agent.name,
                    agent.description,
                    agent.category,
                    " ".join(agent.tools or []),
                ]
            ).lower()

            if query_lower in searchable_text:
                matches.append(agent)

        # Convert to response format
        return [
            {
                "name": agent.name,
                "category": agent.category,
                "description": agent.description,
            }
            for agent in matches
        ]

    def get_agent_details(self, name: str) -> dict[str, Any] | None:
        """Get full metadata for a specific agent.

        Args:
            name: Agent name (e.g., "backend-developer")

        Returns:
            Full agent info including tools, description, category, or None if not found
        """
        agent = self.loader.load_agent(name)

        if not agent:
            return None

        return {
            "name": agent.name,
            "category": agent.category,
            "description": agent.description,
            "tools": agent.tools or [],
            "command": agent.command,
        }

    def list_categories(self) -> list[dict[str, Any]]:
        """List all available agent categories with counts.

        Returns:
            List of category names with agent counts
        """
        all_agents = self.loader.list_agents()

        # Count agents per category
        category_counts: dict[str, int] = {}
        for agent in all_agents:
            category_counts[agent.category] = category_counts.get(agent.category, 0) + 1

        # Convert to response format
        return [
            {
                "category": category,
                "count": count,
            }
            for category, count in sorted(category_counts.items())
        ]

    def invoke_agent(
        self, agent_name: str, task_description: str, _context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Invoke an agent to execute a task.

        Args:
            agent_name: Name of agent to invoke
            task_description: Task for the agent to execute
            _context: Optional context dictionary (reserved for future use)

        Returns:
            Dictionary with:
            - workflow_id: Unique workflow identifier
            - status: "started" | "failed"
            - agent_name: Name of invoked agent
            - message: Status message
        """
        # Validate agent exists
        agent_config = self.loader.load_agent(agent_name)
        if not agent_config:
            return {
                "workflow_id": None,
                "status": "failed",
                "agent_name": agent_name,
                "message": f"Agent '{agent_name}' not found",
                "error": "AGENT_NOT_FOUND",
            }

        # Check agent risk level and get consent if needed
        try:
            from mycelium.mcp.consent import ConsentManager
            from mycelium.mcp.permissions import get_agent_risk_level, parse_agent_tools

            # Find agent file
            agent_files = list(self.loader.plugin_dir.glob(f"*{agent_name}.md"))
            if not agent_files:
                risk_level = "unknown"
                agent_path = None
            else:
                agent_path = agent_files[0]
                risk_level = get_agent_risk_level(agent_path)

                # If high-risk, check/request consent
                if risk_level == "high":
                    consent_mgr = ConsentManager()

                    # Check existing consent
                    if not consent_mgr.check_consent(agent_name, agent_path, risk_level):
                        # Request consent from user
                        tools = parse_agent_tools(agent_path)
                        if not consent_mgr.request_consent(agent_name, agent_path, risk_level, tools):
                            return {
                                "workflow_id": None,
                                "status": "failed",
                                "agent_name": agent_name,
                                "message": "User denied consent for high-risk agent",
                                "error": "CONSENT_DENIED",
                                "risk_level": risk_level,
                            }

        except Exception:
            # If consent check fails, proceed with caution
            risk_level = "unknown"

        # Generate workflow ID
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"

        # Start the agent process
        try:
            manager = self._get_process_manager()
            pid = manager.start_agent(agent_name)

            # Store workflow state in registry
            registry = self._get_registry_client()
            workflow_key = f"mycelium:workflows:{workflow_id}"

            # Would use Redis MCP tools in production:
            # mcp__RedisMCPServer__hset(workflow_key, "workflow_id", workflow_id)
            # mcp__RedisMCPServer__hset(workflow_key, "agent_name", agent_name)
            # mcp__RedisMCPServer__hset(workflow_key, "task", task_description)
            # mcp__RedisMCPServer__hset(workflow_key, "status", "running")
            # mcp__RedisMCPServer__hset(workflow_key, "started_at", datetime.now(timezone.utc).isoformat())
            # mcp__RedisMCPServer__hset(workflow_key, "pid", str(pid))

            # For now, store in Redis via client
            with contextlib.suppress(Exception):
                registry._redis_store_hash(
                    workflow_key,
                    {
                        "workflow_id": workflow_id,
                        "agent_name": agent_name,
                        "task": task_description,
                        "status": "running",
                        "started_at": datetime.now(timezone.utc).isoformat(),
                        "pid": pid,
                        "risk_level": risk_level,
                    },
                )

            return {
                "workflow_id": workflow_id,
                "status": "started",
                "agent_name": agent_name,
                "pid": pid,
                "message": f"Agent '{agent_name}' started successfully",
                "risk_level": risk_level,
            }

        except Exception as e:
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "agent_name": agent_name,
                "message": f"Failed to start agent: {str(e)}",
                "error": str(e),
            }

    def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
        """Get status of a running workflow.

        Args:
            workflow_id: Workflow identifier from invoke_agent

        Returns:
            Dictionary with:
            - workflow_id: Workflow identifier
            - status: "running" | "completed" | "failed" | "not_found"
            - agent_name: Name of agent
            - started_at: ISO timestamp
            - completed_at: ISO timestamp (if completed)
            - result: Execution result (if completed)
            - error: Error message (if failed)
        """
        # Query workflow state from Redis
        registry = self._get_registry_client()
        workflow_key = f"mycelium:workflows:{workflow_id}"

        try:
            workflow_data = registry._redis_get_hash(workflow_key)

            if not workflow_data or not workflow_data.get("workflow_id"):
                return {
                    "workflow_id": workflow_id,
                    "status": "not_found",
                    "message": f"Workflow '{workflow_id}' not found",
                }

            agent_name = str(workflow_data.get("agent_name", ""))

            # Check process status via ProcessManager
            manager = self._get_process_manager()
            process_status = manager.get_process_status(agent_name)

            # Determine workflow status
            if process_status.get("status") == "running":
                status = "running"
            elif process_status.get("status") == "stopped":
                exit_code = process_status.get("exit_code", 0)
                status = "completed" if exit_code == 0 else "failed"
            else:
                status = workflow_data.get("status", "unknown")

            result = {
                "workflow_id": workflow_id,
                "status": status,
                "agent_name": agent_name,
                "started_at": workflow_data.get("started_at"),
                "task": workflow_data.get("task"),
            }

            if status in ("completed", "failed"):
                result["completed_at"] = datetime.now(timezone.utc).isoformat()

                if status == "failed":
                    result["error"] = workflow_data.get("error", "Agent process failed")
                    result["exit_code"] = process_status.get("exit_code")

            return result

        except Exception as e:
            return {
                "workflow_id": workflow_id,
                "status": "error",
                "message": f"Failed to query workflow status: {str(e)}",
                "error": str(e),
            }
