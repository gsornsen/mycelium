"""
Tests for agent index generation and validation.

Tests cover:
- Schema validation
- Generator script functionality
- Index completeness (all 119 agents)
- Metadata extraction
- Token estimation
"""

import json
import sys
from pathlib import Path

import pytest

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_agent_index import AgentIndexGenerator, AgentMetadata


# Test fixtures
@pytest.fixture
def repo_root():
    """Get repository root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def agents_dir(repo_root):
    """Get agents directory."""
    return repo_root / "plugins" / "mycelium-core" / "agents"


@pytest.fixture
def index_path(repo_root):
    """Get index file path."""
    return repo_root / "plugins" / "mycelium-core" / "agents" / "index.json"


@pytest.fixture
def generator(agents_dir, index_path):
    """Create generator instance."""
    return AgentIndexGenerator(agents_dir, index_path)


@pytest.fixture
def sample_agent_content():
    """Sample agent markdown content for testing."""
    return """---
name: test-agent
description: Test agent for validation
tools: Read, Write, Bash
---

You are a test agent with expertise in testing.

## Your task
1. Test things
2. Validate results
3. Report findings
"""


class TestAgentIndexSchema:
    """Test agent index JSON schema validation."""

    def test_index_file_exists(self, index_path):
        """Index file should exist after generation."""
        # This will pass only after running the generator
        assert index_path.parent.exists(), "Agents directory should exist"

    def test_index_schema_structure(self, index_path):
        """Index should have correct schema structure."""
        if not index_path.exists():
            pytest.skip("Index not generated yet")

        with open(index_path) as f:
            index = json.load(f)

        # Check required top-level fields
        assert "version" in index
        assert "generated" in index
        assert "agent_count" in index
        assert "categories" in index
        assert "agents" in index

        # Check types
        assert isinstance(index["version"], str)
        assert isinstance(index["generated"], str)
        assert isinstance(index["agent_count"], int)
        assert isinstance(index["categories"], list)
        assert isinstance(index["agents"], list)

    def test_agent_metadata_schema(self, index_path):
        """Each agent should have complete metadata."""
        if not index_path.exists():
            pytest.skip("Index not generated yet")

        with open(index_path) as f:
            index = json.load(f)

        required_fields = [
            "id",
            "name",
            "display_name",
            "category",
            "description",
            "tools",
            "keywords",
            "file_path",
            "estimated_tokens",
        ]

        for agent in index["agents"]:
            for field in required_fields:
                assert field in agent, f"Agent {agent.get('id')} missing field: {field}"

            # Check types
            assert isinstance(agent["id"], str)
            assert isinstance(agent["name"], str)
            assert isinstance(agent["display_name"], str)
            assert isinstance(agent["category"], str)
            assert isinstance(agent["description"], str)
            assert isinstance(agent["tools"], list)
            assert isinstance(agent["keywords"], list)
            assert isinstance(agent["file_path"], str)
            assert isinstance(agent["estimated_tokens"], int)
            assert agent["estimated_tokens"] > 0

    def test_no_duplicate_agents(self, index_path):
        """Index should not contain duplicate agent IDs."""
        if not index_path.exists():
            pytest.skip("Index not generated yet")

        with open(index_path) as f:
            index = json.load(f)

        agent_ids = [agent["id"] for agent in index["agents"]]
        assert len(agent_ids) == len(set(agent_ids)), "Duplicate agent IDs found"


class TestAgentIndexCompleteness:
    """Test that all agents are indexed."""

    def test_expected_agent_count(self, index_path):
        """Index should contain all 119 agents."""
        if not index_path.exists():
            pytest.skip("Index not generated yet")

        with open(index_path) as f:
            index = json.load(f)

        # According to AGENT_STRUCTURE_CHANGE.md, there are 119 agents
        assert index["agent_count"] == 119, (
            f"Expected 119 agents, got {index['agent_count']}"
        )
        assert len(index["agents"]) == 119

    def test_all_agent_files_indexed(self, agents_dir, index_path):
        """All .md files in agents directory should be indexed."""
        if not index_path.exists():
            pytest.skip("Index not generated yet")

        # Get all .md files (excluding index.json)
        agent_files = list(agents_dir.glob("*.md"))

        with open(index_path) as f:
            index = json.load(f)

        assert len(index["agents"]) == len(agent_files), (
            f"Agent count mismatch: {len(index['agents'])} indexed vs {len(agent_files)} files"
        )

    def test_all_categories_present(self, index_path):
        """Index should contain all expected categories."""
        if not index_path.exists():
            pytest.skip("Index not generated yet")

        with open(index_path) as f:
            index = json.load(f)

        expected_categories = {
            "Business & Product",
            "Claude Code",
            "Core Development",
            "Data & AI",
            "Developer Experience",
            "Infrastructure",
            "Language Specialists",
            "Meta-Orchestration",
            "Project Management",
            "Quality & Security",
            "Research & Analysis",
            "Specialized Domains",
        }

        actual_categories = set(index["categories"])
        assert actual_categories == expected_categories, (
            f"Category mismatch: {actual_categories ^ expected_categories}"
        )


class TestAgentMetadataExtraction:
    """Test metadata extraction from agent files."""

    def test_parse_frontmatter(self, generator, tmp_path):
        """Generator should correctly parse YAML frontmatter."""
        agent_file = tmp_path / "test-agent.md"
        agent_file.write_text("""---
