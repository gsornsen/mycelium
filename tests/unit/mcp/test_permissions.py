"""Unit tests for tool permissions module."""

import pytest

from mycelium.mcp.permissions import (
    ToolPermission,
    analyze_tool_permissions,
    generate_permissions_report,
    get_agent_permissions,
    get_agent_risk_level,
    get_high_risk_agents,
    parse_agent_tools,
)


@pytest.fixture
def temp_plugin_dir(tmp_path):
    """Create temporary plugin directory structure."""
    plugin_dir = tmp_path / "test-plugin"
    agents_dir = plugin_dir / "agents"
    agents_dir.mkdir(parents=True)
    return plugin_dir


@pytest.fixture
def temp_agent_dir(temp_plugin_dir):
    """Get the agents directory."""
    return temp_plugin_dir / "agents"


@pytest.fixture
def high_risk_agent(temp_agent_dir):
    """Create a high-risk agent file."""
    agent_file = temp_agent_dir / "high-risk-agent.md"
    content = """---
name: high-risk-agent
description: Agent with unrestricted access
tools: Read, Write, MultiEdit, Bash, Docker
---

This is a high-risk agent with unrestricted shell and file access.
"""
    agent_file.write_text(content)
    return agent_file


@pytest.fixture
def medium_risk_agent(temp_agent_dir):
    """Create a medium-risk agent file."""
    agent_file = temp_agent_dir / "medium-risk-agent.md"
    content = """---
name: medium-risk-agent
description: Agent with read-only and container access
tools: Read, Docker, kubernetes, redis
---

This is a medium-risk agent with container access.
"""
    agent_file.write_text(content)
    return agent_file


@pytest.fixture
def low_risk_agent(temp_agent_dir):
    """Create a low-risk agent file with only restricted tools."""
    agent_file = temp_agent_dir / "low-risk-agent.md"
    content = """---
name: low-risk-agent
description: Agent with restricted access
tools: Bash(git:*), vite, jest, typescript
---

This is a low-risk agent with restricted shell access.
"""
    agent_file.write_text(content)
    return agent_file


@pytest.fixture
def safe_agent(temp_agent_dir):
    """Create a safe agent file with no risky tools."""
    agent_file = temp_agent_dir / "safe-agent.md"
    content = """---
name: safe-agent
description: Agent with only safe tools
tools: vite, jest, typescript, eslint, prettier
---

This is a safe agent with no shell or file write access.
"""
    agent_file.write_text(content)
    return agent_file


class TestParseAgentTools:
    """Tests for parse_agent_tools function."""

    def test_parse_tools_comma_separated(self, high_risk_agent):
        """Test parsing comma-separated tools."""
        tools = parse_agent_tools(high_risk_agent)
        assert tools == ["Read", "Write", "MultiEdit", "Bash", "Docker"]

    def test_parse_tools_with_patterns(self, low_risk_agent):
        """Test parsing tools with restricted patterns."""
        tools = parse_agent_tools(low_risk_agent)
        assert "Bash(git:*)" in tools

    def test_parse_tools_empty(self, temp_agent_dir):
        """Test parsing agent with no tools."""
        agent_file = temp_agent_dir / "no-tools.md"
        content = """---
name: no-tools
description: Agent with no tools
tools:
---

Agent content.
"""
        agent_file.write_text(content)
        tools = parse_agent_tools(agent_file)
        assert tools == []

    def test_parse_tools_missing_frontmatter(self, temp_agent_dir):
        """Test parsing file with no frontmatter."""
        agent_file = temp_agent_dir / "no-frontmatter.md"
        agent_file.write_text("Just content, no frontmatter.")

        with pytest.raises(ValueError, match="No frontmatter found"):
            parse_agent_tools(agent_file)

    def test_parse_tools_invalid_yaml(self, temp_agent_dir):
        """Test parsing file with invalid YAML."""
        agent_file = temp_agent_dir / "invalid-yaml.md"
        content = """---
name: invalid
tools: [unclosed list
---

Content.
"""
        agent_file.write_text(content)

        with pytest.raises(ValueError, match="Invalid YAML"):
            parse_agent_tools(agent_file)

    def test_parse_tools_nonexistent_file(self, temp_agent_dir):
        """Test parsing nonexistent file."""
        agent_file = temp_agent_dir / "nonexistent.md"

        with pytest.raises(ValueError, match="not found"):
            parse_agent_tools(agent_file)

    def test_parse_tools_list_format(self, temp_agent_dir):
        """Test parsing tools as YAML list."""
        agent_file = temp_agent_dir / "list-tools.md"
        content = """---
name: list-tools
tools:
  - Read
  - Write
  - Bash
---

Content.
"""
        agent_file.write_text(content)
        tools = parse_agent_tools(agent_file)
        assert set(tools) == {"Read", "Write", "Bash"}


