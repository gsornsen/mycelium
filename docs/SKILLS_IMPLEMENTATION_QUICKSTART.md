# Skills Implementation Quick Start Guide

**For:** Developers implementing Phase 3A
**Time to First Skill:** ~4 hours
**Prerequisites:** Python 3.9+, Node.js 18+, Git

---

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Day 1: Skills Infrastructure](#day-1-skills-infrastructure)
3. [Day 2-3: First Skill (S1)](#day-2-3-first-skill-s1)
4. [Testing & Validation](#testing--validation)
5. [Common Patterns](#common-patterns)
6. [Troubleshooting](#troubleshooting)

---

## Development Environment Setup

### Prerequisites

```bash
# 1. Clone repository
cd /home/gerald/git/mycelium

# 2. Install Python dependencies
pip install -r requirements.txt
pip install scikit-learn>=1.0.0 pytest pytest-asyncio pytest-benchmark

# 3. Install Node dependencies (for coordination lib)
cd plugins/mycelium-core
npm install

# 4. Verify existing systems work
python scripts/agent_discovery.py --benchmark
python scripts/mycelium_analytics/test_integration.py
```

### Directory Structure Setup

```bash
# Create skills directory structure
mkdir -p plugins/mycelium-core/skills/{tests,templates}
mkdir -p tests/{skills,integration,benchmark,ab_testing,backward_compat}

# Create initial files
touch plugins/mycelium-core/skills/registry.json
touch plugins/mycelium-core/skills/base_skill.py
touch plugins/mycelium-core/skills/skill_loader.py
touch plugins/mycelium-core/skills/skill_executor.py
touch plugins/mycelium-core/config/feature_flags.json
```

---

## Day 1: Skills Infrastructure

### Step 1: Create Base Skill Interface (30 minutes)

**File:** `plugins/mycelium-core/skills/base_skill.py`

```python
"""
Base Skill Interface
All Mycelium skills must inherit from this class.
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import time


class SkillExecutionError(Exception):
    """Raised when skill execution fails."""
    pass


class BaseSkill(ABC):
    """Base class for all Mycelium skills.

    Example:
        >>> class MySkill(BaseSkill):
        ...     def execute(self, params):
        ...         return {'data': 'result', 'metadata': {...}}
        ...
        >>> skill = MySkill()
        >>> result = skill.execute({'input': 'test'})
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize skill.

        Args:
            config: Optional configuration overrides
        """
        self.config = config or self.default_config()

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute skill logic.

        MUST return dict with 'data' and 'metadata' keys.

        Args:
            params: Input parameters

        Returns:
            {
                'data': <skill result>,
                'metadata': {
                    'latency_ms': float,
                    'cache_hit': bool,
                    'version': str
                }
            }
        """
        pass

    @abstractmethod
    def validate_input(self, params: Dict[str, Any]) -> bool:
        """Validate input parameters.

        Raises:
            ValueError: If validation fails

        Returns:
            True if valid
        """
        pass

    @staticmethod
    @abstractmethod
    def default_config() -> Dict:
        """Return default configuration."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Skill version (semantic versioning)."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> list:
        """List of capabilities this skill provides."""
        pass
```

### Step 2: Create Skill Registry (20 minutes)

**File:** `plugins/mycelium-core/skills/registry.json`

```json
{
  "schema_version": "1.0.0",
  "last_updated": "2025-10-19T00:00:00Z",
  "skills": []
}
```

### Step 3: Create Skill Loader (60 minutes)

**File:** `plugins/mycelium-core/skills/skill_loader.py`

```python
"""
Dynamic Skill Loader
Loads skills on-demand with caching.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import importlib.util
import sys
import time


class SkillNotFoundError(Exception):
    """Raised when skill is not found."""
    pass


class SkillLoader:
    """JIT skill loading with caching."""

    def __init__(self, registry_path: Optional[Path] = None):
        """Initialize loader.

        Args:
            registry_path: Path to registry.json
        """
        if registry_path is None:
            # Default to mycelium-core skills
            registry_path = Path(__file__).parent / 'registry.json'

        self.registry_path = registry_path
        self.registry = self._load_registry()
        self._cache: Dict[str, Any] = {}
        self._stats = {
            'loads': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

    def _load_registry(self) -> Dict:
        """Load registry.json.

        Returns:
            Registry dict
        """
        with open(self.registry_path) as f:
            return json.load(f)

    def load(self, skill_id: str) -> Any:
        """Load skill by ID.

        Args:
            skill_id: Skill identifier

        Returns:
            Instantiated skill object

        Raises:
            SkillNotFoundError: If skill not found
        """
        # Check cache
        if skill_id in self._cache:
            self._stats['cache_hits'] += 1
            return self._cache[skill_id]

        self._stats['cache_misses'] += 1
        self._stats['loads'] += 1

        # Find skill metadata
        skill_meta = None
        for skill in self.registry['skills']:
            if skill['id'] == skill_id:
                skill_meta = skill
                break

        if skill_meta is None:
            raise SkillNotFoundError(f"Skill not found: {skill_id}")

        # Load skill module
        start = time.perf_counter()
        skill = self._load_skill_module(skill_meta)
        load_time = (time.perf_counter() - start) * 1000

        # Validate load time
        target = skill_meta.get('performance', {}).get('load_time_ms', 100)
        if load_time > target:
            print(f"⚠️ Skill '{skill_id}' load time {load_time:.1f}ms > {target}ms")

        # Cache and return
        self._cache[skill_id] = skill
        return skill

    def _load_skill_module(self, skill_meta: Dict) -> Any:
        """Load skill from entry point.

        Args:
            skill_meta: Skill metadata

        Returns:
            Skill instance
        """
        exec_config = skill_meta['execution']
        entry_point = exec_config['entry_point']

        # Build absolute path
        skill_dir = self.registry_path.parent
        module_path = skill_dir / entry_point

        if not module_path.exists():
            raise FileNotFoundError(f"Skill entry point not found: {module_path}")

        # Dynamic import
        spec = importlib.util.spec_from_file_location(
            f"skills.{skill_meta['id']}",
            module_path
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        # Get skill class
        class_name = skill_meta.get('class_name', f"{skill_meta['id'].title().replace('-', '')}Skill")
        skill_class = getattr(module, class_name)

        # Instantiate
        return skill_class()

    def get_capabilities(self) -> Dict[str, list]:
        """Get all capabilities.

        Returns:
            Dict mapping capabilities to skill IDs
        """
        capabilities = {}
        for skill in self.registry['skills']:
            for cap in skill.get('capabilities', []):
                if cap not in capabilities:
                    capabilities[cap] = []
                capabilities[cap].append(skill['id'])
        return capabilities

    def get_stats(self) -> Dict:
        """Get loader statistics."""
        return {
            **self._stats,
            'cache_size': len(self._cache)
        }

    def clear_cache(self):
        """Clear skill cache."""
        self._cache.clear()
```

### Step 4: Create Feature Flags (10 minutes)

**File:** `plugins/mycelium-core/config/feature_flags.json`

```json
{
  "skills_enabled": true,
  "skills_traffic_percent": 0,
  "legacy_fallback_enabled": true,

  "skills": {
    "agent_discovery": {
      "enabled": false,
      "traffic_percent": 0
    }
  },

  "rollback": {
    "auto_rollback_threshold_error_rate": 0.05,
    "auto_rollback_threshold_latency_p95_ms": 100
  }
}
```

### Step 5: Create Test Infrastructure (30 minutes)

**File:** `tests/skills/conftest.py`

```python
"""
Pytest configuration for skills tests.
"""

import pytest
from pathlib import Path
import sys

# Add skills to path
skills_dir = Path(__file__).parent.parent.parent / 'plugins/mycelium-core/skills'
sys.path.insert(0, str(skills_dir))


@pytest.fixture
def skill_loader():
    """Create skill loader."""
    from skill_loader import SkillLoader
    return SkillLoader()


@pytest.fixture
def sample_agents():
    """Load sample agents for testing."""
    import json

    agents_path = Path(__file__).parent / 'fixtures' / 'sample_agents.json'

    if not agents_path.exists():
        # Create minimal fixture
        agents_path.parent.mkdir(parents=True, exist_ok=True)
        with open(agents_path, 'w') as f:
            json.dump({
                'agents': [
                    {
                        'id': 'api-designer',
                        'description': 'API design expert',
                        'keywords': ['api', 'rest', 'graphql'],
                        'category': 'core'
                    },
                    {
                        'id': 'database-optimizer',
                        'description': 'Database performance expert',
                        'keywords': ['database', 'sql', 'performance'],
                        'category': 'infrastructure'
                    }
                ]
            }, f, indent=2)

    with open(agents_path) as f:
        return json.load(f)
```

### Step 6: Verify Infrastructure (5 minutes)

```bash
# Run infrastructure tests
python -m pytest tests/skills/conftest.py -v

# Verify files created
ls -lh plugins/mycelium-core/skills/
ls -lh plugins/mycelium-core/config/

# Verify imports work
python -c "from plugins.mycelium_core.skills.base_skill import BaseSkill; print('✅ BaseSkill OK')"
python -c "from plugins.mycelium_core.skills.skill_loader import SkillLoader; print('✅ SkillLoader OK')"
```

**Expected Output:**
```
✅ BaseSkill OK
✅ SkillLoader OK
```

---

## Day 2-3: First Skill (S1 - Agent Discovery)

### Step 1: Create Skill Directory (5 minutes)

```bash
mkdir -p plugins/mycelium-core/skills/agent-discovery/{tests,fixtures}
cd plugins/mycelium-core/skills/agent-discovery

touch main.py vectorizer.py cache.py config.json
touch tests/{test_search.py,test_cache.py,test_vectorizer.py}
touch README.md requirements.txt
```

### Step 2: Implement LRU Cache (20 minutes)

**File:** `skills/agent-discovery/cache.py`

```python
"""
LRU Cache for agent discovery results.
"""

from collections import OrderedDict
from typing import Optional, Dict, Any


class LRUCache:
    """Least-recently-used cache."""

    def __init__(self, max_size: int = 100):
        """Initialize cache.

        Args:
            max_size: Maximum cache entries
        """
        self._cache = OrderedDict()
        self._max_size = max_size
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }

    def get(self, key: str) -> Optional[Any]:
        """Get cached value.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if key in self._cache:
            self._stats['hits'] += 1
            # Move to end (most recent)
            self._cache.move_to_end(key)
            return self._cache[key]

        self._stats['misses'] += 1
        return None

    def put(self, key: str, value: Any):
        """Cache value.

        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self._cache:
            # Update existing
            self._cache.move_to_end(key)
            self._cache[key] = value
        else:
            # Add new entry
            if len(self._cache) >= self._max_size:
                # Evict least recent
                self._cache.popitem(last=False)
                self._stats['evictions'] += 1

            self._cache[key] = value

    def clear(self):
        """Clear cache."""
        self._cache.clear()

    def get_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            **self._stats,
            'size': len(self._cache)
        }
```

### Step 3: Implement TF-IDF Vectorizer (60 minutes)

**File:** `skills/agent-discovery/vectorizer.py`

```python
"""
TF-IDF Vectorizer for agent search.
Extracted from scripts/agent_discovery.py.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class AgentVectorizer:
    """TF-IDF-based agent similarity ranking."""

    def __init__(self, index_path: str):
        """Initialize vectorizer.

        Args:
            index_path: Path to agents/index.json
        """
        self.index_path = Path(index_path)
        self.agents = self._load_agents()

        # Build vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )

        # Fit on agent corpus
        self.agent_vectors = self._vectorize_agents()

    def _load_agents(self) -> List[Dict]:
        """Load agent metadata.

        Returns:
            List of agent dicts
        """
        with open(self.index_path) as f:
            index = json.load(f)
        return index.get('agents', [])

    def _vectorize_agents(self) -> np.ndarray:
        """Create TF-IDF vectors for all agents.

        Returns:
            Matrix of agent vectors
        """
        # Build corpus from descriptions + keywords
        corpus = []
        for agent in self.agents:
            text = agent.get('description', '')
            text += ' ' + ' '.join(agent.get('keywords', []))
            corpus.append(text)

        # Fit and transform
        return self.vectorizer.fit_transform(corpus)

    def search(
        self,
        query: str,
        max_results: int = 5,
        category_filter: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Search agents using TF-IDF similarity.

        Args:
            query: Search query
            max_results: Max results to return
            category_filter: Optional category filter
            min_score: Minimum similarity score

        Returns:
            List of matching agents with scores

        Example:
            >>> vectorizer = AgentVectorizer('agents/index.json')
            >>> results = vectorizer.search("API design")
            >>> results[0]['agent_id']
            'api-designer'
        """
        # Vectorize query
        query_vector = self.vectorizer.transform([query])

        # Compute cosine similarities
        similarities = cosine_similarity(
            query_vector,
            self.agent_vectors
        )[0]

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1]

        # Build results
        results = []
        for idx in top_indices:
            agent = self.agents[idx]
            score = float(similarities[idx])

            # Apply filters
            if score < min_score:
                continue

            if category_filter:
                if agent.get('category') != category_filter:
                    continue

            results.append({
                'agent_id': agent['id'],
                'score': score,
                'explanation': self._explain_match(query, agent),
                'category': agent.get('category', 'uncategorized')
            })

            if len(results) >= max_results:
                break

        return results

    def _explain_match(self, query: str, agent: Dict) -> str:
        """Generate explanation for match.

        Args:
            query: Search query
            agent: Agent metadata

        Returns:
            Explanation string
        """
        # Find keyword matches
        query_words = set(query.lower().split())
        agent_keywords = set(agent.get('keywords', []))

        matches = query_words.intersection(agent_keywords)

        if matches:
            return f"Matches: {', '.join(sorted(matches))}"
        else:
            # Return truncated description
            desc = agent.get('description', '')
            return desc[:100] + '...' if len(desc) > 100 else desc
```

### Step 4: Implement Main Skill (90 minutes)

**File:** `skills/agent-discovery/main.py`

```python
"""
Agent Discovery Skill
Provides TF-IDF-based agent search and recommendation.

Tier: 1
Priority: #1
Consensus: 5/5 analysts
"""

from typing import Dict, Any, List, Optional
import time
from pathlib import Path
import sys

# Add skills base path
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_skill import BaseSkill, SkillExecutionError

# Import skill components
from .vectorizer import AgentVectorizer
from .cache import LRUCache


class AgentDiscoverySkill(BaseSkill):
    """Agent discovery using TF-IDF similarity."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize agent discovery skill."""
        super().__init__(config)

        # Initialize vectorizer
        self.vectorizer = AgentVectorizer(
            index_path=self.config['index_path']
        )

        # Initialize cache
        if self.config['cache_enabled']:
            self.cache = LRUCache(
                max_size=self.config['cache_size']
            )
        else:
            self.cache = None

        # Initialize telemetry (optional)
        self.telemetry = None
        try:
            from mycelium_analytics import TelemetryCollector, EventStorage
            storage = EventStorage()
            self.telemetry = TelemetryCollector(storage)
        except ImportError:
            pass  # Telemetry unavailable

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent discovery.

        Args:
            params: {
                'query': str,              # Search query (REQUIRED)
                'max_results': int,        # Max results (default: 5)
                'category_filter': str,    # Category filter (optional)
                'min_score': float         # Min score (default: 0.0)
            }

        Returns:
            {
                'data': [
                    {
                        'id': str,
                        'score': float,
                        'reason': str,
                        'category': str
                    }
                ],
                'metadata': {
                    'latency_ms': float,
                    'cache_hit': bool,
                    'version': str,
                    'total_results': int
                }
            }
        """
        start_time = time.perf_counter()

        # Validate input
        self.validate_input(params)

        # Extract parameters
        query = params['query']
        max_results = params.get('max_results', 5)
        category_filter = params.get('category_filter')
        min_score = params.get('min_score', 0.0)

        # Check cache
        cache_key = self._cache_key(params)
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                latency_ms = (time.perf_counter() - start_time) * 1000

                # Record telemetry
                if self.telemetry:
                    self.telemetry.record_skill_execution(
                        skill_id='agent-discovery',
                        operation='search',
                        latency_ms=latency_ms,
                        cache_hit=True
                    )

                return {
                    'data': cached['data'],
                    'metadata': {
                        **cached['metadata'],
                        'latency_ms': latency_ms,
                        'cache_hit': True
                    }
                }

        # Execute search
        try:
            results = self.vectorizer.search(
                query=query,
                max_results=max_results,
                category_filter=category_filter,
                min_score=min_score
            )

            # Format results
            formatted_results = [
                {
                    'id': r['agent_id'],
                    'score': round(r['score'], 3),
                    'reason': r['explanation'],
                    'category': r['category']
                }
                for r in results
            ]

            # Calculate latency
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Build metadata
            metadata = {
                'latency_ms': latency_ms,
                'cache_hit': False,
                'version': self.version,
                'total_results': len(formatted_results)
            }

            # Cache result
            if self.cache:
                self.cache.put(cache_key, {
                    'data': formatted_results,
                    'metadata': metadata
                })

            # Record telemetry
            if self.telemetry:
                self.telemetry.record_skill_execution(
                    skill_id='agent-discovery',
                    operation='search',
                    latency_ms=latency_ms,
                    cache_hit=False,
                    result_count=len(formatted_results)
                )

            return {
                'data': formatted_results,
                'metadata': metadata
            }

        except Exception as e:
            raise SkillExecutionError(f"Agent discovery failed: {e}")

    def validate_input(self, params: Dict[str, Any]) -> bool:
        """Validate input parameters."""
        if 'query' not in params:
            raise ValueError("Missing required parameter: 'query'")

        if not isinstance(params['query'], str):
            raise ValueError("'query' must be a string")

        if len(params['query'].strip()) == 0:
            raise ValueError("'query' cannot be empty")

        if 'max_results' in params:
            if not isinstance(params['max_results'], int):
                raise ValueError("'max_results' must be an integer")
            if params['max_results'] < 1:
                raise ValueError("'max_results' must be >= 1")

        return True

    def _cache_key(self, params: Dict[str, Any]) -> str:
        """Generate cache key."""
        query = params['query']
        max_results = params.get('max_results', 5)
        category = params.get('category_filter', 'all')
        min_score = params.get('min_score', 0.0)

        return f"{query}:{max_results}:{category}:{min_score}"

    @staticmethod
    def default_config() -> Dict:
        """Default configuration."""
        return {
            'index_path': 'plugins/mycelium-core/agents/index.json',
            'cache_enabled': True,
            'cache_size': 100,
            'timeout_ms': 5000
        }

    @property
    def version(self) -> str:
        """Skill version."""
        return "1.0.0"

    @property
    def capabilities(self) -> list:
        """Skill capabilities."""
        return [
            'search_agents',
            'recommend_agents',
            'filter_by_category',
            'similarity_ranking'
        ]


# Convenience function for direct use
def search_agents(
    query: str,
    max_results: int = 5,
    category_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search for agents matching query.

    Args:
        query: Search query
        max_results: Maximum results
        category_filter: Optional category filter

    Returns:
        List of matching agents

    Example:
        >>> results = search_agents("API design")
        >>> results[0]['id']
        'api-designer'
    """
    skill = AgentDiscoverySkill()
    result = skill.execute({
        'query': query,
        'max_results': max_results,
        'category_filter': category_filter
    })
    return result['data']


if __name__ == '__main__':
    # CLI for testing
    import sys

    if len(sys.argv) < 2:
        print("Usage: python main.py <query>")
        sys.exit(1)

    query = ' '.join(sys.argv[1:])
    results = search_agents(query)

    print(f"\nAgent Discovery: '{query}'\n")
    for i, agent in enumerate(results, 1):
        print(f"{i}. {agent['id']} (score: {agent['score']})")
        print(f"   {agent['reason']}\n")
```

### Step 5: Register Skill in Registry (10 minutes)

**File:** `plugins/mycelium-core/skills/registry.json`

```json
{
  "schema_version": "1.0.0",
  "last_updated": "2025-10-19T00:00:00Z",
  "skills": [
    {
      "id": "agent-discovery",
      "name": "Agent Discovery & Recommendation",
      "version": "1.0.0",
      "description": "TF-IDF-based agent matching and recommendation system",
      "author": "mycelium-core",
      "tier": 1,
      "consensus": 5,

      "capabilities": [
        "search_agents",
        "recommend_agents",
        "filter_by_category",
        "similarity_ranking"
      ],

      "execution": {
        "type": "python",
        "entry_point": "agent-discovery/main.py",
        "class_name": "AgentDiscoverySkill",
        "timeout_ms": 5000
      },

      "performance": {
        "target_latency_ms": 10,
        "memory_kb": 45,
        "load_time_ms": 12,
        "cache_ttl_seconds": 3600
      },

      "dependencies": [
        {
          "type": "python_package",
          "name": "scikit-learn",
          "version": ">=1.0.0"
        },
        {
          "type": "python_package",
          "name": "numpy",
          "version": ">=1.20.0"
        }
      ]
    }
  ]
}
```

---

## Testing & Validation

### Unit Tests

**File:** `skills/agent-discovery/tests/test_search.py`

```python
import pytest
from pathlib import Path
import sys

# Add skills to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import AgentDiscoverySkill, search_agents


class TestAgentDiscoverySkill:
    """Unit tests for agent discovery skill."""

    def test_search_basic(self):
        """Test basic search returns results."""
        results = search_agents("API design")

        assert len(results) > 0
        assert all('id' in r for r in results)
        assert all('score' in r for r in results)
        assert all(0 <= r['score'] <= 1 for r in results)

    def test_search_validation(self):
        """Test input validation."""
        skill = AgentDiscoverySkill()

        with pytest.raises(ValueError, match="Missing required parameter"):
            skill.execute({})

        with pytest.raises(ValueError, match="must be a string"):
            skill.execute({'query': 123})

        with pytest.raises(ValueError, match="cannot be empty"):
            skill.execute({'query': ''})

    def test_search_caching(self):
        """Test caching improves performance."""
        skill = AgentDiscoverySkill()

        # First call (cache miss)
        result1 = skill.execute({'query': 'test query'})
        cache_hit1 = result1['metadata']['cache_hit']
        latency1 = result1['metadata']['latency_ms']

        # Second call (cache hit)
        result2 = skill.execute({'query': 'test query'})
        cache_hit2 = result2['metadata']['cache_hit']
        latency2 = result2['metadata']['latency_ms']

        assert not cache_hit1
        assert cache_hit2
        assert latency2 < latency1

    def test_search_performance(self):
        """Test meets latency target."""
        skill = AgentDiscoverySkill()

        # Warm up cache
        skill.execute({'query': 'warm up'})

        # Measure cached performance
        result = skill.execute({'query': 'warm up'})
        latency = result['metadata']['latency_ms']

        assert latency < 10, f"Cached latency {latency:.2f}ms > 10ms target"
```

### Integration Tests

**File:** `tests/integration/test_skill_loading.py`

```python
import pytest
from pathlib import Path
import sys

skills_dir = Path(__file__).parent.parent.parent / 'plugins/mycelium-core/skills'
sys.path.insert(0, str(skills_dir))


@pytest.mark.integration
class TestSkillLoading:
    """Integration tests for skill loading."""

    def test_skill_loader_loads_agent_discovery(self):
        """Test skill loader can load agent-discovery."""
        from skill_loader import SkillLoader

        loader = SkillLoader()
        skill = loader.load('agent-discovery')

        assert skill is not None
        assert skill.version == "1.0.0"
        assert 'search_agents' in skill.capabilities

    def test_skill_execution_end_to_end(self):
        """Test complete skill execution flow."""
        from skill_loader import SkillLoader

        loader = SkillLoader()
        skill = loader.load('agent-discovery')

        result = skill.execute({
            'query': 'API design',
            'max_results': 3
        })

        assert 'data' in result
        assert 'metadata' in result
        assert len(result['data']) <= 3
        assert result['metadata']['version'] == "1.0.0"
```

### Performance Benchmarks

```bash
# Run benchmarks
python -m pytest tests/benchmark/ -v --benchmark-only

# Benchmark specific skill
cd plugins/mycelium-core/skills/agent-discovery
python main.py "API design"  # Should complete in <50ms
```

---

## Common Patterns

### Pattern 1: Adding Telemetry

```python
# In any skill's execute() method
if self.telemetry:
    self.telemetry.record_skill_execution(
        skill_id='my-skill',
        operation='my_operation',
        latency_ms=latency_ms,
        custom_metric=value
    )
```

### Pattern 2: Error Handling

```python
try:
    result = skill.execute(params)
except SkillExecutionError as e:
    # Skill-specific error
    logger.error(f"Skill failed: {e}")
    # Optionally fall back to legacy
    result = fallback_function(params)
except Exception as e:
    # Unexpected error
    logger.exception("Unexpected skill error")
    raise
```

### Pattern 3: Feature Flags

```python
import json

def is_skill_enabled(skill_id: str) -> bool:
    """Check if skill is enabled via feature flags."""
    with open('plugins/mycelium-core/config/feature_flags.json') as f:
        flags = json.load(f)

    return flags.get('skills', {}).get(skill_id, {}).get('enabled', False)

# Usage
if is_skill_enabled('agent-discovery'):
    result = skill.execute(params)
else:
    result = legacy_function(params)
```

---

## Troubleshooting

### Issue: Skill Not Found

```
SkillNotFoundError: Skill not found: agent-discovery
```

**Solution:**
1. Check skill registered in `registry.json`
2. Verify `entry_point` path is correct
3. Ensure skill ID matches exactly

### Issue: Import Errors

```
ModuleNotFoundError: No module named 'base_skill'
```

**Solution:**
```python
# Add this to top of skill files
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Issue: Performance Slower Than Expected

```
⚠️ Skill 'agent-discovery' latency 45ms > 10ms target
```

**Solution:**
1. Check cache is enabled
2. Verify vectorizer pre-trained (not fitting on each request)
3. Profile with `cProfile`:
   ```python
   python -m cProfile -s cumtime main.py "test query"
   ```

### Issue: Tests Fail with Fixture Not Found

```
FileNotFoundError: agents/index.json not found
```

**Solution:**
```bash
# Run from repository root
cd /home/gerald/git/mycelium
python -m pytest tests/skills/ -v
```

---

## Next Steps

1. ✅ Complete Day 1: Skills infrastructure
2. ✅ Complete Day 2-3: First skill (S1)
3. **Day 4-5:** Implement S7 (Analytics Query Skills)
4. **Week 2:** Implement S8 + S3
5. **Week 3:** Implement S2 (8 coordination operations)
6. **Week 4:** Implement S4 + S6 + S5

---

**Estimated Time to Complete This Guide:** 2-3 days
**Questions:** See `/home/gerald/git/mycelium/docs/TECHNICAL_ARCHITECTURE_SKILLS.md`

---

*This quick start guide gets you from zero to a working skill implementation in under a week.*
