"""Tests for CLI shell completion functionality.

Tests dynamic completions for agent names, categories, and shell types.
"""

from unittest.mock import Mock, patch

import click

from mycelium.cli.completion import (
    complete_agent_names,
    complete_categories,
    complete_running_agent_names,
    complete_shell_types,
)
from mycelium.registry.client import AgentInfo


class TestAgentNameCompletion:
    """Test agent name completion."""

    def test_complete_agent_names_returns_all_matching(self) -> None:
        """Test completion returns all agents matching prefix."""
        # Create mock agents
        agents = [
            AgentInfo(name="backend-engineer", category="backend", status="healthy"),
            AgentInfo(name="backend-tester", category="backend", status="healthy"),
            AgentInfo(name="frontend-developer", category="frontend", status="healthy"),
        ]

        with patch("mycelium.cli.completion.RegistryClient") as mock_registry_class:
            mock_registry = Mock()
            mock_registry.list_agents.return_value = agents
            mock_registry_class.return_value = mock_registry

            ctx = Mock(spec=click.Context)
            param = Mock(spec=click.Parameter)

            # Test prefix matching
            results = complete_agent_names(ctx, param, "backend")
            assert results == ["backend-engineer", "backend-tester"]

    def test_complete_agent_names_returns_empty_on_no_match(self) -> None:
        """Test completion returns empty list when no matches."""
        agents = [
            AgentInfo(name="backend-engineer", category="backend", status="healthy"),
        ]

        with patch("mycelium.cli.completion.RegistryClient") as mock_registry_class:
            mock_registry = Mock()
            mock_registry.list_agents.return_value = agents
            mock_registry_class.return_value = mock_registry

            ctx = Mock(spec=click.Context)
            param = Mock(spec=click.Parameter)

            results = complete_agent_names(ctx, param, "notfound")
            assert results == []

    def test_complete_agent_names_handles_registry_error(self) -> None:
        """Test completion handles registry errors gracefully."""
        with patch("mycelium.cli.completion.RegistryClient") as mock_registry_class:
            mock_registry_class.return_value.list_agents.side_effect = Exception("Redis down")

            ctx = Mock(spec=click.Context)
            param = Mock(spec=click.Parameter)

            results = complete_agent_names(ctx, param, "back")
            assert results == []


class TestRunningAgentCompletion:
    """Test running agent name completion."""

    def test_complete_running_agents_filters_by_status(self) -> None:
        """Test completion only returns healthy/starting agents."""
        agents = [
            AgentInfo(name="backend-engineer", category="backend", status="healthy"),
            AgentInfo(name="frontend-developer", category="frontend", status="starting"),
            AgentInfo(name="database-admin", category="infrastructure", status="stopped"),
            AgentInfo(name="api-tester", category="testing", status="unhealthy"),
        ]

        with patch("mycelium.cli.completion.RegistryClient") as mock_registry_class:
            mock_registry = Mock()
            mock_registry.list_agents.return_value = agents
            mock_registry_class.return_value = mock_registry

            ctx = Mock(spec=click.Context)
            param = Mock(spec=click.Parameter)

            results = complete_running_agent_names(ctx, param, "")
            assert set(results) == {"backend-engineer", "frontend-developer"}

    def test_complete_running_agents_with_prefix(self) -> None:
        """Test running agent completion with prefix filter."""
        agents = [
            AgentInfo(name="backend-engineer", category="backend", status="healthy"),
            AgentInfo(name="backend-tester", category="backend", status="healthy"),
            AgentInfo(name="frontend-developer", category="frontend", status="healthy"),
        ]

        with patch("mycelium.cli.completion.RegistryClient") as mock_registry_class:
            mock_registry = Mock()
            mock_registry.list_agents.return_value = agents
            mock_registry_class.return_value = mock_registry

            ctx = Mock(spec=click.Context)
            param = Mock(spec=click.Parameter)

            results = complete_running_agent_names(ctx, param, "backend")
            assert results == ["backend-engineer", "backend-tester"]


class TestCategoryCompletion:
    """Test category completion."""

    def test_complete_categories_returns_unique_categories(self) -> None:
        """Test completion returns unique categories."""
        agents = [
            AgentInfo(name="backend-engineer", category="backend", status="healthy"),
            AgentInfo(name="backend-tester", category="backend", status="healthy"),
            AgentInfo(name="frontend-developer", category="frontend", status="healthy"),
            AgentInfo(name="infra-admin", category="infrastructure", status="healthy"),
        ]

        with patch("mycelium.cli.completion.RegistryClient") as mock_registry_class:
            mock_registry = Mock()
            mock_registry.list_agents.return_value = agents
            mock_registry_class.return_value = mock_registry

            ctx = Mock(spec=click.Context)
            param = Mock(spec=click.Parameter)

            results = complete_categories(ctx, param, "")
            assert set(results) == {"backend", "frontend", "infrastructure"}

    def test_complete_categories_filters_by_prefix(self) -> None:
        """Test category completion filters by prefix."""
        agents = [
            AgentInfo(name="backend-engineer", category="backend", status="healthy"),
            AgentInfo(name="frontend-developer", category="frontend", status="healthy"),
            AgentInfo(name="infra-admin", category="infrastructure", status="healthy"),
        ]

        with patch("mycelium.cli.completion.RegistryClient") as mock_registry_class:
            mock_registry = Mock()
            mock_registry.list_agents.return_value = agents
            mock_registry_class.return_value = mock_registry

            ctx = Mock(spec=click.Context)
            param = Mock(spec=click.Parameter)

            results = complete_categories(ctx, param, "in")
            assert results == ["infrastructure"]


class TestShellTypeCompletion:
    """Test shell type completion."""

    def test_complete_shell_types_returns_all_shells(self) -> None:
        """Test completion returns all supported shells."""
        ctx = Mock(spec=click.Context)
        param = Mock(spec=click.Parameter)

        results = complete_shell_types(ctx, param, "")
        assert results == ["bash", "zsh", "fish"]

    def test_complete_shell_types_filters_by_prefix(self) -> None:
        """Test shell type completion filters by prefix."""
        ctx = Mock(spec=click.Context)
        param = Mock(spec=click.Parameter)

        results = complete_shell_types(ctx, param, "ba")
        assert results == ["bash"]

        results = complete_shell_types(ctx, param, "z")
        assert results == ["zsh"]

    def test_complete_shell_types_handles_no_match(self) -> None:
        """Test shell type completion with no matches."""
        ctx = Mock(spec=click.Context)
        param = Mock(spec=click.Parameter)

        results = complete_shell_types(ctx, param, "invalid")
        assert results == []
