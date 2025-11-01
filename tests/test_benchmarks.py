"""Performance benchmarks using pytest-benchmark.

This module contains performance benchmarks for critical operations using
the pytest-benchmark plugin. These tests are marked with @pytest.mark.benchmark
and can be run separately from the main test suite.

Usage:
    pytest tests/test_benchmarks.py -m benchmark --benchmark-only
    pytest tests/ -m benchmark --benchmark-json=results.json

Author: DevOps Engineer
Date: 2025-10-27
"""

import json
import tempfile
from pathlib import Path

import pytest

from scripts.agent_discovery import AgentDiscovery


@pytest.fixture
def benchmark_index():
    """Create a realistic agent index for benchmarking.

    Creates an index with 100+ agents to simulate production scale.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Generate 100+ agent entries
        agents = []
        for i in range(100):
            category = ["core", "infrastructure", "quality", "data"][i % 4]
            agent_id = f"test-agent-{i:03d}"
            file_path = tmp_path / f"{agent_id}.md"

            agents.append(
                {
                    "id": agent_id,
                    "name": f"Test Agent {i}",
                    "category": category,
                    "file_path": str(file_path),
                    "description": f"Specialist for task {i}",
                    "keywords": [f"keyword{i}", f"tech{i % 10}", "testing"],
                    "tools": ["Read", "Write", "Bash"],
                    "expertise": [f"Skill {i}", f"Domain {i % 5}"],
                }
            )

            # Create agent file
            file_path.write_text(
                f"# Test Agent {i}\n\nSpecialist for task {i}.\n\n## Expertise\n- Skill {i}\n- Domain {i % 5}"
            )

        # Create index.json
        index_data = {
            "agents": agents,
            "metadata": {
                "version": "1.0.0",
                "generated": "2025-10-27T00:00:00Z",
                "total_agents": len(agents),
            },
        }

        index_path = tmp_path / "index.json"
        with index_path.open("w") as f:
            json.dump(index_data, f, indent=2)

        yield index_path


# ============================================================================
# Agent Discovery Benchmarks
# ============================================================================


@pytest.mark.benchmark
def test_benchmark_list_all_agents(benchmark, benchmark_index):
    """Benchmark listing all agents (should be <20ms)."""
    discovery = AgentDiscovery(benchmark_index)

    # Benchmark the operation
    result = benchmark(discovery.list_agents)

    # Verify result is valid
    assert len(result) == 100


@pytest.mark.benchmark
def test_benchmark_list_agents_by_category(benchmark, benchmark_index):
    """Benchmark filtering agents by category (should be <5ms)."""
    discovery = AgentDiscovery(benchmark_index)

    # Benchmark the operation
    result = benchmark(discovery.list_agents, category="core")

    # Verify result is valid
    assert len(result) > 0


@pytest.mark.benchmark
def test_benchmark_list_agents_by_keywords(benchmark, benchmark_index):
    """Benchmark filtering agents by keywords (should be <5ms)."""
    discovery = AgentDiscovery(benchmark_index)

    # Benchmark the operation
    result = benchmark(discovery.list_agents, keywords=["testing"])

    # Verify result is valid
    assert len(result) > 0


@pytest.mark.benchmark
def test_benchmark_get_agent_first_load(benchmark, benchmark_index):
    """Benchmark first load of agent (with file I/O, should be <5ms)."""
    discovery = AgentDiscovery(benchmark_index)

    # Benchmark the operation
    result = benchmark(discovery.get_agent, "test-agent-050")

    # Verify result is valid
    assert result is not None
    assert "content" in result


@pytest.mark.benchmark
def test_benchmark_get_agent_cached(benchmark, benchmark_index):
    """Benchmark cached agent access (should be <1ms)."""
    discovery = AgentDiscovery(benchmark_index)

    # Pre-load the agent to cache it
    discovery.get_agent("test-agent-050")

    # Benchmark cached access
    result = benchmark(discovery.get_agent, "test-agent-050")

    # Verify result is valid
    assert result is not None
    assert "content" in result


@pytest.mark.benchmark
def test_benchmark_search_agents(benchmark, benchmark_index):
    """Benchmark searching agents (should be <10ms)."""
    discovery = AgentDiscovery(benchmark_index)

    # Benchmark the operation
    result = benchmark(discovery.search, "testing")

    # Verify result is valid
    assert len(result) > 0


@pytest.mark.benchmark
def test_benchmark_get_stats(benchmark, benchmark_index):
    """Benchmark statistics gathering (should be <1ms)."""
    discovery = AgentDiscovery(benchmark_index)

    # Do some operations first
    discovery.list_agents()
    discovery.get_agent("test-agent-001")
    discovery.search("test")

    # Benchmark the operation
    result = benchmark(discovery.get_stats)

    # Verify result is valid
    assert "cache" in result
    assert "total_lookups" in result
    assert "file_reads" in result
    assert "cache_hit_rate" in result


# ============================================================================
# Index Loading Benchmarks
# ============================================================================


@pytest.mark.benchmark
def test_benchmark_index_loading(benchmark, benchmark_index):
    """Benchmark loading and initializing agent index (should be <50ms)."""

    def load_index():
        return AgentDiscovery(benchmark_index)

    # Benchmark the operation
    result = benchmark(load_index)

    # Verify result is valid
    assert len(result.index["agents"]) == 100


# ============================================================================
# Cache Benchmarks
# ============================================================================


@pytest.mark.benchmark
def test_benchmark_cache_operations(benchmark, benchmark_index):
    """Benchmark cache put/get operations (should be <0.1ms)."""
    from scripts.agent_discovery import AgentCache

    cache = AgentCache(max_size=100)
    test_agent = {"id": "test", "content": "Test content"}

    def cache_operation():
        cache.put("test-id", test_agent)
        return cache.get("test-id")

    # Benchmark the operation
    result = benchmark(cache_operation)

    # Verify result is valid
    assert result == test_agent


@pytest.mark.benchmark
def test_benchmark_cache_lru_eviction(benchmark):
    """Benchmark cache LRU eviction behavior."""
    from scripts.agent_discovery import AgentCache

    cache = AgentCache(max_size=10)

    # Pre-fill cache to trigger evictions
    for i in range(10):
        cache.put(f"agent-{i}", {"id": i})

    def add_with_eviction():
        cache.put("new-agent", {"id": "new"})
        return cache.get("new-agent")

    # Benchmark the operation
    result = benchmark(add_with_eviction)

    # Verify result is valid
    assert result is not None


# ============================================================================
# Stress Test Benchmarks
# ============================================================================


@pytest.mark.benchmark
@pytest.mark.slow
def test_benchmark_high_volume_access(benchmark, benchmark_index):
    """Benchmark high-volume agent access pattern.

    Simulates 1000 agent accesses with realistic access patterns.
    This test is marked as 'slow' and only runs in benchmark mode.
    """
    discovery = AgentDiscovery(benchmark_index, cache_size=50)

    def high_volume_access():
        # Simulate realistic access pattern:
        # - 70% popular agents (cache hits)
        # - 30% diverse agents (cache misses)
        popular_agents = [f"test-agent-{i:03d}" for i in range(20)]
        diverse_agents = [f"test-agent-{i:03d}" for i in range(20, 100)]

        for i in range(100):
            if i % 10 < 7:  # 70% popular
                agent_id = popular_agents[i % len(popular_agents)]
            else:  # 30% diverse
                agent_id = diverse_agents[i % len(diverse_agents)]

            discovery.get_agent(agent_id)

        return discovery.get_stats()

    # Benchmark the operation
    stats = benchmark(high_volume_access)

    # Verify cache is being used effectively
    assert stats["cache_hit_rate"] > 50.0  # Should be >50% hit rate


# ============================================================================
# Configuration
# ============================================================================

# pytest-benchmark configuration
# These settings apply to all benchmarks in this file
pytest_benchmark_config = {
    "min_rounds": 5,  # Minimum number of rounds
    "max_time": 1.0,  # Maximum time per benchmark (seconds)
    "min_time": 0.000005,  # Minimum time per round (5μs)
    "timer": "perf_counter",  # Use high-resolution timer
    "calibration_precision": 10,  # Calibration rounds
    "warmup": True,  # Enable warmup
}
