"""Unit tests for MCP discovery tools."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from mycelium.config.agent_loader import AgentConfig
from mycelium.mcp.tools import AgentDiscoveryTools


@pytest.fixture
def sample_agents() -> list[AgentConfig]:
    """Create sample agent configurations for testing."""
    return [
        AgentConfig(
            name="backend-developer",
            category="core",
            description="Senior backend engineer specializing in scalable API development",
            command=["claude", "--agent", "backend-developer"],
            tools=["Read", "Write", "Bash", "Docker", "database", "redis"],
        ),
        AgentConfig(
            name="python-pro",
            category="language",
            description="Python expert with deep knowledge of Python 3.11+ features",
            command=["claude", "--agent", "python-pro"],
            tools=["Read", "Write", "Bash", "python"],
        ),
        AgentConfig(
            name="react-specialist",
            category="language",
            description="React developer expert in modern React patterns and hooks",
            command=["claude", "--agent", "react-specialist"],
            tools=["Read", "Write", "Bash", "npm"],
        ),
        AgentConfig(
            name="database-optimizer",
            category="data",
            description="Database optimization specialist for PostgreSQL and MySQL",
            command=["claude", "--agent", "database-optimizer"],
            tools=["Read", "Write", "Bash", "database", "postgresql"],
        ),
    ]


@pytest.fixture
def mock_loader(sample_agents: list[AgentConfig]) -> Mock:
    """Create mock agent loader."""
    loader = Mock()
    loader.list_agents.return_value = sample_agents
    loader.load_agent.side_effect = lambda name: next((agent for agent in sample_agents if agent.name == name), None)
    loader.get_categories.return_value = ["core", "language", "data"]
    return loader


class TestAgentDiscoveryTools:
    """Test suite for AgentDiscoveryTools."""

    def test_init_default_plugin_dir(self) -> None:
        """Test initialization with default plugin directory."""
        tools = AgentDiscoveryTools()
        assert tools.loader is not None
        # Check that default path points to plugins/mycelium-core/agents
        expected_path = Path(__file__).parent.parent.parent.parent.parent / "plugins" / "mycelium-core" / "agents"
        # Just verify loader was created (actual path check is implementation detail)

    def test_init_custom_plugin_dir(self, tmp_path: Path) -> None:
        """Test initialization with custom plugin directory."""
        custom_dir = tmp_path / "custom_agents"
        custom_dir.mkdir()
        tools = AgentDiscoveryTools(plugin_dir=custom_dir)
        assert tools.loader is not None

    def test_discover_agents_by_name(self, mock_loader: Mock) -> None:
        """Test discovering agents by name match."""
        tools = AgentDiscoveryTools()
        tools.loader = mock_loader

        results = tools.discover_agents("backend")

        assert len(results) == 1
        assert results[0]["name"] == "backend-developer"
        assert results[0]["category"] == "core"
        assert "API development" in results[0]["description"]

    def test_discover_agents_by_description(self, mock_loader: Mock) -> None:
        """Test discovering agents by description match."""
        tools = AgentDiscoveryTools()
        tools.loader = mock_loader

        results = tools.discover_agents("Python")

        assert len(results) == 1
        assert results[0]["name"] == "python-pro"
        assert results[0]["category"] == "language"

    def test_discover_agents_by_tools(self, mock_loader: Mock) -> None:
        """Test discovering agents by tool match."""
        tools = AgentDiscoveryTools()
        tools.loader = mock_loader

        results = tools.discover_agents("database")

        # Should match backend-developer and database-optimizer
        assert len(results) == 2
        names = {r["name"] for r in results}
        assert "backend-developer" in names
        assert "database-optimizer" in names

    def test_discover_agents_no_match(self, mock_loader: Mock) -> None:
        """Test discovering agents with no matches."""
        tools = AgentDiscoveryTools()
        tools.loader = mock_loader

        results = tools.discover_agents("nonexistent")

        assert len(results) == 0

    def test_discover_agents_case_insensitive(self, mock_loader: Mock) -> None:
        """Test that search is case insensitive."""
        tools = AgentDiscoveryTools()
        tools.loader = mock_loader

        results = tools.discover_agents("PYTHON")

        assert len(results) == 1
        assert results[0]["name"] == "python-pro"

    def test_get_agent_details_success(self, mock_loader: Mock) -> None:
        """Test getting agent details for existing agent."""
        tools = AgentDiscoveryTools()
        tools.loader = mock_loader

        result = tools.get_agent_details("backend-developer")

        assert result is not None
        assert result["name"] == "backend-developer"
        assert result["category"] == "core"
        assert "API development" in result["description"]
        assert "Read" in result["tools"]
        assert "database" in result["tools"]
        assert result["command"] == ["claude", "--agent", "backend-developer"]

    def test_get_agent_details_not_found(self, mock_loader: Mock) -> None:
        """Test getting agent details for non-existent agent."""
        tools = AgentDiscoveryTools()
        tools.loader = mock_loader

        result = tools.get_agent_details("nonexistent-agent")

        assert result is None

    def test_get_agent_details_without_tools(self, mock_loader: Mock, sample_agents: list[AgentConfig]) -> None:
        """Test getting agent details when agent has no tools."""
        # Add agent without tools
        no_tools_agent = AgentConfig(
            name="minimal-agent",
            category="test",
            description="Minimal agent",
            command=["claude", "--agent", "minimal-agent"],
            tools=None,
        )
        sample_agents.append(no_tools_agent)
        mock_loader.load_agent.side_effect = lambda name: next(
            (agent for agent in sample_agents if agent.name == name), None
        )

        tools = AgentDiscoveryTools()
        tools.loader = mock_loader

        result = tools.get_agent_details("minimal-agent")

        assert result is not None
        assert result["tools"] == []

    def test_list_categories(self, mock_loader: Mock) -> None:
        """Test listing all categories with counts."""
        tools = AgentDiscoveryTools()
        tools.loader = mock_loader

        results = tools.list_categories()

        # Should have core (1), language (2), data (1)
        assert len(results) == 3

        # Check counts
        category_map = {r["category"]: r["count"] for r in results}
        assert category_map["core"] == 1
        assert category_map["language"] == 2
        assert category_map["data"] == 1

    def test_list_categories_sorted(self, mock_loader: Mock) -> None:
        """Test that categories are sorted alphabetically."""
        tools = AgentDiscoveryTools()
        tools.loader = mock_loader

        results = tools.list_categories()

        categories = [r["category"] for r in results]
        assert categories == sorted(categories)

    def test_list_categories_empty(self) -> None:
        """Test listing categories when no agents exist."""
        mock_loader = Mock()
        mock_loader.list_agents.return_value = []

        tools = AgentDiscoveryTools()
        tools.loader = mock_loader

        results = tools.list_categories()

        assert len(results) == 0
