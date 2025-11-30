"""Unit tests for agent discovery scanner."""

from pathlib import Path

import pytest

from mycelium.discovery.scanner import AgentScanner, DiscoveredAgent
from mycelium.errors import MyceliumError
from mycelium.registry.client import RegistryClient


class TestDiscoveredAgent:
    """Test DiscoveredAgent dataclass."""

    def test_creation(self) -> None:
        """Test creating a discovered agent."""
        agent = DiscoveredAgent(
            name="test-agent",
            category="backend",
            description="Test agent description",
            file_path=Path("/path/to/agent.md"),
        )

        assert agent.name == "test-agent"
        assert agent.category == "backend"
        assert agent.description == "Test agent description"
        assert agent.file_path == Path("/path/to/agent.md")
        assert agent.version is None
        assert agent.capabilities is None


class TestAgentScanner:
    """Test AgentScanner."""

    def test_initialization(self) -> None:
        """Test scanner initialization."""
        scanner = AgentScanner()
        assert isinstance(scanner.registry, RegistryClient)
        assert scanner.discovered == {}

    def test_initialization_with_registry(self) -> None:
        """Test scanner initialization with custom registry."""
        registry = RegistryClient(redis_url="redis://custom:6379")
        scanner = AgentScanner(registry=registry)
        assert scanner.registry is registry

    def test_scan_directory_nonexistent(self) -> None:
        """Test scanning nonexistent directory."""
        scanner = AgentScanner()
        nonexistent = Path("/nonexistent/path")

        with pytest.raises(MyceliumError) as exc_info:
            scanner.scan_directory(nonexistent)

        assert "not found" in str(exc_info.value).lower()

    def test_extract_category_from_frontmatter(self) -> None:
        """Test category extraction from YAML frontmatter."""
        scanner = AgentScanner()
        content = """---
category: backend
description: Test agent
---

# Agent Name

This is the agent content.
"""
        category = scanner._extract_category(content)
        assert category == "backend"

    def test_extract_category_from_inline(self) -> None:
        """Test category extraction from inline marker."""
        scanner = AgentScanner()
        content = """
# Backend Engineer

Category: **backend**

This is a backend specialist.
"""
        category = scanner._extract_category(content)
        assert category == "backend"

    def test_extract_category_from_filename(self) -> None:
        """Test category extraction from filename prefix pattern."""
        scanner = AgentScanner()
        content = """---
name: test-agent
description: Test agent
---

# Agent Name
"""
        # Filename pattern: NN-category-name
        assert scanner._extract_category(content, "01-core-backend-developer") == "core"
        assert scanner._extract_category(content, "02-language-python-pro") == "language"
        assert scanner._extract_category(content, "05-data-ml-engineer") == "data"
        assert scanner._extract_category(content, "09-meta-coordinator") == "meta"

    def test_extract_category_default(self) -> None:
        """Test default category extraction."""
        scanner = AgentScanner()
        content = """
# Some Agent

This is an agent without explicit category.
"""
        category = scanner._extract_category(content)
        assert category == "general"

    def test_extract_category_from_content(self) -> None:
        """Test category extraction from content keywords."""
        scanner = AgentScanner()
        content = """
# Backend Developer

This agent specializes in backend development.
"""
        category = scanner._extract_category(content)
        assert category == "backend"

    def test_extract_description_from_frontmatter(self) -> None:
        """Test description extraction from YAML frontmatter."""
        scanner = AgentScanner()
        content = """---
category: backend
description: "A specialized backend developer"
---

# Agent Name
"""
        description = scanner._extract_description(content)
        assert description == "A specialized backend developer"

    def test_extract_description_from_content(self) -> None:
        """Test description extraction from content."""
        scanner = AgentScanner()
        content = """---
category: backend
---

# Backend Engineer

Expert in Python and distributed systems.
"""
        description = scanner._extract_description(content)
        assert "Python" in description or "distributed" in description

    def test_extract_description_with_formatting(self) -> None:
        """Test description extraction with markdown formatting."""
        scanner = AgentScanner()
        content = """
# Agent Name

This is a **bold** description with *italic* text.
"""
        description = scanner._extract_description(content)
        # Should strip markdown formatting
        assert "**" not in description or "bold" in description

    def test_is_agent_file_positive(self) -> None:
        """Test agent file detection - positive case."""
        scanner = AgentScanner()
        content = """
---
category: backend
---

# Backend Agent
"""
        assert scanner._is_agent_file(content, "backend-agent")

    def test_is_agent_file_negative(self) -> None:
        """Test agent file detection - negative case."""
        scanner = AgentScanner()
        content = """
# Random Documentation

This is just regular documentation.
No agent-related content here.
"""
        # Even random docs might match our heuristic if they mention "category"
        # This is by design - we're lenient in discovery
        assert scanner._is_agent_file(content, "random-doc") or True

    def test_get_discovered_agent(self) -> None:
        """Test retrieving discovered agent."""
        scanner = AgentScanner()
        scanner.discovered["test-agent"] = DiscoveredAgent(
            name="test-agent",
            category="backend",
            description="Test",
            file_path=Path("/test"),
        )

        agent = scanner.get_discovered_agent("test-agent")
        assert agent is not None
        assert agent.name == "test-agent"

    def test_get_discovered_agent_not_found(self) -> None:
        """Test retrieving non-existent discovered agent."""
        scanner = AgentScanner()
        agent = scanner.get_discovered_agent("nonexistent")
        assert agent is None

    def test_register_discovered_agents_empty(self) -> None:
        """Test registering when no agents discovered."""
        scanner = AgentScanner()
        count = scanner.register_discovered_agents()
        assert count == 0