class TestAnalyzeToolPermissions:
    """Tests for analyze_tool_permissions function."""

    def test_analyze_high_risk_tools(self):
        """Test analyzing high-risk tools."""
        tools = ["Bash", "Write", "Edit"]
        permissions = analyze_tool_permissions(tools)

        assert len(permissions) == 3
        assert all(p.risk_level == "high" for p in permissions)
        assert all(isinstance(p, ToolPermission) for p in permissions)

    def test_analyze_medium_risk_tools(self):
        """Test analyzing medium-risk tools."""
        tools = ["Read", "Docker", "kubernetes"]
        permissions = analyze_tool_permissions(tools)

        assert len(permissions) == 3
        read_perm = next(p for p in permissions if p.tool_name == "Read")
        assert read_perm.risk_level == "medium"

    def test_analyze_low_risk_tools(self):
        """Test analyzing low-risk tools."""
        tools = ["vite", "jest", "typescript"]
        permissions = analyze_tool_permissions(tools)

        assert len(permissions) == 3
        assert all(p.risk_level == "low" for p in permissions)

    def test_analyze_restricted_bash(self):
        """Test analyzing restricted Bash patterns."""
        tools = ["Bash(git:*)", "Bash(npm:*)"]
        permissions = analyze_tool_permissions(tools)

        assert len(permissions) == 2
        assert all(p.risk_level == "low" for p in permissions)
        assert all("Restricted shell" in p.description for p in permissions)

    def test_analyze_unrestricted_bash_patterns(self):
        """Test detecting unrestricted Bash patterns."""
        unrestricted = ["Bash", "Bash(*)", "Bash(*:*)"]

        for pattern in unrestricted:
            permissions = analyze_tool_permissions([pattern])
            assert permissions[0].risk_level == "high"
            assert "Unrestricted shell" in permissions[0].description

    def test_analyze_mixed_risk_tools(self):
        """Test analyzing mix of risk levels."""
        tools = ["Bash", "Read", "vite"]
        permissions = analyze_tool_permissions(tools)

        risk_levels = {p.risk_level for p in permissions}
        assert "high" in risk_levels
        assert "medium" in risk_levels
        assert "low" in risk_levels

    def test_analyze_empty_tools(self):
        """Test analyzing empty tool list."""
        permissions = analyze_tool_permissions([])
        assert permissions == []


class TestGetAgentRiskLevel:
    """Tests for get_agent_risk_level function."""

    def test_high_risk_agent(self, high_risk_agent):
        """Test identifying high-risk agent."""
        risk_level = get_agent_risk_level(high_risk_agent)
        assert risk_level == "high"

    def test_medium_risk_agent(self, medium_risk_agent):
        """Test identifying medium-risk agent."""
        risk_level = get_agent_risk_level(medium_risk_agent)
        assert risk_level == "medium"

    def test_low_risk_agent(self, low_risk_agent):
        """Test identifying low-risk agent."""
        risk_level = get_agent_risk_level(low_risk_agent)
        assert risk_level == "low"

    def test_safe_agent(self, safe_agent):
        """Test identifying safe agent."""
        risk_level = get_agent_risk_level(safe_agent)
        assert risk_level == "low"

    def test_agent_with_no_tools(self, temp_agent_dir):
        """Test agent with no tools."""
        agent_file = temp_agent_dir / "empty-tools.md"
        content = """---
name: empty
tools:
---
"""
        agent_file.write_text(content)
        risk_level = get_agent_risk_level(agent_file)
        assert risk_level == "low"

    def test_invalid_agent_file(self, temp_agent_dir):
        """Test handling invalid agent file."""
        agent_file = temp_agent_dir / "invalid.md"
        agent_file.write_text("Invalid content")

        risk_level = get_agent_risk_level(agent_file)
        assert risk_level == "unknown"


