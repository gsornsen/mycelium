"""Lazy-loading agent discovery system for Mycelium.

Provides efficient agent lookup with metadata-only loading and on-demand
content fetching. Designed for <20ms discovery operations with intelligent
caching.

Performance targets:
    - list_agents(): <20ms
    - get_agent() first load: <5ms
    - get_agent() cached: <1ms
    - search(): <10ms

Example:
    >>> from pathlib import Path
    >>> discovery = AgentDiscovery(Path("plugins/mycelium-core/agents/index.json"))
    >>> agents = discovery.list_agents(category="core-development")
    >>> len(agents)
    12
    >>> agent = discovery.get_agent("01-core-api-designer")
    >>> print(len(agent['content']))  # Lazily loaded
    4582

Author: @claude-code-developer
Phase: 1 Week 3
Date: 2025-10-17
"""

import json
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any


class AgentDiscoveryError(Exception):
    """Base exception for agent discovery errors."""
    pass


class IndexNotFoundError(AgentDiscoveryError):
    """Raised when index.json file is not found."""
    pass


class MalformedIndexError(AgentDiscoveryError):
    """Raised when index.json is malformed."""
    pass


class AgentCache:
    """LRU cache for agent content with statistics tracking.

    Implements least-recently-used eviction policy to balance memory
    usage and performance. Tracks cache hits/misses for monitoring.

    Args:
        max_size: Maximum number of agents to cache (default: 50)

    Example:
        >>> cache = AgentCache(max_size=10)
        >>> cache.put("agent-1", {"content": "..."})
        >>> agent = cache.get("agent-1")  # Cache hit
        >>> stats = cache.get_stats()
        >>> stats['hits']
        1
    """

    def __init__(self, max_size: int = 50):
        """Initialize LRU cache.

        Args:
            max_size: Maximum cached agents before eviction
        """
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'puts': 0
        }

    def get(self, key: str) -> dict[str, Any] | None:
        """Get cached agent, moving to end (most recent).

        Args:
            key: Agent ID

        Returns:
            Cached agent dict or None if not cached
        """
        if key in self._cache:
            self._stats['hits'] += 1
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return self._cache[key]

        self._stats['misses'] += 1
        return None

    def put(self, key: str, value: dict[str, Any]) -> None:
        """Cache agent content with LRU eviction.

        Args:
            key: Agent ID
            value: Agent dict with content
        """
        self._stats['puts'] += 1

        if key in self._cache:
            # Update existing entry
            self._cache.move_to_end(key)
            self._cache[key] = value
        else:
            # Add new entry
            if len(self._cache) >= self._max_size:
                # Evict least recently used (first item)
                evicted_key = next(iter(self._cache))
                del self._cache[evicted_key]
                self._stats['evictions'] += 1

            self._cache[key] = value

    def clear(self) -> None:
        """Clear all cached content."""
        self._cache.clear()
        # Reset stats but preserve eviction count
        evictions = self._stats['evictions']
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': evictions,
            'puts': 0
        }

    def get_stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dict with hits, misses, evictions, puts, size
        """
        return {
            **self._stats,
            'size': len(self._cache)
        }


class AgentDiscovery:
    """Lazy-loading agent discovery with intelligent caching.

    Provides efficient agent lookup with metadata-only loading and
    on-demand content fetching. Uses lookup tables for O(1) access
    and LRU caching for performance.

    Performance targets:
        - list_agents(): <20ms
        - get_agent() first load: <5ms
        - get_agent() cached: <1ms
        - search(): <10ms

    Example:
        >>> discovery = AgentDiscovery(Path("plugins/mycelium-core/agents/index.json"))
        >>> agents = discovery.list_agents(category="core-development")
        >>> len(agents)
        12
        >>> agent = discovery.get_agent("01-core-api-designer")
        >>> 'content' in agent
        True
    """

    def __init__(self, index_path: Path, cache_size: int = 50):
        """Initialize discovery system.

        Loads metadata index and builds lookup tables for fast access.
        Does NOT load agent content (lazy loaded on get_agent()).

        Args:
            index_path: Path to index.json file
            cache_size: Maximum agents to cache (default: 50)

        Raises:
            IndexNotFoundError: If index file doesn't exist
            MalformedIndexError: If index is malformed
        """
        self.index_path = index_path
        self.cache_size = cache_size

        # Load lightweight index (metadata only)
        self.index = self._load_index()

        # Build lookup tables for O(1) access
        self._id_to_agent: dict[str, dict[str, Any]] = {}
        self._category_to_agents: dict[str, list[dict[str, Any]]] = {}
        self._keyword_to_agents: dict[str, list[dict[str, Any]]] = {}
        self._build_lookup_tables()

        # Initialize content cache
        self._cache = AgentCache(max_size=cache_size)

        # Performance statistics
        self._stats = {
            'file_reads': 0,
            'total_lookups': 0
        }

        # Initialize telemetry (graceful degradation if unavailable)
        self.telemetry: Any | None = None
        try:
            from mycelium_analytics import EventStorage, TelemetryCollector
            storage = EventStorage()
            self.telemetry = TelemetryCollector(storage)
        except Exception:
            # Telemetry unavailable - continue without it
            pass

    def _load_index(self) -> dict[str, Any]:
        """Load index.json metadata (lightweight).

        Returns:
            Index dictionary with agent metadata

        Raises:
            IndexNotFoundError: If index doesn't exist
            MalformedIndexError: If index is malformed
        """
        if not self.index_path.exists():
            raise IndexNotFoundError(
                f"Index file not found: {self.index_path}"
            )

        try:
            with open(self.index_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise MalformedIndexError(
                f"Invalid JSON in index file: {e}"
            )

        if 'agents' not in data:
            raise MalformedIndexError(
                "Index missing required 'agents' key"
            )

        if not isinstance(data['agents'], list):
            raise MalformedIndexError(
                "'agents' must be a list"
            )

        return data

    def _build_lookup_tables(self) -> None:
        """Build lookup tables for fast O(1) access.

        Creates:
            - ID → agent mapping (O(1) get_agent)
            - Category → agents mapping (O(1) category filter)
            - Keyword → agents inverted index (O(k) search)
        """
        for agent in self.index['agents']:
            # Validate required fields
            if 'id' not in agent:
                continue  # Skip malformed agents

            agent_id = agent['id']

            # ID lookup table
            self._id_to_agent[agent_id] = agent

            # Category lookup table
            category = agent.get('category', 'uncategorized')
            if category not in self._category_to_agents:
                self._category_to_agents[category] = []
            self._category_to_agents[category].append(agent)

            # Keyword inverted index
            for keyword in agent.get('keywords', []):
                keyword_lower = keyword.lower()
                if keyword_lower not in self._keyword_to_agents:
                    self._keyword_to_agents[keyword_lower] = []
                self._keyword_to_agents[keyword_lower].append(agent)

    def list_agents(
        self,
        category: str | None = None,
        keywords: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """List agents (metadata only, no content).

        Returns lightweight metadata for all matching agents without
        loading full markdown content. Use get_agent() to load content.

        Args:
            category: Filter by category (e.g., "core-development")
            keywords: Filter by keywords (OR logic)

        Returns:
            List of agent metadata dicts (no 'content' field)

        Example:
            >>> agents = discovery.list_agents(category="infrastructure")
            >>> len(agents)
            12
            >>> 'content' in agents[0]
            False
        """
        start_time = time.perf_counter()

        # Start with all agents
        if category:
            # O(1) lookup by category
            agents = self._category_to_agents.get(category, [])
        else:
            # All agents
            agents = self.index['agents']

        # Filter by keywords if provided
        if keywords:
            filtered = []
            for agent in agents:
                agent_keywords = [kw.lower() for kw in agent.get('keywords', [])]
                if any(kw.lower() in agent_keywords for kw in keywords):
                    filtered.append(agent)
            agents = filtered

        # Record telemetry
        duration_ms = (time.perf_counter() - start_time) * 1000
        if self.telemetry:
            self.telemetry.record_agent_discovery(
                operation='list_agents',
                duration_ms=duration_ms,
                agent_count=len(agents),
            )

        # Return metadata only (no content)
        return agents

    def get_agent(self, agent_id: str) -> dict[str, Any] | None:
        """Get agent details (lazy load content).

        Loads full agent content on first access, then caches for future
        requests. Subsequent accesses are <1ms from cache.

        Args:
            agent_id: Agent identifier (e.g., "01-core-api-designer")

        Returns:
            Agent dict with metadata + content, or None if not found

        Example:
            >>> agent = discovery.get_agent("01-core-api-designer")
            >>> agent is not None
            True
            >>> 'content' in agent
            True
        """
        start_time = time.perf_counter()
        self._stats['total_lookups'] += 1

        # Check cache first
        cached = self._cache.get(agent_id)
        cache_hit = cached is not None

        if cached is not None:
            # Record telemetry for cache hit
            duration_ms = (time.perf_counter() - start_time) * 1000
            if self.telemetry:
                self.telemetry.record_agent_discovery(
                    operation='get_agent',
                    duration_ms=duration_ms,
                    cache_hit=True,
                    agent_count=1,
                )
            return cached

        # O(1) lookup in index
        agent_meta = self._id_to_agent.get(agent_id)
        if agent_meta is None:
            # Record telemetry for miss (agent not found)
            duration_ms = (time.perf_counter() - start_time) * 1000
            if self.telemetry:
                self.telemetry.record_agent_discovery(
                    operation='get_agent',
                    duration_ms=duration_ms,
                    cache_hit=False,
                    agent_count=0,
                )
            return None

        # Lazy load content from markdown file
        agent_file = Path(agent_meta['file_path'])
        if not agent_file.exists():
            # Agent file missing (broken reference)
            duration_ms = (time.perf_counter() - start_time) * 1000
            if self.telemetry:
                self.telemetry.record_agent_discovery(
                    operation='get_agent',
                    duration_ms=duration_ms,
                    cache_hit=False,
                    agent_count=0,
                )
            return None

        try:
            self._stats['file_reads'] += 1
            content = agent_file.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            # File read error
            duration_ms = (time.perf_counter() - start_time) * 1000
            if self.telemetry:
                self.telemetry.record_agent_discovery(
                    operation='get_agent',
                    duration_ms=duration_ms,
                    cache_hit=False,
                    agent_count=0,
                )
            return None

        # Combine metadata + content
        agent_full = {**agent_meta, 'content': content}

        # Cache for future requests
        self._cache.put(agent_id, agent_full)

        # Record telemetry for successful load
        duration_ms = (time.perf_counter() - start_time) * 1000
        if self.telemetry:
            self.telemetry.record_agent_discovery(
                operation='get_agent',
                duration_ms=duration_ms,
                cache_hit=False,
                agent_count=1,
            )

            # Also record agent load metrics
            content_size = len(content.encode('utf-8'))
            # Rough token estimate: ~4 chars per token
            estimated_tokens = content_size // 4
            self.telemetry.record_agent_load(
                agent_id=agent_id,
                load_time_ms=duration_ms,
                content_size_bytes=content_size,
                estimated_tokens=estimated_tokens,
            )

        return agent_full

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search agents by keyword in metadata.

        Fast search across agent names, descriptions, and keywords using
        inverted index. Does not search full content (use get_agent() for that).

        Args:
            query: Search string (case-insensitive)

        Returns:
            List of matching agent metadata dicts

        Example:
            >>> results = discovery.search("api")
            >>> len(results) > 0
            True
            >>> any('api' in r['name'].lower() for r in results)
            True
        """
        start_time = time.perf_counter()

        query_lower = query.lower()
        results_set = set()  # Use set to avoid duplicates

        # Search in keyword inverted index (O(k))
        for keyword, agents in self._keyword_to_agents.items():
            if query_lower in keyword:
                for agent in agents:
                    results_set.add(agent['id'])

        # Search in names and descriptions (O(n))
        for agent in self.index['agents']:
            # Skip if already found via keywords
            if agent['id'] in results_set:
                continue

            # Search in name
            if query_lower in agent.get('name', '').lower():
                results_set.add(agent['id'])
                continue

            # Search in description
            if query_lower in agent.get('description', '').lower():
                results_set.add(agent['id'])

        # Convert IDs back to agent metadata
        results = [
            self._id_to_agent[agent_id]
            for agent_id in results_set
            if agent_id in self._id_to_agent
        ]

        # Record telemetry
        duration_ms = (time.perf_counter() - start_time) * 1000
        if self.telemetry:
            self.telemetry.record_agent_discovery(
                operation='search',
                duration_ms=duration_ms,
                agent_count=len(results),
            )

        return results

    def get_stats(self) -> dict[str, Any]:
        """Get performance statistics.

        Returns:
            Dict with cache stats, file reads, lookups, etc.

        Example:
            >>> stats = discovery.get_stats()
            >>> stats['cache']['hits'] + stats['cache']['misses']
            50
        """
        cache_stats = self._cache.get_stats()

        return {
            'cache': cache_stats,
            'file_reads': self._stats['file_reads'],
            'total_lookups': self._stats['total_lookups'],
            'cache_hit_rate': (
                cache_stats['hits'] / max(1, self._stats['total_lookups'])
            ) * 100
        }

    def clear_cache(self) -> None:
        """Clear the content cache.

        Useful for testing or freeing memory. Metadata and lookup
        tables remain loaded for fast access.

        Example:
            >>> discovery.clear_cache()
            >>> stats = discovery.get_stats()
            >>> stats['cache']['size']
            0
        """
        self._cache.clear()


