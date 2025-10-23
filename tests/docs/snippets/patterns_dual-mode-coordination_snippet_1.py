# Source: patterns/dual-mode-coordination.md
# Line: 414
# Valid syntax: True
# Has imports: True
# Has assignments: True

from unittest.mock import patch

import pytest


class TestCoordination:
    @pytest.fixture(params=["redis", "taskqueue", "markdown"])
    def coordination_mode(self, request):
        return request.param

    async def test_store_agent_status(self, coordination_mode):
        status = {
            "agent_type": "ai-engineer",
            "status": "busy",
            "last_updated": "2025-10-12T14:30:00Z"
        }

        if coordination_mode == "redis":
            # Test Redis path
            with patch("mcp__RedisMCPServer__json_set") as mock:
                await store_agent_status("ai-engineer", status)
                assert mock.called

        elif coordination_mode == "taskqueue":
            # Test TaskQueue path
            with patch("mcp__taskqueue__create_task") as mock:
                await store_agent_status("ai-engineer", status)
                assert mock.called

        elif coordination_mode == "markdown":
            # Test markdown path
            with patch("builtins.open") as mock:
                await store_agent_status("ai-engineer", status)
                assert mock.called