class TestGeneratePermissionsReport:
    """Tests for generate_permissions_report function."""

    def test_report_structure(self, temp_plugin_dir, high_risk_agent, low_risk_agent):
        """Test report has correct structure."""
        report = generate_permissions_report(temp_plugin_dir)

        assert "plugin_dir" in report
        assert "total_agents" in report
        assert "agents" in report
        assert "summary" in report

        assert report["total_agents"] == 2
        assert len(report["agents"]) == 2

    def test_report_summary_counts(self, temp_plugin_dir, high_risk_agent, medium_risk_agent, low_risk_agent):
        """Test report summary has correct counts."""
        report = generate_permissions_report(temp_plugin_dir)

        summary = report["summary"]
        assert summary["high"] == 1
        assert summary["medium"] == 1
        assert summary["low"] == 1

    def test_report_agent_details(self, temp_plugin_dir, high_risk_agent):
        """Test report includes agent details."""
        report = generate_permissions_report(temp_plugin_dir)

        agent = report["agents"][0]
        assert "name" in agent
        assert "file" in agent
        assert "risk_level" in agent
        assert "tools" in agent
        assert "permissions" in agent

        assert agent["name"] == "high-risk-agent"
        assert agent["risk_level"] == "high"

    def test_report_empty_directory(self, temp_plugin_dir):
        """Test report with no agents."""
        # Remove all agent files
        agents_dir = temp_plugin_dir / "agents"
        for f in agents_dir.glob("*.md"):
            f.unlink()

        report = generate_permissions_report(temp_plugin_dir)

        assert report["total_agents"] == 0
        assert len(report["agents"]) == 0
        assert all(count == 0 for count in report["summary"].values())

    def test_report_nonexistent_directory(self, tmp_path):
        """Test report with nonexistent directory."""
        nonexistent = tmp_path / "nonexistent"
        report = generate_permissions_report(nonexistent)

        assert "error" in report
        assert len(report["agents"]) == 0

    def test_report_handles_invalid_agents(self, temp_plugin_dir):
        """Test report handles invalid agent files."""
        agents_dir = temp_plugin_dir / "agents"
        invalid = agents_dir / "invalid.md"
        invalid.write_text("No frontmatter")

        report = generate_permissions_report(temp_plugin_dir)

        assert report["total_agents"] == 1
        agent = report["agents"][0]
        assert agent["risk_level"] == "unknown"
        assert "error" in agent


class TestGetHighRiskAgents:
    """Tests for get_high_risk_agents function."""

    def test_find_high_risk_agents(self, temp_plugin_dir, high_risk_agent, medium_risk_agent, low_risk_agent):
        """Test finding only high-risk agents."""
        high_risk = get_high_risk_agents(temp_plugin_dir)

        assert len(high_risk) == 1
        assert high_risk[0]["name"] == "high-risk-agent"
        assert high_risk[0]["risk_level"] == "high"

    def test_no_high_risk_agents(self, temp_plugin_dir, medium_risk_agent, low_risk_agent):
        """Test when no high-risk agents exist."""
        high_risk = get_high_risk_agents(temp_plugin_dir)

        assert len(high_risk) == 0

    def test_multiple_high_risk_agents(self, temp_plugin_dir):
        """Test finding multiple high-risk agents."""
        agents_dir = temp_plugin_dir / "agents"

        # Create two high-risk agents
        for i in range(2):
            agent_file = agents_dir / f"high-risk-{i}.md"
            content = f"""---
name: high-risk-{i}
tools: Bash, Write
---
"""
            agent_file.write_text(content)

        high_risk = get_high_risk_agents(temp_plugin_dir)

        assert len(high_risk) == 2
        assert all(agent["risk_level"] == "high" for agent in high_risk)


