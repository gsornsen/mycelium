"""Tests for lazy-loading agent discovery system.

Comprehensive test suite covering:
- Index loading and validation
- Agent listing and filtering
- Lazy content loading
- Cache behavior and LRU eviction
- Search functionality
- Performance benchmarks
- Error handling

Author: @claude-code-developer
Phase: 1 Week 3
Date: 2025-10-17
"""

import json
import tempfile
from pathlib import Path

import pytest

from scripts.agent_discovery import (
    AgentCache,
    AgentDiscovery,
    IndexNotFoundError,
    MalformedIndexError,
    benchmark_discovery,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def tmp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_index(tmp_dir):
    """Create mock index.json for testing.

    Creates:
        - index.json with 4 test agents
        - Agent markdown files with content
    """
    index_data = {
        "agents": [
            {
                "id": "test-agent-1",
                "name": "Test Agent 1",
                "category": "core-development",
                "file_path": str(tmp_dir / "agent1.md"),
                "description": "API design specialist for REST and GraphQL",
                "keywords": ["api", "rest", "graphql"],
                "tools": ["Read", "Write"],
                "expertise": ["API design", "REST"],
            },
            {
                "id": "test-agent-2",
                "name": "Test Agent 2",
                "category": "infrastructure",
                "file_path": str(tmp_dir / "agent2.md"),
                "description": "DevOps expert specializing in Kubernetes",
                "keywords": ["devops", "kubernetes", "docker"],
                "tools": ["Bash"],
                "expertise": ["DevOps", "Kubernetes"],
            },
            {
                "id": "test-agent-3",
                "name": "Test Agent 3",
                "category": "core-development",
                "file_path": str(tmp_dir / "agent3.md"),
                "description": "Python development specialist",
                "keywords": ["python", "testing", "asyncio"],
                "tools": ["Read", "Write", "Bash"],
                "expertise": ["Python", "Testing"],
            },
            {
                "id": "test-agent-4",
                "name": "Test Agent 4",
                "category": "data-ai",
                "file_path": str(tmp_dir / "agent4.md"),
                "description": "Machine learning engineer for model training",
                "keywords": ["ml", "pytorch", "training"],
                "tools": ["Read", "Write"],
                "expertise": ["ML", "PyTorch"],
            },
        ],
        "metadata": {
            "version": "1.0.0",
            "generated": "2025-10-17T00:00:00Z",
            "total_agents": 4,
        },
    }

    index_path = tmp_dir / "index.json"
    with index_path.open("w") as f:
        json.dump(index_data, f, indent=2)

    # Create agent markdown files
    (tmp_dir / "agent1.md").write_text(
        "# Test Agent 1\n\nAPI design specialist.\n\n## Expertise\n- REST APIs\n- GraphQL"
    )
    (tmp_dir / "agent2.md").write_text(
        "# Test Agent 2\n\nDevOps expert.\n\n## Expertise\n- Kubernetes\n- Docker"
    )
    (tmp_dir / "agent3.md").write_text(
        "# Test Agent 3\n\nPython specialist.\n\n## Expertise\n- Async programming\n- Testing"
    )
    (tmp_dir / "agent4.md").write_text(
        "# Test Agent 4\n\nML engineer.\n\n## Expertise\n- PyTorch\n- Model training"
    )

    return index_path


# ============================================================================
# AgentCache Tests
# ============================================================================


class TestAgentCache:
    """Test AgentCache LRU implementation."""

    def test_cache_initialization(self):
        """Test cache initializes with correct defaults."""
        cache = AgentCache(max_size=10)
        stats = cache.get_stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
        assert stats["size"] == 0

    def test_cache_put_and_get(self):
        """Test basic put and get operations."""
        cache = AgentCache(max_size=10)
        agent = {"id": "test-1", "content": "Test content"}

        cache.put("test-1", agent)
        result = cache.get("test-1")

        assert result == agent
        assert cache.get_stats()["hits"] == 1

    def test_cache_miss(self):
        """Test cache miss increments miss counter."""
        cache = AgentCache(max_size=10)
        result = cache.get("nonexistent")

        assert result is None
        assert cache.get_stats()["misses"] == 1

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = AgentCache(max_size=3)

        # Fill cache
        cache.put("agent-1", {"id": "1"})
        cache.put("agent-2", {"id": "2"})
        cache.put("agent-3", {"id": "3"})

        assert cache.get_stats()["size"] == 3

        # Add 4th agent, should evict agent-1 (least recent)
        cache.put("agent-4", {"id": "4"})

        assert cache.get_stats()["size"] == 3
        assert cache.get_stats()["evictions"] == 1
        assert cache.get("agent-1") is None  # Evicted
        assert cache.get("agent-4") is not None  # Present

    def test_cache_lru_ordering(self):
        """Test LRU ordering is maintained on access."""
        cache = AgentCache(max_size=2)

        cache.put("agent-1", {"id": "1"})
        cache.put("agent-2", {"id": "2"})

        # Access agent-1 (makes it most recent)
        cache.get("agent-1")

        # Add agent-3, should evict agent-2 (least recent)
        cache.put("agent-3", {"id": "3"})

        assert cache.get("agent-1") is not None  # Still cached
        assert cache.get("agent-2") is None  # Evicted
        assert cache.get("agent-3") is not None  # Present

    def test_cache_clear(self):
        """Test cache clear removes all entries."""
        cache = AgentCache(max_size=10)

        cache.put("agent-1", {"id": "1"})
        cache.put("agent-2", {"id": "2"})
        cache.clear()

        assert cache.get_stats()["size"] == 0
        assert cache.get("agent-1") is None
        assert cache.get("agent-2") is None


# ============================================================================
# AgentDiscovery Tests
# ============================================================================


class TestAgentDiscovery:
    """Test AgentDiscovery core functionality."""

    def test_load_index(self, mock_index):
        """Test index loads successfully."""
        discovery = AgentDiscovery(mock_index)
        assert len(discovery.index["agents"]) == 4

    def test_index_not_found(self, tmp_dir):
        """Test error when index file doesn't exist."""
        with pytest.raises(IndexNotFoundError):
            AgentDiscovery(tmp_dir / "nonexistent.json")

    def test_malformed_index_invalid_json(self, tmp_dir):
        """Test error when index has invalid JSON."""
        invalid_index = tmp_dir / "invalid.json"
        invalid_index.write_text("{ invalid json }")

        with pytest.raises(MalformedIndexError):
            AgentDiscovery(invalid_index)

    def test_malformed_index_missing_agents_key(self, tmp_dir):
        """Test error when index missing 'agents' key."""
        invalid_index = tmp_dir / "invalid.json"
        invalid_index.write_text('{"metadata": {}}')

        with pytest.raises(MalformedIndexError):
            AgentDiscovery(invalid_index)

    def test_malformed_index_agents_not_list(self, tmp_dir):
        """Test error when 'agents' is not a list."""
        invalid_index = tmp_dir / "invalid.json"
        invalid_index.write_text('{"agents": {}}')

        with pytest.raises(MalformedIndexError):
            AgentDiscovery(invalid_index)

    def test_list_agents_all(self, mock_index):
        """Test listing all agents returns metadata only."""
        discovery = AgentDiscovery(mock_index)
        agents = discovery.list_agents()

        assert len(agents) == 4
        assert all("id" in agent for agent in agents)
        assert all("content" not in agent for agent in agents)

    def test_list_agents_by_category(self, mock_index):
        """Test filtering agents by category."""
        discovery = AgentDiscovery(mock_index)
        agents = discovery.list_agents(category="core-development")

        assert len(agents) == 2
        assert all(a["category"] == "core-development" for a in agents)

    def test_list_agents_by_keywords(self, mock_index):
        """Test filtering agents by keywords."""
        discovery = AgentDiscovery(mock_index)
        agents = discovery.list_agents(keywords=["kubernetes"])

        assert len(agents) == 1
        assert agents[0]["id"] == "test-agent-2"

    def test_list_agents_by_multiple_keywords(self, mock_index):
        """Test filtering by multiple keywords (OR logic)."""
        discovery = AgentDiscovery(mock_index)
        agents = discovery.list_agents(keywords=["api", "kubernetes"])

        assert len(agents) == 2  # agent-1 (api) and agent-2 (kubernetes)

    def test_get_agent_lazy_load(self, mock_index):
        """Test lazy loading of agent content."""
        discovery = AgentDiscovery(mock_index)

        # First call should load from file
        agent = discovery.get_agent("test-agent-1")

        assert agent is not None
        assert "content" in agent
        assert "# Test Agent 1" in agent["content"]
        assert "API design specialist" in agent["content"]

        stats = discovery.get_stats()
        assert stats["file_reads"] == 1
        assert stats["total_lookups"] == 1

    def test_get_agent_cached(self, mock_index):
        """Test caching behavior on repeated access."""
        discovery = AgentDiscovery(mock_index)

        # First call
        agent1 = discovery.get_agent("test-agent-1")

        # Second call (should be cached)
        agent2 = discovery.get_agent("test-agent-1")

        assert agent1 == agent2

        stats = discovery.get_stats()
        assert stats["file_reads"] == 1  # Only one file read
        assert stats["total_lookups"] == 2  # Two lookups
        assert stats["cache"]["hits"] == 1  # One cache hit
        assert stats["cache_hit_rate"] == 50.0  # 1/2 = 50%

    def test_get_agent_not_found(self, mock_index):
        """Test getting nonexistent agent returns None."""
        discovery = AgentDiscovery(mock_index)
        agent = discovery.get_agent("nonexistent")

        assert agent is None

    def test_get_agent_file_missing(self, mock_index, tmp_dir):
        """Test handling of missing agent file."""
        discovery = AgentDiscovery(mock_index)

        # Delete agent file
        (tmp_dir / "agent1.md").unlink()

        agent = discovery.get_agent("test-agent-1")
        assert agent is None

    def test_search_by_description(self, mock_index):
        """Test search in agent descriptions."""
        discovery = AgentDiscovery(mock_index)
        results = discovery.search("api")

        assert len(results) >= 1
        assert any(r["id"] == "test-agent-1" for r in results)

    def test_search_by_keyword(self, mock_index):
        """Test search in agent keywords."""
        discovery = AgentDiscovery(mock_index)
        results = discovery.search("kubernetes")

        assert len(results) == 1
        assert results[0]["id"] == "test-agent-2"

    def test_search_by_name(self, mock_index):
        """Test search in agent names."""
        discovery = AgentDiscovery(mock_index)
        results = discovery.search("Test Agent 3")

        assert len(results) >= 1
        assert any(r["id"] == "test-agent-3" for r in results)

    def test_search_case_insensitive(self, mock_index):
        """Test search is case-insensitive."""
        discovery = AgentDiscovery(mock_index)
        results_lower = discovery.search("python")
        results_upper = discovery.search("PYTHON")
        results_mixed = discovery.search("PyThOn")

        assert len(results_lower) == len(results_upper) == len(results_mixed)

    def test_search_no_results(self, mock_index):
        """Test search with no matches returns empty list."""
        discovery = AgentDiscovery(mock_index)
        results = discovery.search("nonexistent-keyword")

        assert results == []

    def test_lookup_tables_performance(self, mock_index):
        """Test lookup tables provide O(1) access."""
        import time

        discovery = AgentDiscovery(mock_index)

        # Time category lookup (should be O(1))
        start = time.perf_counter()
        agents = discovery.list_agents(category="core-development")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(agents) == 2
        assert elapsed_ms < 1.0  # Should be <1ms for O(1) lookup

    def test_clear_cache(self, mock_index):
        """Test cache clearing."""
        discovery = AgentDiscovery(mock_index)

        # Load some agents
        discovery.get_agent("test-agent-1")
        discovery.get_agent("test-agent-2")

        assert discovery.get_stats()["cache"]["size"] == 2

        # Clear cache
        discovery.clear_cache()

        assert discovery.get_stats()["cache"]["size"] == 0

    def test_cache_size_limit(self, mock_index):
        """Test cache respects size limit."""
        discovery = AgentDiscovery(mock_index, cache_size=2)

        # Load 3 agents (cache size is 2)
        discovery.get_agent("test-agent-1")
        discovery.get_agent("test-agent-2")
        discovery.get_agent("test-agent-3")  # Should evict agent-1

        stats = discovery.get_stats()
        assert stats["cache"]["size"] == 2
        assert stats["cache"]["evictions"] == 1


# ============================================================================
# Performance Tests
# ============================================================================


class TestPerformance:
    """Test performance benchmarks meet targets."""

    def test_list_agents_performance(self, mock_index):
        """Test list_agents meets <20ms target."""
        import time

        discovery = AgentDiscovery(mock_index)

        # Warm up
        discovery.list_agents()

        # Benchmark
        start = time.perf_counter()
        for _ in range(100):
            discovery.list_agents()
        elapsed_ms = (time.perf_counter() - start) * 1000 / 100

        assert elapsed_ms < 20.0, f"list_agents took {elapsed_ms:.2f}ms, target: <20ms"

    def test_get_agent_first_load_performance(self, mock_index):
        """Test get_agent first load meets <5ms target."""
        import time

        discovery = AgentDiscovery(mock_index)

        # Benchmark first load
        start = time.perf_counter()
        discovery.get_agent("test-agent-1")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 5.0, (
            f"get_agent (first) took {elapsed_ms:.2f}ms, target: <5ms"
        )

    def test_get_agent_cached_performance(self, mock_index):
        """Test get_agent cached access meets <1ms target."""
        import time

        discovery = AgentDiscovery(mock_index)

        # Load agent once
        discovery.get_agent("test-agent-1")

        # Benchmark cached access
        start = time.perf_counter()
        for _ in range(100):
            discovery.get_agent("test-agent-1")
        elapsed_ms = (time.perf_counter() - start) * 1000 / 100

        assert elapsed_ms < 1.0, (
            f"get_agent (cached) took {elapsed_ms:.2f}ms, target: <1ms"
        )

    def test_search_performance(self, mock_index):
        """Test search meets <10ms target."""
        import time

        discovery = AgentDiscovery(mock_index)

        # Benchmark search
        start = time.perf_counter()
        for _ in range(100):
            discovery.search("api")
        elapsed_ms = (time.perf_counter() - start) * 1000 / 100

        assert elapsed_ms < 10.0, f"search took {elapsed_ms:.2f}ms, target: <10ms"

    def test_benchmark_function(self, mock_index):
        """Test benchmark function runs successfully."""
        results = benchmark_discovery(mock_index)

        # Verify all expected metrics present
        assert "list_all_agents_ms" in results
        assert "get_agent_first_ms" in results
        assert "get_agent_cached_ms" in results
        assert "search_ms" in results
        assert "filter_category_ms" in results

        # Verify targets
        assert results["list_all_agents_ms"] < 20
        assert results["get_agent_first_ms"] < 5
        assert results["get_agent_cached_ms"] < 1
        assert results["search_ms"] < 10
        assert results["filter_category_ms"] < 5


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests with realistic scenarios."""

    def test_workflow_list_then_get(self, mock_index):
        """Test typical workflow: list then get."""
        discovery = AgentDiscovery(mock_index)

        # List agents in category
        agents = discovery.list_agents(category="core-development")
        assert len(agents) == 2

        # Get full content for first agent
        agent = discovery.get_agent(agents[0]["id"])
        assert agent is not None
        assert "content" in agent

    def test_workflow_search_then_get(self, mock_index):
        """Test typical workflow: search then get."""
        discovery = AgentDiscovery(mock_index)

        # Search for agents
        results = discovery.search("python")
        assert len(results) > 0

        # Get full content for first result
        agent = discovery.get_agent(results[0]["id"])
        assert agent is not None
        assert "content" in agent

    def test_concurrent_access_simulation(self, mock_index):
        """Simulate concurrent access to different agents."""
        discovery = AgentDiscovery(mock_index)

        # Simulate multiple requests
        agent_ids = ["test-agent-1", "test-agent-2", "test-agent-3", "test-agent-4"]

        for _ in range(3):  # 3 rounds
            for agent_id in agent_ids:
                agent = discovery.get_agent(agent_id)
                assert agent is not None

        stats = discovery.get_stats()
        assert stats["total_lookups"] == 12  # 3 rounds * 4 agents
        assert stats["file_reads"] == 4  # Only first access reads file

    def test_cache_effectiveness(self, mock_index):
        """Test cache improves performance on repeated access."""
        discovery = AgentDiscovery(mock_index)

        # Access pattern: agent-1 multiple times, others once
        discovery.get_agent("test-agent-1")
        discovery.get_agent("test-agent-2")
        discovery.get_agent("test-agent-1")  # Cached
        discovery.get_agent("test-agent-3")
        discovery.get_agent("test-agent-1")  # Cached
        discovery.get_agent("test-agent-4")

        stats = discovery.get_stats()
        assert stats["cache_hit_rate"] > 30.0  # 2/6 = 33% cache hits


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
