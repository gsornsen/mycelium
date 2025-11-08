#!/usr/bin/env python3
"""Agent Coordination Utility - Report status to Redis MCP.

This utility allows specialized agents to easily report their coordination
status to Redis using the RedisCoordinationHelper. It can be invoked from
any agent to update workload, tasks, and heartbeats.

Usage:
    # Report idle status
    python scripts/agent_coordinator.py report code-reviewer --status idle

    # Report active task
    python scripts/agent_coordinator.py report code-reviewer \
        --status busy \
        --workload 75 \
        --task-id code-review-main \
        --task-desc "Reviewing main application code" \
        --progress 45

    # Update heartbeat
    python scripts/agent_coordinator.py heartbeat code-reviewer

    # Get agent status
    python scripts/agent_coordinator.py get code-reviewer

    # Get all agents
    python scripts/agent_coordinator.py list
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from mycelium_onboarding.coordination.redis_helper import RedisCoordinationHelper
except ImportError as e:
    logger.error(f"Failed to import RedisCoordinationHelper: {e}")
    logger.error("Ensure mycelium_onboarding is in PYTHONPATH")
    sys.exit(1)


class AgentCoordinator:
    """Coordination utility for agents."""

    def __init__(self, redis_client: Any = None):
        """Initialize coordinator.

        Args:
            redis_client: Optional Redis client (will use mock if not provided)
        """
        if redis_client is None:
            # Use mock for demonstration
            from test_coordination_workflow import MockRedisClient

            redis_client = MockRedisClient()

        self.helper = RedisCoordinationHelper(redis_client)

    async def report_status(
        self,
        agent_type: str,
        status: str,
        workload: int = 0,
        task_id: str | None = None,
        task_description: str | None = None,
        progress: int | None = None,
    ) -> bool:
        """Report agent status to Redis.

        Args:
            agent_type: Agent identifier (e.g., "code-reviewer")
            status: Status (idle, busy, completed, error)
            workload: Workload percentage (0-100)
            task_id: Optional task ID
            task_description: Optional task description
            progress: Optional task progress (0-100)

        Returns:
            True if successful
        """
        status_data = {"status": status, "workload": workload, "agent_type": agent_type, "updated_at": datetime.now()}

        if task_id and task_description:
            status_data["current_task"] = {
                "id": task_id,
                "description": task_description,
                "progress": progress or 0,
                "started_at": datetime.now(),
            }
            status_data["task_count"] = 1
        else:
            status_data["current_task"] = None
            status_data["task_count"] = 0

        success = await self.helper.set_agent_status(agent_type, status_data, expire_seconds=3600)

        if success:
            logger.info(f"✓ Status reported for {agent_type}: {status} ({workload}%)")
        else:
            logger.error(f"✗ Failed to report status for {agent_type}")

        return success

    async def update_heartbeat(self, agent_type: str) -> bool:
        """Update agent heartbeat.

        Args:
            agent_type: Agent identifier

        Returns:
            True if successful
        """
        success = await self.helper.update_heartbeat(agent_type)

        if success:
            logger.info(f"✓ Heartbeat updated for {agent_type}")
        else:
            logger.error(f"✗ Failed to update heartbeat for {agent_type}")

        return success

    async def get_status(self, agent_type: str) -> dict[str, Any] | None:
        """Get agent status from Redis.

        Args:
            agent_type: Agent identifier

        Returns:
            Status dictionary or None if not found
        """
        status = await self.helper.get_agent_status(agent_type)

        if status:
            logger.info(f"✓ Retrieved status for {agent_type}")
            print(json.dumps(status, indent=2, default=str))
        else:
            logger.warning(f"⚠ No status found for {agent_type}")

        return status

    async def list_agents(self) -> dict[str, dict[str, Any]]:
        """List all coordinating agents.

        Returns:
            Dictionary of agent statuses
        """
        agents = await self.helper.get_all_agents()

        logger.info(f"✓ Retrieved {len(agents)} agents")

        if agents:
            print("\n=== Coordinating Agents ===\n")
            for agent_type, status in sorted(agents.items()):
                workload = status.get("workload", 0)
                task_count = status.get("task_count", 0)
                agent_status = status.get("status", "unknown")

                print(f"{agent_type:25s} | {agent_status:10s} | {workload:3d}% | {task_count} tasks")
        else:
            print("\n⚠ No agents currently coordinating\n")

        return agents


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Agent Coordination Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Report idle status
  python scripts/agent_coordinator.py report code-reviewer --status idle

  # Report active task
  python scripts/agent_coordinator.py report code-reviewer \\
      --status busy --workload 75 \\
      --task-id code-review-main \\
      --task-desc "Reviewing main application code" \\
      --progress 45

  # Update heartbeat
  python scripts/agent_coordinator.py heartbeat code-reviewer

  # Get agent status
  python scripts/agent_coordinator.py get code-reviewer

  # List all agents
  python scripts/agent_coordinator.py list
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Report status command
    report_parser = subparsers.add_parser("report", help="Report agent status")
    report_parser.add_argument("agent_type", help="Agent type (e.g., code-reviewer)")
    report_parser.add_argument(
        "--status", required=True, choices=["idle", "busy", "completed", "error"], help="Agent status"
    )
    report_parser.add_argument("--workload", type=int, default=0, help="Workload percentage (0-100)")
    report_parser.add_argument("--task-id", help="Task ID")
    report_parser.add_argument("--task-desc", help="Task description")
    report_parser.add_argument("--progress", type=int, help="Task progress (0-100)")

    # Heartbeat command
    heartbeat_parser = subparsers.add_parser("heartbeat", help="Update agent heartbeat")
    heartbeat_parser.add_argument("agent_type", help="Agent type")

    # Get status command
    get_parser = subparsers.add_parser("get", help="Get agent status")
    get_parser.add_argument("agent_type", help="Agent type")

    # List agents command
    subparsers.add_parser("list", help="List all coordinating agents")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize coordinator
    coordinator = AgentCoordinator()

    # Execute command
    if args.command == "report":
        await coordinator.report_status(
            agent_type=args.agent_type,
            status=args.status,
            workload=args.workload,
            task_id=args.task_id,
            task_description=args.task_desc,
            progress=args.progress,
        )

    elif args.command == "heartbeat":
        await coordinator.update_heartbeat(args.agent_type)

    elif args.command == "get":
        await coordinator.get_status(args.agent_type)

    elif args.command == "list":
        await coordinator.list_agents()


if __name__ == "__main__":
    asyncio.run(main())