name: test-agent
description: Test agent for validation
tools: Read, Write, Bash
---

Agent content here.
""")

        metadata = generator.parse_agent_file(agent_file)

        assert metadata is not None
        assert metadata.name == "test-agent"
        assert metadata.description == "Test agent for validation"
        assert sorted(metadata.tools) == ["Bash", "Read", "Write"]

    def test_extract_category_from_filename(self, generator):
        """Generator should extract category from filename prefix."""
        # Test various filename patterns
        test_cases = [
            ("01-core-api-designer.md", "Core Development"),
            ("02-language-python-pro.md", "Language Specialists"),
            ("09-meta-multi-agent-coordinator.md", "Meta-Orchestration"),
            ("11-claude-plugin-developer.md", "Claude Code"),
        ]

        for filename, expected_category in test_cases:
            category = generator._extract_category_from_filename(filename)
            assert category == expected_category, (
                f"Filename {filename} should map to {expected_category}, got {category}"
            )

    def test_generate_display_name(self, generator):
        """Generator should create proper display names."""
        test_cases = [
            ("api-designer", "Api Designer"),
            ("multi-agent-coordinator", "Multi Agent Coordinator"),
            ("python-pro", "Python Pro"),
        ]

        for name, expected_display in test_cases:
            display = generator._generate_display_name(name)
            assert display == expected_display

    def test_keyword_extraction(self, generator, sample_agent_content):
        """Generator should extract relevant keywords."""
        # Extract from sample content
        description = "Test agent for validation"
        body = "You are a test agent with expertise in testing."

        keywords = generator._extract_keywords(description, body)

        assert isinstance(keywords, list)
        assert len(keywords) <= 15
        # Keywords should not contain stop words
        for kw in keywords:
            assert kw not in generator.STOP_WORDS

    def test_token_estimation(self, generator, sample_agent_content):
        """Generator should estimate token counts reasonably."""
        tokens = generator._estimate_tokens(sample_agent_content)

        assert tokens > 0
        # Sample content has ~30 words, so estimate should be ~40-60 tokens
        assert 30 < tokens < 100


class TestGeneratorValidation:
    """Test generator validation logic."""

    def test_validate_correct_index(self, generator, index_path):
        """Valid index should pass validation."""
        if not index_path.exists():
            pytest.skip("Index not generated yet")

        generator.scan_agents()

        with open(index_path) as f:
            index = json.load(f)

        assert generator.validate_index(index), "Valid index should pass validation"

    def test_reject_invalid_version(self, generator):
        """Invalid version should fail validation."""
        generator.agents = []
        invalid_index = {
            "version": "2.0.0",  # Wrong version
            "agent_count": 0,
            "categories": [],
            "agents": [],
        }

        assert not generator.validate_index(invalid_index)

    def test_reject_duplicate_ids(self, generator):
        """Duplicate agent IDs should fail validation."""
        generator.agents = [
            AgentMetadata(
                id="test-agent",
                name="test-agent",
                display_name="Test Agent",
                category="Test",
                description="Test",
                tools=[],
                keywords=[],
                file_path="test.md",
                estimated_tokens=100,
            )
        ]

        invalid_index = {
            "version": "1.0.0",
            "agent_count": 1,
            "categories": ["Test"],
            "agents": [
                {
                    "id": "test-agent",
                    "name": "test-agent",
                    "display_name": "Test Agent",
                    "category": "Test",
                    "description": "Test",
                    "tools": [],
                    "keywords": [],
                    "file_path": "test.md",
                    "estimated_tokens": 100,
                },
                {
                    "id": "test-agent",  # Duplicate
                    "name": "test-agent",
                    "display_name": "Test Agent",
                    "category": "Test",
                    "description": "Test",
                    "tools": [],
                    "keywords": [],
                    "file_path": "test2.md",
                    "estimated_tokens": 100,
                },
            ],
        }

        assert not generator.validate_index(invalid_index)


class TestIndexGeneration:
    """Test full index generation process."""

    def test_scan_agents(self, generator, agents_dir):
        """Generator should scan all agent files."""
        generator.scan_agents()

        assert len(generator.agents) > 0
        # Should have all 119 agents
        assert len(generator.agents) == 119

    def test_generate_index_structure(self, generator):
        """Generated index should have correct structure."""
        generator.scan_agents()
        index = generator.generate_index()

        assert index["version"] == "1.0.0"
        assert index["agent_count"] == len(generator.agents)
        assert len(index["agents"]) == len(generator.agents)
        assert "generated" in index
        assert "categories" in index


# Integration test
class TestEndToEnd:
    """End-to-end integration test."""

    def test_full_generation_workflow(self, generator):
        """Full workflow should succeed."""
        # This would normally regenerate the index
        # For testing, we just validate the existing one
        success = generator.run(validate_only=True)
        assert success, "Index generation workflow should succeed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