def benchmark_discovery(index_path: Path) -> dict[str, float]:
    """Benchmark discovery performance and validate targets.

    Runs comprehensive performance tests:
        - List all agents
        - Get agent (first load)
        - Get agent (cached)
        - Search by keyword
        - Filter by category

    Args:
        index_path: Path to index.json

    Returns:
        Dict with benchmark results in milliseconds

    Example:
        >>> results = benchmark_discovery(Path("plugins/.../index.json"))
        >>> results['list_all_agents_ms'] < 20
        True
    """
    discovery = AgentDiscovery(index_path)
    results = {}

    # Test 1: List all agents (metadata only)
    start = time.perf_counter()
    agents = discovery.list_agents()
    elapsed = (time.perf_counter() - start) * 1000
    results['list_all_agents_ms'] = elapsed
    results['agent_count'] = len(agents)

    # Test 2: Get single agent (first load)
    if agents:
        discovery.clear_cache()
        agent_id = agents[0]['id']

        start = time.perf_counter()
        agent = discovery.get_agent(agent_id)
        elapsed = (time.perf_counter() - start) * 1000
        results['get_agent_first_ms'] = elapsed

        # Test 3: Get same agent (cached)
        start = time.perf_counter()
        agent = discovery.get_agent(agent_id)
        elapsed = (time.perf_counter() - start) * 1000
        results['get_agent_cached_ms'] = elapsed

    # Test 4: Search by keyword
    start = time.perf_counter()
    search_results = discovery.search("api")
    elapsed = (time.perf_counter() - start) * 1000
    results['search_ms'] = elapsed
    results['search_result_count'] = len(search_results)

    # Test 5: Filter by category
    categories = set(a.get('category') for a in agents if 'category' in a)
    if categories:
        test_category = next(iter(categories))
        start = time.perf_counter()
        filtered = discovery.list_agents(category=test_category)
        elapsed = (time.perf_counter() - start) * 1000
        results['filter_category_ms'] = elapsed
        results['filtered_count'] = len(filtered)

    # Performance statistics
    stats = discovery.get_stats()
    results['cache_hit_rate'] = stats['cache_hit_rate']
    results['file_reads'] = stats['file_reads']

    return results


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--benchmark':
        # Run benchmarks
        index = Path('plugins/mycelium-core/agents/index.json')

        if not index.exists():
            print(f"Error: Index not found at {index}")
            print("Run from repository root: cd /home/gerald/git/mycelium")
            sys.exit(1)

        results = benchmark_discovery(index)

        print("=== Agent Discovery Performance Benchmarks ===\n")
        print(f"Agent count:         {results['agent_count']}")
        print("\nPerformance:")
        print(f"  List all agents:   {results['list_all_agents_ms']:.2f}ms")
        print(f"  Get agent (first): {results['get_agent_first_ms']:.2f}ms")
        print(f"  Get agent (cached):{results['get_agent_cached_ms']:.2f}ms")
        print(f"  Search 'api':      {results['search_ms']:.2f}ms ({results['search_result_count']} results)")
        print(f"  Filter category:   {results['filter_category_ms']:.2f}ms ({results['filtered_count']} agents)")
        print("\nCache statistics:")
        print(f"  Cache hit rate:    {results['cache_hit_rate']:.1f}%")
        print(f"  File reads:        {results['file_reads']}")

        # Validate targets
        print("\n=== Target Validation ===\n")
        targets = {
            'list_all_agents_ms': 20,
            'get_agent_first_ms': 5,
            'get_agent_cached_ms': 1,
            'search_ms': 10,
            'filter_category_ms': 5
        }

        all_passed = True
        for metric, target in targets.items():
            actual = results[metric]
            passed = actual < target
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{metric:25s}: {actual:6.2f}ms < {target}ms  {status}")
            if not passed:
                all_passed = False

        print()
        if all_passed:
            print("All performance targets met! 🎉")
            sys.exit(0)
        else:
            print("Some targets missed. Optimization needed.")
            sys.exit(1)
    else:
        print("Usage: python agent_discovery.py --benchmark")
        sys.exit(0)