class TestGetAgentPermissions:
    """Tests for get_agent_permissions function."""

    def test_get_permissions_structure(self, high_risk_agent):
        """Test get_agent_permissions returns correct structure."""
        perm_data = get_agent_permissions(high_risk_agent)

        assert "name" in perm_data
        assert "description" in perm_data
        assert "file" in perm_data
        assert "risk_level" in perm_data
        assert "tools" in perm_data
        assert "permissions" in perm_data
        assert "high_risk_tools" in perm_data
        assert "medium_risk_tools" in perm_data

    def test_get_permissions_details(self, high_risk_agent):
        """Test get_agent_permissions returns correct details."""
        perm_data = get_agent_permissions(high_risk_agent)

        assert perm_data["name"] == "high-risk-agent"
        assert perm_data["risk_level"] == "high"
        assert len(perm_data["tools"]) == 5
        assert "Bash" in perm_data["high_risk_tools"]
        assert "Write" in perm_data["high_risk_tools"]

    def test_get_permissions_includes_descriptions(self, high_risk_agent):
        """Test permissions include descriptions."""
        perm_data = get_agent_permissions(high_risk_agent)

        for perm in perm_data["permissions"]:
            assert "tool" in perm
            assert "pattern" in perm
            assert "risk" in perm
            assert "description" in perm
            assert len(perm["description"]) > 0

    def test_get_permissions_medium_risk_categorization(self, medium_risk_agent):
        """Test medium-risk tools are properly categorized."""
        perm_data = get_agent_permissions(medium_risk_agent)

        assert perm_data["risk_level"] == "medium"
        assert "Read" in perm_data["medium_risk_tools"]
        assert len(perm_data["high_risk_tools"]) == 0

    def test_get_permissions_invalid_file(self, temp_agent_dir):
        """Test handling invalid agent file."""
        invalid = temp_agent_dir / "invalid.md"
        invalid.write_text("No frontmatter")

        perm_data = get_agent_permissions(invalid)

        assert perm_data["risk_level"] == "unknown"
        assert "error" in perm_data


class TestToolPermissionDataclass:
    """Tests for ToolPermission dataclass."""

    def test_create_tool_permission(self):
        """Test creating ToolPermission instance."""
        perm = ToolPermission(
            tool_name="Bash", pattern=r"^Bash$", risk_level="high", description="Unrestricted shell access"
        )

        assert perm.tool_name == "Bash"
        assert perm.pattern == r"^Bash$"
        assert perm.risk_level == "high"
        assert perm.description == "Unrestricted shell access"

    def test_tool_permission_immutable(self):
        """Test ToolPermission is a dataclass."""
        perm = ToolPermission(tool_name="Read", pattern=r"^Read$", risk_level="medium", description="File read access")

        # Can access attributes
        assert perm.tool_name == "Read"

        # Has dataclass methods
        assert hasattr(perm, "__dataclass_fields__")


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_tools_with_spaces(self, temp_agent_dir):
        """Test handling tools with extra spaces."""
        agent_file = temp_agent_dir / "spaces.md"
        content = """---
name: spaces
tools: Read , Write , Bash
---
"""
        agent_file.write_text(content)
        tools = parse_agent_tools(agent_file)

        # Should strip spaces
        assert tools == ["Read", "Write", "Bash"]

    def test_tools_with_newlines(self, temp_agent_dir):
        """Test handling multiline tool lists."""
        agent_file = temp_agent_dir / "multiline.md"
        content = """---
name: multiline
tools: >
  Read, Write, Bash,
  Docker, kubernetes
---
"""
        agent_file.write_text(content)
        tools = parse_agent_tools(agent_file)

        assert len(tools) >= 4  # At least Read, Write, Bash, Docker

    def test_case_sensitivity(self):
        """Test tool matching is case-sensitive."""
        tools = ["bash", "BASH", "Bash"]
        permissions = analyze_tool_permissions(tools)

        # Only "Bash" should match high-risk pattern
        high_risk = [p for p in permissions if p.risk_level == "high"]
        assert len(high_risk) == 1
        assert high_risk[0].tool_name == "Bash"

    def test_unicode_in_description(self, temp_agent_dir):
        """Test handling unicode in agent description."""
        agent_file = temp_agent_dir / "unicode.md"
        # Fix YAML indentation
        content = """---
name: unicode-agent
description: "Agent with unicode: 你好 🚀"
tools: Read, Write
---
"""
        agent_file.write_text(content, encoding="utf-8")
        perm_data = get_agent_permissions(agent_file)

        assert "你好" in perm_data["description"]
        assert "🚀" in perm_data["description"]

    def test_very_long_tool_list(self, temp_agent_dir):
        """Test handling very long tool lists."""
        tools = ", ".join([f"tool{i}" for i in range(100)])
        agent_file = temp_agent_dir / "many-tools.md"
        content = f"""---
name: many-tools
tools: {tools}
---
"""
        agent_file.write_text(content)
        parsed_tools = parse_agent_tools(agent_file)

        assert len(parsed_tools) == 100

    def test_duplicate_tools(self, temp_agent_dir):
        """Test handling duplicate tools."""
        agent_file = temp_agent_dir / "dupes.md"
        content = """---
name: dupes
tools: Read, Write, Read, Bash, Write
---
"""
        agent_file.write_text(content)
        tools = parse_agent_tools(agent_file)

        # Should include duplicates (filtering not required)
        assert len(tools) == 5
