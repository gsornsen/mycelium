# Mycelium Claude Code Skills: Technical Architecture & Implementation Specification

**Document Type:** Technical Architecture Design
**Author:** claude-code-developer (Technical Lead)
**Date:** 2025-10-19
**Status:** Draft for PM Review
**Phase:** Skills Phase 3A/3B/3C Planning

---

## Executive Summary

This document provides comprehensive technical architecture and implementation guidance for transforming Mycelium's 130-agent ecosystem with Claude Code skills. Based on analysis from 5 independent experts, this specification enables a developer to implement the system with:

- **Clear file locations and structure**
- **Code patterns and examples**
- **Integration points with existing systems**
- **Testing strategies and validation**
- **Risk mitigation and rollback procedures**

**Key Decision:** Implement Phase 3A (8 tactical skills) first to validate approach before architectural transformation (Phase 3B/3C).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Skill Definition Schema](#skill-definition-schema)
3. [File Structure & Organization](#file-structure--organization)
4. [Phase 3A: Tactical Skills Implementation](#phase-3a-tactical-skills-implementation)
5. [Phase 3B: Architectural Foundation](#phase-3b-architectural-foundation)
6. [Phase 3C: Advanced Intelligence](#phase-3c-advanced-intelligence)
7. [Integration with Existing Systems](#integration-with-existing-systems)
8. [Testing Strategy](#testing-strategy)
9. [Migration & Rollback](#migration--rollback)
10. [Technical Risks & Mitigation](#technical-risks--mitigation)

---

## 1. Architecture Overview

### 1.1 Current Architecture (Phase 1 + Phase 2)

```
Current Mycelium Architecture
├── Agent System
│   ├── 130 agents across 11 categories
│   ├── Lazy loading via agent_discovery.py (673 lines)
│   ├── Metadata index: plugins/mycelium-core/agents/index.json
│   └── 820KB total definitions (down from 2.5MB)
│
├── Coordination Infrastructure
│   ├── Dual-mode: Redis MCP / TaskQueue MCP / Markdown fallback
│   ├── lib/coordination.js - CoordinationClient
│   ├── lib/workflow.js - WorkflowClient
│   └── lib/pubsub.js - Event publishing
│
├── Analytics (Phase 2)
│   ├── scripts/mycelium_analytics/ - Telemetry collection
│   ├── Performance tracking (p50/p95/p99)
│   ├── Cache hit rates (87.2%, 41.3x speedup)
│   └── Token consumption monitoring
│
└── Plugin Architecture
    ├── .claude-plugin/plugin.json - Manifest
    ├── agents/ - Agent definitions
    ├── commands/ - Slash commands
    ├── hooks/ - Event handlers (hooks.json)
    └── lib/ - Coordination substrate
```

### 1.2 Target Architecture (Skills-Based)

```
Skills-Based Mycelium Architecture
├── Skill Registry
│   ├── plugins/mycelium-core/skills/registry.json (NEW)
│   ├── Dynamic skill loading (JIT)
│   ├── Capability-based discovery
│   └── 15KB metadata (vs 820KB agent definitions)
│
├── Skill Execution Layer (NEW)
│   ├── skills/agent-discovery/ - S1: Agent matching
│   ├── skills/coordination-protocol/ - S2: 8 operations
│   ├── skills/prompt-compressor/ - S3: Dynamic compression
│   ├── skills/token-budget-optimizer/ - S4: ML allocation
│   ├── skills/context-diff/ - S5: Delta compression
│   ├── skills/mycelium-orchestrator/ - S6: Intelligent routing
│   ├── skills/analytics-queries/ - S7: Pre-compiled queries
│   └── skills/compression-pipeline/ - S8: Automated workflow
│
├── Coordination Infrastructure (ENHANCED)
│   ├── Skill lending protocol (Phase 3B)
│   ├── Shared skill library
│   └── Cross-agent execution context
│
├── Analytics (INTEGRATED)
│   ├── Skill performance tracking
│   ├── Cache effectiveness monitoring
│   └── A/B testing framework
│
└── Plugin Architecture (EXTENDED)
    ├── agents/ - Legacy agents (6-month deprecation)
    ├── skills/ - Skill-based agents (NEW)
    ├── commands/ - Skill-invoking commands
    └── hooks/ - Skill validation/formatting hooks
```

### 1.3 Data Flow: Before vs After

**Before (Prompt-Based Discovery):**
```
User Query: "optimize API performance"
   │
   ▼
Claude Reasoning (5,000-8,000 tokens)
   ├── Parse query for keywords
   ├── Extract file extensions
   ├── Check git context
   ├── TF-IDF similarity across 119 agents
   ├── Rank by relevance
   └── Generate explanations
   │
   ▼
Response: [api-designer (0.94), performance-engineer (0.91), ...]
   │
   └── Latency: 500ms, Tokens: 7,000
```

**After (Skill-Based Discovery):**
```
User Query: "optimize API performance"
   │
   ▼
Skill Invocation: agent-discovery
   ├── Input: {query: "optimize API performance"}
   └── Execution: Python/JS skill code
       │
       ▼
   TF-IDF Vectorizer (pre-trained)
       ├── Query embedding
       ├── Cosine similarity
       └── Top-K results
   │
   ▼
Response: [
  {id: "api-designer", score: 0.94, reason: "API design patterns"},
  {id: "performance-engineer", score: 0.91, reason: "Performance optimization"}
]
   │
   └── Latency: <10ms, Tokens: 200
```

---

## 2. Skill Definition Schema

### 2.1 Skill Metadata Structure

**Location:** `plugins/mycelium-core/skills/registry.json`

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
        "entry_point": "skills/agent-discovery/main.py",
        "function": "search_agents",
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
          "type": "file",
          "path": "scripts/agent_discovery.py"
        }
      ],

      "input_schema": {
        "type": "object",
        "required": ["query"],
        "properties": {
          "query": {"type": "string"},
          "max_results": {"type": "integer", "default": 5},
          "category_filter": {"type": "string", "optional": true}
        }
      },

      "output_schema": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {"type": "string"},
            "score": {"type": "number"},
            "reason": {"type": "string"}
          }
        }
      },

      "telemetry": {
        "enabled": true,
        "metrics": ["latency", "cache_hit_rate", "accuracy"]
      }
    }
  ]
}
```

### 2.2 Skill Implementation Structure

**Location:** `plugins/mycelium-core/skills/agent-discovery/`

```
skills/agent-discovery/
├── main.py                 # Entry point with search_agents()
├── vectorizer.py           # TF-IDF vectorizer logic
├── cache.py                # LRU cache implementation
├── config.json             # Skill-specific configuration
├── tests/
│   ├── test_search.py      # Unit tests
│   ├── test_cache.py       # Cache tests
│   └── fixtures/           # Test data
├── README.md               # Skill documentation
└── requirements.txt        # Python dependencies
```

### 2.3 Skill Interface Contract

All skills MUST implement this interface:

```python
# skills/base_skill.py

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import time

class BaseSkill(ABC):
    """Base class for all Mycelium skills."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize skill with configuration.

        Args:
            config: Skill-specific configuration
        """
        self.config = config or self.default_config()
        self.cache = None  # Optional caching
        self.telemetry = None  # Optional telemetry

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute skill logic.

        Args:
            params: Input parameters matching input_schema

        Returns:
            Result dict with 'data' and 'metadata' keys
            {
                'data': <skill-specific result>,
                'metadata': {
                    'latency_ms': float,
                    'cache_hit': bool,
                    'version': str
                }
            }

        Raises:
            SkillExecutionError: If execution fails
        """
        pass

    @abstractmethod
    def validate_input(self, params: Dict[str, Any]) -> bool:
        """Validate input against schema.

        Args:
            params: Input parameters

        Returns:
            True if valid, raises exception otherwise
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
        """Skill version."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> list:
        """List of capabilities provided."""
        pass
```

---

## 3. File Structure & Organization

### 3.1 Repository Structure (After Skills Implementation)

```
mycelium/
├── .claude-plugin/
│   └── marketplace.json                 # Plugin marketplace metadata
│
├── plugins/
│   └── mycelium-core/
│       ├── .claude-plugin/
│       │   └── plugin.json              # Plugin metadata
│       │
│       ├── agents/                       # LEGACY (Phase 3B deprecation)
│       │   ├── index.json               # Agent metadata index
│       │   ├── 01-core-api-designer.md
│       │   └── ... (130 agents)
│       │
│       ├── skills/                       # NEW: Skill-based system
│       │   ├── registry.json            # ⭐ Skill registry
│       │   ├── base_skill.py            # ⭐ Base skill interface
│       │   ├── skill_loader.py          # ⭐ Dynamic skill loading
│       │   ├── skill_executor.py        # ⭐ Execution engine
│       │   │
│       │   ├── agent-discovery/         # S1: Agent Discovery Skill
│       │   │   ├── main.py
│       │   │   ├── vectorizer.py
│       │   │   ├── cache.py
│       │   │   ├── config.json
│       │   │   ├── tests/
│       │   │   └── README.md
│       │   │
│       │   ├── coordination-protocol/   # S2: Coordination Skills
│       │   │   ├── create_task.py
│       │   │   ├── publish_event.py
│       │   │   ├── get_status.py
│       │   │   ├── ... (8 operations)
│       │   │   └── tests/
│       │   │
│       │   ├── prompt-compressor/       # S3: Compression Skill
│       │   │   ├── main.py
│       │   │   ├── compression_rules.json
│       │   │   ├── tests/
│       │   │   └── README.md
│       │   │
│       │   ├── token-budget-optimizer/  # S4: Budget Optimization
│       │   │   ├── main.py
│       │   │   ├── predictor.py         # ML model
│       │   │   ├── optimizer.py         # Linear programming
│       │   │   └── tests/
│       │   │
│       │   ├── context-diff/            # S5: Diff Compression
│       │   │   ├── main.py
│       │   │   ├── differ.py
│       │   │   └── tests/
│       │   │
│       │   ├── mycelium-orchestrator/   # S6: Meta-orchestration
│       │   │   ├── main.py
│       │   │   ├── intent_classifier.py
│       │   │   ├── pattern_matcher.py
│       │   │   ├── dag_builder.py
│       │   │   └── tests/
│       │   │
│       │   ├── analytics-queries/       # S7: Analytics Skills
│       │   │   ├── performance_report.py
│       │   │   ├── cache_efficiency.py
│       │   │   ├── token_savings.py
│       │   │   └── tests/
│       │   │
│       │   └── compression-pipeline/    # S8: Compression Pipeline
│       │       ├── main.py
│       │       ├── pipeline.sh
│       │       └── tests/
│       │
│       ├── commands/                     # Slash commands
│       │   ├── infra-check.md
│       │   ├── team-status.md
│       │   └── skill-benchmark.md       # NEW: Skill testing command
│       │
│       ├── hooks/                        # Event handlers
│       │   ├── hooks.json
│       │   ├── pre-skill-validator.py   # NEW: Validate skill inputs
│       │   └── post-skill-telemetry.py  # NEW: Record skill metrics
│       │
│       ├── lib/                          # Coordination substrate
│       │   ├── coordination.js          # CoordinationClient
│       │   ├── workflow.js              # WorkflowClient
│       │   ├── pubsub.js                # Event publishing
│       │   └── skill_integration.js     # NEW: Skill invocation from JS
│       │
│       └── tests/
│           ├── integration/
│           │   ├── test_skill_discovery.py
│           │   ├── test_skill_coordination.py
│           │   └── test_backward_compat.py
│           └── benchmark/
│               └── benchmark_skills.py
│
├── scripts/
│   ├── agent_discovery.py               # LEGACY (extracted to skill)
│   ├── compress_descriptions.py         # LEGACY (extracted to skill)
│   ├── mycelium_analytics/              # Analytics integration
│   │   ├── __init__.py
│   │   ├── telemetry.py
│   │   └── skill_metrics.py             # NEW: Skill-specific metrics
│   └── migrate_to_skills.py             # NEW: Migration script
│
├── docs/
│   ├── CLAUDE_CODE_SKILLS_SYNTHESIS.md  # ✅ Exists
│   ├── SKILLS_EXECUTIVE_SUMMARY.md      # ✅ Exists
│   ├── TECHNICAL_ARCHITECTURE_SKILLS.md # ⭐ This document
│   ├── SKILL_DEVELOPMENT_GUIDE.md       # NEW: How to create skills
│   └── MIGRATION_GUIDE_SKILLS.md        # NEW: Agent → Skill migration
│
└── bin/
    └── mycelium-skill                   # NEW: Skill CLI tool
```

### 3.2 Key File Locations Summary

| Component | Location | Purpose |
|-----------|----------|---------|
| **Skill Registry** | `plugins/mycelium-core/skills/registry.json` | Central skill metadata |
| **Skill Base Class** | `plugins/mycelium-core/skills/base_skill.py` | Interface contract |
| **Skill Loader** | `plugins/mycelium-core/skills/skill_loader.py` | JIT loading logic |
| **Skill Executor** | `plugins/mycelium-core/skills/skill_executor.py` | Execution engine |
| **Agent Discovery Skill** | `plugins/mycelium-core/skills/agent-discovery/` | S1 implementation |
| **Coordination Skills** | `plugins/mycelium-core/skills/coordination-protocol/` | S2 implementation |
| **Analytics Integration** | `scripts/mycelium_analytics/skill_metrics.py` | Telemetry tracking |
| **Migration Script** | `scripts/migrate_to_skills.py` | Agent → Skill converter |

---

## 4. Phase 3A: Tactical Skills Implementation

### 4.1 Timeline & Deliverables

**Duration:** 4 weeks
**Team:** 2 developers
**Risk Level:** LOW

```
Week 1: Foundation + S1 + S7
├── Day 1-2: Skill infrastructure
│   ├── Create skills/ directory
│   ├── Implement BaseSkill interface
│   ├── Create SkillLoader
│   ├── Create SkillExecutor
│   └── Set up registry.json
│
├── Day 3-4: S1 - Agent Discovery Skill
│   ├── Extract TF-IDF logic from agent_discovery.py
│   ├── Create main.py with search_agents()
│   ├── Implement caching layer
│   ├── Unit tests (95% coverage)
│   └── Integration tests
│
└── Day 5: S7 - Analytics Query Skills
    ├── Extract queries from mycelium_analytics
    ├── Create performance_report.py
    ├── Create cache_efficiency.py
    ├── Create token_savings.py
    └── Tests

Week 2: Compression + Orchestration
├── Day 1-2: S8 - Compression Pipeline Skill
│   ├── Wrap compress_descriptions.py
│   ├── Create pipeline automation
│   ├── Validation logic
│   └── Tests
│
└── Day 3-5: S3 - Prompt Compression Skill
    ├── Dynamic compression logic
    ├── Budget-aware adaptation
    ├── Keyword preservation validator
    └── Tests

Week 3: Coordination Protocol Suite
├── Day 1-5: S2 - 8 Coordination Operations
    ├── create_task.py (Task creation)
    ├── update_task_status.py (State transitions)
    ├── publish_event.py (Event publishing)
    ├── subscribe_events.py (Event subscription)
    ├── get_workflow_status.py (Status queries)
    ├── distribute_work.py (Load balancing)
    ├── aggregate_results.py (Result merging)
    ├── coordinate_handoff.py (Agent handoffs)
    └── Integration tests

Week 4: Optimization + Meta-Skills
├── Day 1-2: S4 - Token Budget Optimizer
│   ├── ML-based prediction model
│   ├── Linear programming optimizer
│   ├── Budget allocation logic
│   └── Tests
│
├── Day 3-4: S6 - Orchestration Meta-Skill
│   ├── Intent classification
│   ├── Pattern matching
│   ├── DAG construction
│   └── Tests
│
└── Day 5: S5 - Context Diff Compression
    ├── JSON diff logic
    ├── Delta compression
    ├── Apply instructions
    └── Tests
```

### 4.2 S1: Agent Discovery Skill (Detailed Implementation)

**Priority:** #1 (Highest ROI)
**Consensus:** 5/5 analysts
**Estimated Effort:** 2 days

#### File Structure
```
skills/agent-discovery/
├── main.py              # Entry point
├── vectorizer.py        # TF-IDF implementation
├── cache.py             # LRU cache
├── config.json          # Configuration
├── tests/
│   ├── test_search.py
│   ├── test_cache.py
│   └── fixtures/
│       └── sample_agents.json
├── README.md
└── requirements.txt     # scikit-learn>=1.0.0
```

#### main.py Implementation
```python
"""
Agent Discovery Skill
Provides TF-IDF-based agent search and recommendation.

Author: mycelium-core
Tier: 1
Consensus: 5/5
"""

from typing import Dict, Any, List, Optional
import time
from pathlib import Path
import sys

# Add skills base path
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_skill import BaseSkill, SkillExecutionError

from .vectorizer import AgentVectorizer
from .cache import LRUCache


class AgentDiscoverySkill(BaseSkill):
    """Agent discovery using TF-IDF similarity ranking."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize discovery skill.

        Args:
            config: Optional configuration overrides
        """
        super().__init__(config)

        # Load or create vectorizer
        self.vectorizer = AgentVectorizer(
            index_path=self.config['index_path']
        )

        # Initialize cache
        if self.config['cache_enabled']:
            self.cache = LRUCache(max_size=self.config['cache_size'])

        # Load telemetry if available
        try:
            from mycelium_analytics import TelemetryCollector
            self.telemetry = TelemetryCollector()
        except ImportError:
            self.telemetry = None

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent discovery.

        Args:
            params: {
                'query': str,              # Search query
                'max_results': int,        # Max agents to return (default: 5)
                'category_filter': str,    # Optional category filter
                'min_score': float         # Minimum similarity score (default: 0.0)
            }

        Returns:
            {
                'data': [
                    {
                        'id': str,
                        'score': float,
                        'reason': str,
                        'category': str
                    }, ...
                ],
                'metadata': {
                    'latency_ms': float,
                    'cache_hit': bool,
                    'version': str,
                    'query': str,
                    'total_candidates': int
                }
            }
        """
        start_time = time.perf_counter()

        # Validate input
        self.validate_input(params)

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

            # Calculate metadata
            latency_ms = (time.perf_counter() - start_time) * 1000
            metadata = {
                'latency_ms': latency_ms,
                'cache_hit': False,
                'version': self.version,
                'query': query,
                'total_candidates': len(results)
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
            raise SkillExecutionError(
                f"Agent discovery failed: {e}"
            )

    def validate_input(self, params: Dict[str, Any]) -> bool:
        """Validate input parameters.

        Args:
            params: Input dict

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        if 'query' not in params:
            raise ValueError("Missing required parameter: 'query'")

        if not isinstance(params['query'], str):
            raise ValueError("'query' must be a string")

        if len(params['query']) == 0:
            raise ValueError("'query' cannot be empty")

        if 'max_results' in params:
            if not isinstance(params['max_results'], int):
                raise ValueError("'max_results' must be an integer")
            if params['max_results'] < 1:
                raise ValueError("'max_results' must be >= 1")

        return True

    def _cache_key(self, params: Dict[str, Any]) -> str:
        """Generate cache key from parameters.

        Args:
            params: Input parameters

        Returns:
            Cache key string
        """
        query = params['query']
        max_results = params.get('max_results', 5)
        category = params.get('category_filter', 'all')
        min_score = params.get('min_score', 0.0)

        return f"{query}:{max_results}:{category}:{min_score}"

    @staticmethod
    def default_config() -> Dict:
        """Default configuration.

        Returns:
            Config dict with defaults
        """
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


# Convenience function for direct invocation
def search_agents(
    query: str,
    max_results: int = 5,
    category_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search for agents matching query.

    Args:
        query: Search query
        max_results: Maximum results to return
        category_filter: Optional category filter

    Returns:
        List of matching agents with scores

    Example:
        >>> results = search_agents("optimize API performance")
        >>> results[0]['id']
        'api-designer'
        >>> results[0]['score']
        0.94
    """
    skill = AgentDiscoverySkill()
    result = skill.execute({
        'query': query,
        'max_results': max_results,
        'category_filter': category_filter
    })
    return result['data']


if __name__ == '__main__':
    # Simple CLI for testing
    import sys

    if len(sys.argv) < 2:
        print("Usage: python main.py <query>")
        sys.exit(1)

    query = ' '.join(sys.argv[1:])
    results = search_agents(query)

    print(f"\nAgent Discovery Results for: '{query}'\n")
    for i, agent in enumerate(results, 1):
        print(f"{i}. {agent['id']} (score: {agent['score']})")
        print(f"   {agent['reason']}\n")
```

#### vectorizer.py Implementation
```python
"""
TF-IDF Vectorizer for agent discovery.
Extracts logic from scripts/agent_discovery.py.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class AgentVectorizer:
    """TF-IDF-based agent similarity ranking."""

    def __init__(self, index_path: str):
        """Initialize vectorizer with agent index.

        Args:
            index_path: Path to agents/index.json
        """
        self.index_path = Path(index_path)
        self.agents = self._load_agents()
        self.vectorizer = self._build_vectorizer()
        self.agent_vectors = self._vectorize_agents()

    def _load_agents(self) -> List[Dict[str, Any]]:
        """Load agent metadata from index.

        Returns:
            List of agent metadata dicts
        """
        with open(self.index_path) as f:
            index = json.load(f)
        return index['agents']

    def _build_vectorizer(self) -> TfidfVectorizer:
        """Build TF-IDF vectorizer from agent corpus.

        Returns:
            Fitted TfidfVectorizer
        """
        # Create corpus from agent descriptions + keywords
        corpus = []
        for agent in self.agents:
            text = f"{agent.get('description', '')} "
            text += ' '.join(agent.get('keywords', []))
            corpus.append(text)

        # Fit vectorizer
        vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words='english',
            ngram_range=(1, 2)
        )
        vectorizer.fit(corpus)

        return vectorizer

    def _vectorize_agents(self) -> np.ndarray:
        """Vectorize all agents.

        Returns:
            Matrix of agent vectors
        """
        corpus = []
        for agent in self.agents:
            text = f"{agent.get('description', '')} "
            text += ' '.join(agent.get('keywords', []))
            corpus.append(text)

        return self.vectorizer.transform(corpus)

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
            max_results: Maximum results
            category_filter: Optional category filter
            min_score: Minimum similarity score

        Returns:
            List of matching agents with scores
        """
        # Vectorize query
        query_vector = self.vectorizer.transform([query])

        # Compute similarities
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

            if category_filter and agent.get('category') != category_filter:
                continue

            results.append({
                'agent_id': agent['id'],
                'score': score,
                'explanation': self._explain_match(query, agent, score),
                'category': agent.get('category', 'uncategorized')
            })

            if len(results) >= max_results:
                break

        return results

    def _explain_match(
        self,
        query: str,
        agent: Dict[str, Any],
        score: float
    ) -> str:
        """Generate explanation for match.

        Args:
            query: Search query
            agent: Agent metadata
            score: Similarity score

        Returns:
            Explanation string
        """
        # Simple explanation based on keywords
        agent_keywords = set(agent.get('keywords', []))
        query_words = set(query.lower().split())

        matches = agent_keywords.intersection(query_words)

        if matches:
            return f"Matches keywords: {', '.join(matches)}"
        else:
            return agent.get('description', '')[:100]
```

#### Tests
```python
# skills/agent-discovery/tests/test_search.py

import pytest
from ..main import AgentDiscoverySkill, search_agents


def test_search_agents_basic():
    """Test basic agent search."""
    results = search_agents("API design")

    assert len(results) > 0
    assert results[0]['id'] in ['api-designer', 'backend-developer']
    assert results[0]['score'] > 0.5


def test_search_agents_category_filter():
    """Test category filtering."""
    skill = AgentDiscoverySkill()
    result = skill.execute({
        'query': 'database',
        'category_filter': 'infrastructure'
    })

    agents = result['data']
    assert all(
        'database' in a['id'].lower() or
        'infra' in a['category'].lower()
        for a in agents
    )


def test_search_agents_caching():
    """Test caching improves performance."""
    skill = AgentDiscoverySkill()

    # First call (cache miss)
    result1 = skill.execute({'query': 'test query'})
    latency1 = result1['metadata']['latency_ms']
    cache_hit1 = result1['metadata']['cache_hit']

    # Second call (cache hit)
    result2 = skill.execute({'query': 'test query'})
    latency2 = result2['metadata']['latency_ms']
    cache_hit2 = result2['metadata']['cache_hit']

    assert not cache_hit1
    assert cache_hit2
    assert latency2 < latency1  # Cached should be faster


def test_search_agents_validation():
    """Test input validation."""
    skill = AgentDiscoverySkill()

    with pytest.raises(ValueError, match="Missing required parameter"):
        skill.execute({})

    with pytest.raises(ValueError, match="query' must be a string"):
        skill.execute({'query': 123})

    with pytest.raises(ValueError, match="cannot be empty"):
        skill.execute({'query': ''})


def test_search_agents_performance():
    """Test meets latency target (<10ms cached, <50ms uncached)."""
    skill = AgentDiscoverySkill()

    # Warm up
    skill.execute({'query': 'test'})

    # Measure cached performance
    result = skill.execute({'query': 'test'})
    assert result['metadata']['latency_ms'] < 10

    # Measure uncached performance
    skill.cache.clear()
    result = skill.execute({'query': 'unique query 123'})
    assert result['metadata']['latency_ms'] < 50
```

### 4.3 S2: Coordination Protocol Skills (8 Operations)

**Priority:** #4 (High ROI, critical infrastructure)
**Consensus:** 5/5 analysts
**Estimated Effort:** 5 days

#### Implementation Pattern

Each coordination operation becomes a standalone skill following this pattern:

```python
# skills/coordination-protocol/create_task.py

"""
Coordination Skill: Create Task
Wraps CoordinationClient.createTask() for zero-overhead invocation.
"""

from typing import Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_skill import BaseSkill, SkillExecutionError


class CreateTaskSkill(BaseSkill):
    """Create task with dependency management."""

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create task in coordination system.

        Args:
            params: {
                'type': str,                    # Task type
                'assigned_to': str,             # Agent ID
                'depends_on': List[str],        # Task dependencies (optional)
                'priority': str,                # 'low'|'normal'|'high' (optional)
                'deadline': str,                # ISO timestamp (optional)
                'data': Dict                    # Task-specific data (optional)
            }

        Returns:
            {
                'data': {
                    'task_id': str,
                    'status': str,
                    'created_at': str
                },
                'metadata': {
                    'latency_ms': float,
                    'coordination_mode': str  # 'redis'|'taskqueue'|'markdown'
                }
            }
        """
        self.validate_input(params)

        # Import coordination client
        try:
            from ....lib.coordination import CoordinationClient
        except ImportError:
            raise SkillExecutionError(
                "CoordinationClient not available"
            )

        # Initialize client
        client = CoordinationClient()
        await client.initialize()

        # Create task
        task = await client.createTask({
            'type': params['type'],
            'assigned_to': params['assigned_to'],
            'depends_on': params.get('depends_on', []),
            'priority': params.get('priority', 'normal'),
            'deadline': params.get('deadline'),
            'data': params.get('data', {})
        })

        return {
            'data': {
                'task_id': task.id,
                'status': task.status,
                'created_at': task.created_at
            },
            'metadata': {
                'latency_ms': task.creation_latency_ms,
                'coordination_mode': client.mode
            }
        }

    def validate_input(self, params: Dict[str, Any]) -> bool:
        """Validate input parameters."""
        required = ['type', 'assigned_to']
        for field in required:
            if field not in params:
                raise ValueError(f"Missing required field: {field}")

        if 'priority' in params:
            if params['priority'] not in ['low', 'normal', 'high']:
                raise ValueError("Invalid priority")

        return True

    @staticmethod
    def default_config() -> Dict:
        return {
            'timeout_ms': 1000,
            'retry_attempts': 3
        }

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> list:
        return ['create_task', 'manage_dependencies', 'set_priority']


# Convenience function
async def create_task(
    task_type: str,
    assigned_to: str,
    depends_on: list = None,
    **kwargs
) -> Dict[str, Any]:
    """Create coordination task.

    Args:
        task_type: Type of task
        assigned_to: Agent ID
        depends_on: Optional dependencies
        **kwargs: Additional parameters

    Returns:
        Task creation result

    Example:
        >>> result = await create_task(
        ...     task_type='train-model',
        ...     assigned_to='ai-engineer',
        ...     depends_on=['load-data'],
        ...     priority='high'
        ... )
        >>> result['data']['task_id']
        'task-abc-123'
    """
    skill = CreateTaskSkill()
    return skill.execute({
        'type': task_type,
        'assigned_to': assigned_to,
        'depends_on': depends_on or [],
        **kwargs
    })
```

**8 Coordination Skills:**

1. **create_task.py** - Task creation with dependencies
2. **update_task_status.py** - State transition validation
3. **publish_event.py** - Pub/sub event publishing
4. **subscribe_events.py** - Event subscription patterns
5. **get_workflow_status.py** - Workflow state queries
6. **distribute_work.py** - Load-balanced distribution
7. **aggregate_results.py** - Result collection/merging
8. **coordinate_handoff.py** - Agent-to-agent handoffs

### 4.4 Phase 3A Testing Strategy

#### Unit Tests (95% Coverage Target)

```python
# tests/skills/test_all_skills.py

import pytest
from pathlib import Path
import sys

# Add skills to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'plugins/mycelium-core/skills'))


class TestPhase3ASkills:
    """Comprehensive test suite for Phase 3A skills."""

    @pytest.mark.parametrize('skill_id', [
        'agent-discovery',
        'coordination-protocol',
        'prompt-compressor',
        'token-budget-optimizer',
        'context-diff',
        'mycelium-orchestrator',
        'analytics-queries',
        'compression-pipeline'
    ])
    def test_skill_loads(self, skill_id):
        """Test all skills can be loaded."""
        from skill_loader import SkillLoader

        loader = SkillLoader()
        skill = loader.load(skill_id)

        assert skill is not None
        assert skill.version
        assert len(skill.capabilities) > 0

    @pytest.mark.parametrize('skill_id', [
        'agent-discovery',
        'coordination-protocol',
    ])
    def test_skill_performance(self, skill_id):
        """Test skills meet latency targets."""
        from skill_loader import SkillLoader

        loader = SkillLoader()
        skill = loader.load(skill_id)

        # Get target from registry
        registry = loader.get_registry()
        target_ms = registry[skill_id]['performance']['target_latency_ms']

        # Execute skill
        result = skill.execute(sample_params[skill_id])

        assert result['metadata']['latency_ms'] < target_ms

    def test_backward_compatibility(self):
        """Test existing workflows work with skills."""
        # Import old agent discovery
        from scripts.agent_discovery import AgentDiscovery

        # Import new skill
        from skills.agent_discovery import search_agents

        # Compare results
        old_discovery = AgentDiscovery(...)
        old_results = old_discovery.search("API design")

        new_results = search_agents("API design")

        # Should return similar agents
        old_ids = [r['id'] for r in old_results]
        new_ids = [r['id'] for r in new_results]

        # At least 80% overlap
        overlap = len(set(old_ids) & set(new_ids)) / len(old_ids)
        assert overlap >= 0.8
```

#### Integration Tests

```python
# tests/integration/test_skill_coordination.py

import pytest


class TestSkillCoordination:
    """Test skills work with coordination infrastructure."""

    @pytest.mark.asyncio
    async def test_skill_invocation_from_agent(self):
        """Test agent can invoke skill."""
        from skills.agent_discovery import search_agents

        # Simulate agent invoking skill
        results = search_agents("database optimization")

        assert len(results) > 0
        assert results[0]['id'] in [
            'database-optimizer',
            'postgres-pro',
            'database-administrator'
        ]

    @pytest.mark.asyncio
    async def test_skill_telemetry_integration(self):
        """Test skills integrate with Phase 2 analytics."""
        from skills.agent_discovery import AgentDiscoverySkill
        from mycelium_analytics import TelemetryCollector

        # Execute skill
        skill = AgentDiscoverySkill()
        skill.execute({'query': 'test'})

        # Check telemetry
        telemetry = TelemetryCollector()
        metrics = telemetry.get_skill_metrics('agent-discovery')

        assert metrics['total_calls'] > 0
        assert 'latency_p95' in metrics
```

---

## 5. Phase 3B: Architectural Foundation

### 5.1 Timeline & Architecture

**Duration:** 8 weeks
**Team:** 3 developers
**Risk Level:** MEDIUM

**Prerequisites:** Phase 3A gate criteria must pass

### 5.2 A1: Dynamic Skill Loading Architecture

#### Current vs Target

**Current (Static Loading):**
```javascript
// Startup: Load all 119 agents (820KB)
const agents = fs.readFileSync('agents/index.json');
const allAgents = JSON.parse(agents);  // 820KB in memory
```

**Target (Dynamic Loading):**
```javascript
// Startup: Load metadata only (15KB)
const registry = fs.readFileSync('skills/registry.json');
const skillMetadata = JSON.parse(registry);  // 15KB in memory

// Runtime: Load skills on-demand
async function invokeSkill(skillId, params) {
    const skill = await SkillLoader.load(skillId);  // JIT load
    return await skill.execute(params);
}
```

#### Implementation

**File:** `plugins/mycelium-core/skills/skill_loader.py`

```python
"""
Dynamic Skill Loader
Provides just-in-time skill loading with caching.

Performance targets:
- Registry load: <2ms
- Skill load (first): <5ms
- Skill load (cached): <0.5ms
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import importlib
import time


class SkillLoader:
    """JIT skill loading with caching."""

    def __init__(self, registry_path: Optional[Path] = None):
        """Initialize skill loader.

        Args:
            registry_path: Path to registry.json
        """
        self.registry_path = registry_path or Path(
            'plugins/mycelium-core/skills/registry.json'
        )

        # Load lightweight registry (metadata only)
        self.registry = self._load_registry()

        # Skill cache (loaded skills)
        self._cache: Dict[str, Any] = {}

        # Statistics
        self._stats = {
            'loads': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

    def _load_registry(self) -> Dict[str, Any]:
        """Load skill registry metadata.

        Returns:
            Registry dict with skill metadata
        """
        with open(self.registry_path) as f:
            return json.load(f)

    def load(self, skill_id: str) -> Any:
        """Load skill (with caching).

        Args:
            skill_id: Skill identifier

        Returns:
            Instantiated skill object

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        start_time = time.perf_counter()

        # Check cache
        if skill_id in self._cache:
            self._stats['cache_hits'] += 1
            return self._cache[skill_id]

        self._stats['cache_misses'] += 1
        self._stats['loads'] += 1

        # Get skill metadata
        skill_meta = self._get_skill_metadata(skill_id)

        if skill_meta is None:
            raise SkillNotFoundError(f"Skill not found: {skill_id}")

        # Dynamic import based on execution type
        exec_config = skill_meta['execution']

        if exec_config['type'] == 'python':
            # Import Python module
            module_path = exec_config['entry_point']
            module = self._import_python_module(module_path)

            # Get skill class
            skill_class = getattr(
                module,
                skill_meta.get('class_name', f"{skill_id.title()}Skill")
            )

            # Instantiate
            skill = skill_class()

        elif exec_config['type'] == 'javascript':
            # Import JS module (via Node bridge)
            raise NotImplementedError("JS skills not yet supported")

        else:
            raise ValueError(f"Unknown execution type: {exec_config['type']}")

        # Cache loaded skill
        self._cache[skill_id] = skill

        # Log load time
        load_time_ms = (time.perf_counter() - start_time) * 1000
        if load_time_ms > skill_meta['performance']['load_time_ms']:
            print(f"⚠️ Skill '{skill_id}' load time exceeded target: "
                  f"{load_time_ms:.2f}ms > "
                  f"{skill_meta['performance']['load_time_ms']}ms")

        return skill

    def _get_skill_metadata(self, skill_id: str) -> Optional[Dict]:
        """Get skill metadata from registry.

        Args:
            skill_id: Skill identifier

        Returns:
            Skill metadata or None
        """
        for skill in self.registry['skills']:
            if skill['id'] == skill_id:
                return skill
        return None

    def _import_python_module(self, module_path: str):
        """Dynamically import Python module.

        Args:
            module_path: Path to module (e.g., 'skills/agent-discovery/main.py')

        Returns:
            Imported module
        """
        # Convert path to module name
        module_name = module_path.replace('/', '.').replace('.py', '')

        # Import module
        return importlib.import_module(module_name)

    def get_capabilities(self) -> Dict[str, list]:
        """Get all available capabilities.

        Returns:
            Dict mapping capabilities to skill IDs

        Example:
            {
                'search_agents': ['agent-discovery'],
                'create_task': ['coordination-protocol'],
                ...
            }
        """
        capabilities = {}

        for skill in self.registry['skills']:
            for capability in skill.get('capabilities', []):
                if capability not in capabilities:
                    capabilities[capability] = []
                capabilities[capability].append(skill['id'])

        return capabilities

    def get_stats(self) -> Dict[str, int]:
        """Get loader statistics.

        Returns:
            Stats dict with loads, cache hits, etc.
        """
        return {
            **self._stats,
            'cache_size': len(self._cache),
            'cache_hit_rate': (
                self._stats['cache_hits'] /
                max(1, self._stats['cache_hits'] + self._stats['cache_misses'])
            ) * 100
        }

    def clear_cache(self):
        """Clear skill cache."""
        self._cache.clear()


class SkillNotFoundError(Exception):
    """Raised when skill is not found in registry."""
    pass
```

### 5.3 A2: Skill-Based Coordination Protocol

**Goal:** Replace message-passing with skill lending

**Before (Message-Passing - 2900ms):**
```javascript
// Agent A needs data analysis
await pubsub.publish('data:analyze', {
    dataset: 'customers.csv',
    operations: ['summary', 'trends']
});

// Wait for Agent B to process and respond
const result = await pubsub.subscribe('data:results');
```

**After (Skill Lending - 2001ms):**
```javascript
// Agent A borrows skill from Agent B
const analyzerSkill = await skillRegistry.borrow(
    'dataset-analyzer',
    from: 'data-engineer'
);

// Execute directly (no message overhead)
const result = await analyzerSkill.execute({
    dataset: 'customers.csv',
    operations: ['summary', 'trends']
});
```

**Implementation:** `plugins/mycelium-core/lib/skill_registry.js`

```javascript
/**
 * Skill Registry - Manages skill lending between agents
 */

export class SkillRegistry {
    constructor() {
        this.skills = new Map();
        this.borrowers = new Map();
    }

    /**
     * Register skill from agent
     */
    register(skillId, agent, skillImpl) {
        this.skills.set(skillId, {
            owner: agent,
            implementation: skillImpl,
            borrows: 0
        });
    }

    /**
     * Lend skill to another agent
     */
    async borrow(skillId, fromAgent) {
        const skill = this.skills.get(skillId);

        if (!skill) {
            throw new Error(`Skill not found: ${skillId}`);
        }

        // Create execution context for borrower
        const context = this._createContext(fromAgent);

        // Track borrow
        skill.borrows++;

        // Return wrapped skill with context
        return {
            execute: async (params) => {
                return await skill.implementation.execute(params, context);
            }
        };
    }

    _createContext(borrower) {
        return {
            borrower,
            timestamp: new Date().toISOString(),
            executionId: crypto.randomUUID()
        };
    }
}
```

---

## 6. Phase 3C: Advanced Intelligence

**Duration:** 12 weeks
**Team:** 4 developers
**Risk Level:** MEDIUM-HIGH

**Prerequisites:** Phase 3A + 3B gate criteria must pass

### 6.1 I1: Self-Optimizing Coordination Strategy

**Goal:** RL-based optimization of coordination patterns

**Implementation:** `skills/coordination-optimizer/main.py`

```python
"""
Self-Optimizing Coordination Strategy
Uses reinforcement learning to optimize workflow patterns.

Based on Phase 2 analytics telemetry.
"""

from typing import Dict, Any
import numpy as np


class CoordinationOptimizer:
    """RL-based coordination optimization."""

    def __init__(self):
        """Initialize optimizer with RL agent."""
        # Simplified Q-learning for demo
        self.q_table = {}  # (state, action) -> value
        self.learning_rate = 0.1
        self.discount_factor = 0.95

    def optimize(self, workflow_pattern: str) -> Dict[str, Any]:
        """Optimize coordination for workflow pattern.

        Args:
            workflow_pattern: Workflow identifier

        Returns:
            Optimized coordination strategy
        """
        # Analyze historical performance
        history = self._get_pattern_performance(workflow_pattern)

        # Train RL agent
        policy = self._train_policy(history)

        # Return optimal strategy
        return {
            'strategy': policy.get_action(current_state),
            'expected_improvement': policy.value_estimate(),
            'confidence': policy.confidence_score()
        }

    def _get_pattern_performance(self, pattern: str) -> list:
        """Get historical performance from Phase 2 analytics.

        Args:
            pattern: Workflow pattern

        Returns:
            List of historical executions
        """
        from mycelium_analytics import AnalyticsQuery

        query = AnalyticsQuery()
        return query.get_workflow_history(pattern, days=30)
```

---

## 7. Integration with Existing Systems

### 7.1 Integration with Agent Discovery (Phase 1)

**Existing:** `scripts/agent_discovery.py` (673 lines)

**Integration Strategy:**
1. **Week 1:** Extract core logic to skill
2. **Week 2-4:** Parallel operation (feature flag)
3. **Month 2:** Deprecate old system (6-month notice)

```python
# scripts/agent_discovery.py (LEGACY - Phase 3A migration)

class AgentDiscovery:
    """Legacy agent discovery (DEPRECATED after Phase 3A)."""

    def search(self, query: str):
        """Search agents (legacy method).

        DEPRECATED: Use skills.agent-discovery instead.
        Will be removed in Phase 3B (6 months).
        """
        import warnings
        warnings.warn(
            "AgentDiscovery.search() is deprecated. "
            "Use skills.agent_discovery.search_agents() instead.",
            DeprecationWarning,
            stacklevel=2
        )

        # Feature flag: Use skills if enabled
        from os import getenv
        if getenv('MYCELIUM_USE_SKILLS', 'false') == 'true':
            from skills.agent_discovery import search_agents
            return search_agents(query)

        # Legacy implementation
        return self._legacy_search(query)
```

### 7.2 Integration with Analytics (Phase 2)

**Existing:** `scripts/mycelium_analytics/`

**New:** `scripts/mycelium_analytics/skill_metrics.py`

```python
"""
Skill-specific analytics integration.
Extends Phase 2 telemetry for skill tracking.
"""

from typing import Dict, Any
from . import TelemetryCollector


class SkillTelemetry(TelemetryCollector):
    """Skill performance tracking."""

    def record_skill_execution(
        self,
        skill_id: str,
        operation: str,
        latency_ms: float,
        cache_hit: bool = False,
        **kwargs
    ):
        """Record skill execution metrics.

        Args:
            skill_id: Skill identifier
            operation: Operation name
            latency_ms: Execution latency
            cache_hit: Whether cache was used
            **kwargs: Additional metrics
        """
        self.record_event(
            event_type='skill_execution',
            data={
                'skill_id': skill_id,
                'operation': operation,
                'latency_ms': latency_ms,
                'cache_hit': cache_hit,
                **kwargs
            }
        )

    def get_skill_performance(
        self,
        skill_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get skill performance summary.

        Args:
            skill_id: Skill identifier
            days: Days of history

        Returns:
            Performance metrics
        """
        events = self.query_events(
            event_type='skill_execution',
            filters={'skill_id': skill_id},
            days=days
        )

        latencies = [e['latency_ms'] for e in events]

        return {
            'total_calls': len(events),
            'latency_p50': np.percentile(latencies, 50),
            'latency_p95': np.percentile(latencies, 95),
            'latency_p99': np.percentile(latencies, 99),
            'cache_hit_rate': sum(
                e['cache_hit'] for e in events
            ) / len(events) * 100
        }
```

### 7.3 Integration with Coordination Library

**Existing:** `plugins/mycelium-core/lib/coordination.js`

**Enhancement:** Add skill invocation support

```javascript
// plugins/mycelium-core/lib/skill_integration.js

import { PythonBridge } from './python_bridge.js';

/**
 * Invoke Python skill from JavaScript
 */
export async function invokeSkill(skillId, params) {
    const bridge = new PythonBridge();

    // Execute Python skill
    const result = await bridge.execute(
        'skills.skill_executor',
        'execute_skill',
        [skillId, params]
    );

    return result;
}

/**
 * Example: Invoke agent discovery from JS
 */
export async function searchAgents(query) {
    return await invokeSkill('agent-discovery', {
        query,
        max_results: 5
    });
}
```

---

## 8. Testing Strategy

### 8.1 Testing Pyramid

```
                 ▲
                / \
               /E2E\              10%  - End-to-end tests
              /-----\
             /Integr.\            30%  - Integration tests
            /---------\
           /   Unit    \          60%  - Unit tests
          /-------------\
```

### 8.2 Unit Tests (60% of tests)

**Coverage Target:** 95%

**Location:** `plugins/mycelium-core/skills/*/tests/`

**Example:** `skills/agent-discovery/tests/test_vectorizer.py`

```python
import pytest
from ..vectorizer import AgentVectorizer


class TestAgentVectorizer:
    """Unit tests for TF-IDF vectorizer."""

    @pytest.fixture
    def vectorizer(self):
        """Create test vectorizer."""
        return AgentVectorizer(
            index_path='fixtures/test_agents.json'
        )

    def test_vectorizer_initialization(self, vectorizer):
        """Test vectorizer loads agents."""
        assert len(vectorizer.agents) > 0
        assert vectorizer.vectorizer is not None

    def test_vectorizer_search(self, vectorizer):
        """Test search returns results."""
        results = vectorizer.search("API design")

        assert len(results) > 0
        assert all('agent_id' in r for r in results)
        assert all('score' in r for r in results)
        assert all(0 <= r['score'] <= 1 for r in results)

    def test_vectorizer_category_filter(self, vectorizer):
        """Test category filtering works."""
        results = vectorizer.search(
            "database",
            category_filter="infrastructure"
        )

        assert all(
            r['category'] == 'infrastructure'
            for r in results
        )
```

### 8.3 Integration Tests (30% of tests)

**Location:** `tests/integration/`

**Example:** `tests/integration/test_skill_workflow.py`

```python
import pytest


@pytest.mark.integration
class TestSkillWorkflow:
    """Integration tests for skill workflows."""

    @pytest.mark.asyncio
    async def test_agent_discovery_to_coordination(self):
        """Test agent discovery → task coordination flow."""
        from skills.agent_discovery import search_agents
        from skills.coordination_protocol import create_task

        # 1. Discover agents
        agents = search_agents("database optimization")
        assert len(agents) > 0

        # 2. Create task for top agent
        top_agent = agents[0]
        task = await create_task(
            task_type='optimize_db',
            assigned_to=top_agent['id']
        )

        assert task['data']['task_id']
        assert task['data']['status'] == 'created'

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete workflow: discovery → orchestration → execution."""
        from skills.mycelium_orchestrator import route_request

        # User request
        result = await route_request(
            query="Build a REST API for user management",
            constraints={'deadline': '2 days'}
        )

        # Verify orchestration plan
        assert result['agents']
        assert result['dag']
        assert result['estimated_cost_tokens']
```

### 8.4 Performance Tests

**Location:** `tests/benchmark/`

**Example:** `tests/benchmark/benchmark_skills.py`

```python
import pytest
import time


@pytest.mark.benchmark
class TestSkillPerformance:
    """Performance benchmarks for skills."""

    def test_agent_discovery_latency(self):
        """Test agent discovery meets <10ms target."""
        from skills.agent_discovery import search_agents

        # Warm up cache
        search_agents("test")

        # Benchmark
        latencies = []
        for _ in range(100):
            start = time.perf_counter()
            search_agents("API design")
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)

        # p95 should be < 10ms
        p95 = sorted(latencies)[95]
        assert p95 < 10, f"p95 latency {p95:.2f}ms exceeds target 10ms"

    def test_skill_loading_overhead(self):
        """Test skill loading is fast (<5ms)."""
        from skills.skill_loader import SkillLoader

        loader = SkillLoader()
        loader.clear_cache()

        # Measure first load
        start = time.perf_counter()
        skill = loader.load('agent-discovery')
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 5, f"Skill load {elapsed:.2f}ms exceeds target 5ms"
```

### 8.5 A/B Testing

**Location:** `tests/ab_testing/`

```python
# tests/ab_testing/test_discovery_comparison.py

import pytest
from typing import List, Dict


class TestAgentDiscoveryAB:
    """A/B test: Legacy vs Skill-based discovery."""

    def test_accuracy_comparison(self):
        """Compare accuracy of legacy vs skill-based."""
        # Test queries with known expected results
        test_cases = [
            ("API design", ["api-designer", "backend-developer"]),
            ("database optimization", ["database-optimizer", "postgres-pro"]),
            ("machine learning", ["ml-engineer", "ai-engineer"]),
        ]

        legacy_accuracy = self._test_legacy_discovery(test_cases)
        skill_accuracy = self._test_skill_discovery(test_cases)

        # Skill-based should be >= legacy accuracy
        assert skill_accuracy >= legacy_accuracy

    def test_latency_comparison(self):
        """Compare latency of legacy vs skill-based."""
        queries = ["API", "database", "frontend", "testing", "deployment"]

        legacy_latencies = self._benchmark_legacy(queries)
        skill_latencies = self._benchmark_skills(queries)

        # Skills should be faster
        assert skill_latencies['p95'] < legacy_latencies['p95']

    def _test_legacy_discovery(self, test_cases) -> float:
        """Test legacy discovery accuracy."""
        from scripts.agent_discovery import AgentDiscovery

        discovery = AgentDiscovery(...)
        correct = 0

        for query, expected in test_cases:
            results = discovery.search(query)
            result_ids = [r['id'] for r in results[:len(expected)]]

            # Check if any expected agents in results
            if any(exp in result_ids for exp in expected):
                correct += 1

        return correct / len(test_cases)

    def _test_skill_discovery(self, test_cases) -> float:
        """Test skill-based discovery accuracy."""
        from skills.agent_discovery import search_agents

        correct = 0

        for query, expected in test_cases:
            results = search_agents(query)
            result_ids = [r['id'] for r in results[:len(expected)]]

            if any(exp in result_ids for exp in expected):
                correct += 1

        return correct / len(test_cases)
```

---

## 9. Migration & Rollback

### 9.1 Migration Timeline

```
Month 1 (Phase 3A):
├── Week 1: Skills infrastructure + S1 + S7
├── Week 2: S8 + S3
├── Week 3: S2 (coordination suite)
└── Week 4: S4 + S6 + S5

Month 2-3 (Phase 3B):
├── Week 5-6: A1 (Dynamic loading)
├── Week 7-9: A2 + A3 (Coordination + Sharing)
├── Week 10-11: A4 (Context management)
└── Week 12: A5 (Marketplace)

Parallel Operation Period:
├── Months 1-3: Legacy + Skills both active
├── Month 4-6: Skills preferred, legacy deprecated
└── Month 7: Legacy removed

Deprecation Notices:
├── Month 1: Deprecation warnings in legacy code
├── Month 3: Update docs to recommend skills
├── Month 6: Final deprecation notice
└── Month 7: Legacy code removal
```

### 9.2 Feature Flags

**File:** `plugins/mycelium-core/config/feature_flags.json`

```json
{
  "skills_enabled": true,
  "skills_traffic_percent": 100,
  "legacy_fallback_enabled": true,

  "skills": {
    "agent_discovery": {
      "enabled": true,
      "traffic_percent": 100
    },
    "coordination_protocol": {
      "enabled": true,
      "traffic_percent": 100
    },
    "prompt_compressor": {
      "enabled": true,
      "traffic_percent": 80
    }
  },

  "rollback": {
    "auto_rollback_threshold_error_rate": 0.05,
    "auto_rollback_threshold_latency_p95_ms": 100
  }
}
```

### 9.3 Rollback Procedures

#### Emergency Rollback (Critical Failure)

```bash
#!/bin/bash
# bin/rollback-skills.sh

set -e

echo "🚨 EMERGENCY ROLLBACK: Disabling skills"

# 1. Disable all skills via feature flags
cat > plugins/mycelium-core/config/feature_flags.json <<EOF
{
  "skills_enabled": false,
  "legacy_fallback_enabled": true
}
EOF

# 2. Restart any services (if applicable)
# systemctl restart mycelium-coordination

# 3. Verify legacy system operational
python -c "from scripts.agent_discovery import AgentDiscovery; print('✅ Legacy system OK')"

# 4. Alert team
echo "⚠️ Skills disabled, legacy system active"
echo "Review logs: tail -f logs/skills-error.log"

echo "✅ Rollback complete. System using legacy code."
```

#### Gradual Rollback (Performance Issues)

```python
# scripts/gradual_rollback.py

"""
Gradually reduce skill traffic if performance degrades.
"""

import json
from pathlib import Path


def reduce_skill_traffic(skill_id: str, decrement: int = 10):
    """Reduce traffic to skill by X%.

    Args:
        skill_id: Skill to reduce
        decrement: Percentage to reduce
    """
    config_path = Path('plugins/mycelium-core/config/feature_flags.json')

    with open(config_path) as f:
        config = json.load(f)

    current_percent = config['skills'][skill_id]['traffic_percent']
    new_percent = max(0, current_percent - decrement)

    config['skills'][skill_id]['traffic_percent'] = new_percent

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"Reduced {skill_id} traffic: {current_percent}% → {new_percent}%")


# Example: Reduce prompt-compressor to 50% traffic
reduce_skill_traffic('prompt_compressor', decrement=30)
```

### 9.4 Backward Compatibility Tests

```python
# tests/backward_compat/test_legacy_compat.py

import pytest


class TestBackwardCompatibility:
    """Ensure skills don't break existing code."""

    def test_legacy_agent_discovery_still_works(self):
        """Test legacy AgentDiscovery class works."""
        from scripts.agent_discovery import AgentDiscovery

        discovery = AgentDiscovery(
            Path('plugins/mycelium-core/agents/index.json')
        )

        results = discovery.search("API design")
        assert len(results) > 0

    def test_legacy_coordination_still_works(self):
        """Test legacy CoordinationClient works."""
        from lib.coordination import CoordinationClient

        client = CoordinationClient()
        await client.initialize()

        task = await client.createTask({
            'type': 'test',
            'assigned_to': 'test-agent'
        })

        assert task.id

    def test_existing_workflows_unchanged(self):
        """Test existing workflow patterns work."""
        # Run 10 common workflow patterns
        workflows = [
            'api-design-workflow',
            'database-migration-workflow',
            'frontend-build-workflow',
            # ... etc
        ]

        for workflow_id in workflows:
            result = run_workflow(workflow_id)
            assert result.status == 'success'
```

---

## 10. Technical Risks & Mitigation

### 10.1 Risk Matrix

| Risk ID | Risk | Likelihood | Impact | Severity | Mitigation |
|---------|------|-----------|--------|----------|------------|
| **R1** | Skill execution failures | MEDIUM | HIGH | HIGH | Circuit breakers, fallbacks, comprehensive testing |
| **R2** | Backward compatibility breaks | LOW | HIGH | MEDIUM | Parallel operation, automated compat tests |
| **R3** | Performance regression | LOW | MEDIUM | LOW | Continuous benchmarking, A/B testing |
| **R4** | Team capacity constraints | HIGH | MEDIUM | HIGH | Phased approach, scope flexibility |
| **R5** | Claude API changes | MEDIUM | HIGH | HIGH | Abstraction layer, version pinning |
| **R6** | Data loss during migration | LOW | CRITICAL | MEDIUM | Comprehensive backups, validation |
| **R7** | Integration complexity | MEDIUM | MEDIUM | MEDIUM | Incremental integration, extensive testing |
| **R8** | Cache invalidation bugs | MEDIUM | MEDIUM | MEDIUM | Cache versioning, TTL management |

### 10.2 R1: Skill Execution Failures

**Mitigation Strategy:**

```python
# plugins/mycelium-core/skills/skill_executor.py

"""
Skill executor with circuit breaker pattern.
"""

from typing import Dict, Any
import time


class CircuitBreaker:
    """Circuit breaker for skill execution."""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            timeout: Seconds before attempting reset
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker.

        Args:
            func: Function to execute
            *args, **kwargs: Function arguments

        Returns:
            Function result or raises CircuitOpenError
        """
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise CircuitOpenError(
                    f"Circuit open for skill, too many failures"
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise


class SkillExecutor:
    """Execute skills with error handling and fallbacks."""

    def __init__(self):
        """Initialize executor."""
        self.circuit_breakers = {}
        self.fallback_enabled = True

    async def execute(
        self,
        skill_id: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute skill with error handling.

        Args:
            skill_id: Skill identifier
            params: Skill parameters

        Returns:
            Skill result or fallback result
        """
        # Get or create circuit breaker
        if skill_id not in self.circuit_breakers:
            self.circuit_breakers[skill_id] = CircuitBreaker()

        cb = self.circuit_breakers[skill_id]

        try:
            # Try skill execution with circuit breaker
            result = cb.call(self._execute_skill, skill_id, params)
            return result

        except CircuitOpenError:
            # Circuit open, use fallback immediately
            if self.fallback_enabled:
                return await self._fallback_to_legacy(skill_id, params)
            else:
                raise

        except Exception as e:
            # Skill execution error
            logger.error(f"Skill {skill_id} failed: {e}")

            # Try fallback
            if self.fallback_enabled:
                return await self._fallback_to_legacy(skill_id, params)
            else:
                raise

    async def _execute_skill(
        self,
        skill_id: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute skill (internal).

        Args:
            skill_id: Skill identifier
            params: Parameters

        Returns:
            Skill result
        """
        from .skill_loader import SkillLoader

        loader = SkillLoader()
        skill = loader.load(skill_id)

        return skill.execute(params)

    async def _fallback_to_legacy(
        self,
        skill_id: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback to legacy implementation.

        Args:
            skill_id: Skill identifier
            params: Parameters

        Returns:
            Legacy implementation result
        """
        logger.warning(
            f"Falling back to legacy for {skill_id}"
        )

        # Map skill_id to legacy function
        fallback_map = {
            'agent-discovery': self._legacy_agent_discovery,
            'coordination-protocol': self._legacy_coordination,
            # ... etc
        }

        if skill_id not in fallback_map:
            raise ValueError(f"No fallback for {skill_id}")

        return await fallback_map[skill_id](params)

    async def _legacy_agent_discovery(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Legacy agent discovery fallback."""
        from scripts.agent_discovery import AgentDiscovery

        discovery = AgentDiscovery(...)
        results = discovery.search(params['query'])

        return {
            'data': results,
            'metadata': {
                'fallback': True,
                'legacy_implementation': 'agent_discovery.py'
            }
        }
```

### 10.3 R4: Team Capacity Constraints

**Mitigation Strategy:**

**Scope Prioritization:**
```
MUST HAVE (Phase 3A):
- S1: Agent Discovery Skill
- S2: Coordination Protocol Suite
- S7: Analytics Query Skills

SHOULD HAVE (Phase 3A):
- S3: Prompt Compression Skill
- S6: Orchestration Meta-Skill

NICE TO HAVE (Phase 3A):
- S4: Token Budget Optimizer
- S5: Context Diff Compression
- S8: Compression Pipeline

DEFER IF NEEDED:
- Phase 3B (Architectural Foundation)
- Phase 3C (Advanced Intelligence)
```

**Community Contribution Strategy:**

```markdown
# docs/CONTRIBUTING_SKILLS.md

## Contributing Skills to Mycelium

We welcome community contributions! Here's how to create and submit a skill:

### 1. Create Skill
```bash
# Use skill generator
./bin/mycelium-skill create my-skill-name
```

### 2. Implement Skill
- Follow BaseSkill interface
- Add comprehensive tests (95% coverage)
- Document in README.md

### 3. Submit PR
- Add skill to registry.json
- Include usage examples
- Pass CI/CD checks

### 4. Review Process
- Code review by maintainers
- Performance validation
- Integration testing

### 5. Merge & Publish
- Merge to main branch
- Skill available in marketplace
- Community can use immediately
```

---

## 11. Summary & Next Steps

### 11.1 Architecture Decision Summary

| Decision | Rationale | Impact |
|----------|-----------|--------|
| **Phased Implementation** | Validate approach before full transformation | Low risk, iterative improvement |
| **Skills-First for Phase 3A** | Immediate value, minimal architectural change | 40-65% token reduction in 4 weeks |
| **Backward Compatibility** | Ensure existing workflows continue | Zero breaking changes, smooth transition |
| **Feature Flags** | Gradual rollout with easy rollback | Risk mitigation, A/B testing |
| **Skill Registry** | Central metadata management | <2ms startup, 98% memory reduction |
| **JIT Loading** | Load skills on-demand | 7x faster startup, reduced memory |
| **Circuit Breakers** | Graceful degradation on failures | >99.9% uptime target |

### 11.2 Implementation Checklist for PM

**Week 1 Prep (Before Development Starts):**
- [ ] Review and approve this architecture document
- [ ] Assemble 2-developer team for Phase 3A
- [ ] Set up development environment
- [ ] Create feature branch: `feat/skills-phase-3a`
- [ ] Set up CI/CD for skills testing
- [ ] Configure analytics for A/B testing

**Phase 3A Milestones:**
- [ ] Week 1: Foundation + S1 + S7 complete
- [ ] Week 2: S8 + S3 complete
- [ ] Week 3: S2 (8 coordination ops) complete
- [ ] Week 4: S4 + S6 + S5 complete
- [ ] Week 4: Gate criteria validation
- [ ] Week 4: Go/No-Go decision for Phase 3B

**Gate Criteria (Phase 3A → Phase 3B):**
- [ ] 40%+ token reduction measured
- [ ] 30%+ latency reduction measured
- [ ] <0.5% error rate (vs 2% baseline)
- [ ] 95%+ user acceptance (internal team)
- [ ] Zero critical bugs in production
- [ ] All 8 skills implemented and tested

**Technical Deliverables:**
- [ ] Skills infrastructure (registry, loader, executor)
- [ ] 8 tactical skills (S1-S8) with 95% test coverage
- [ ] Integration with Phase 2 analytics
- [ ] Feature flags and rollback procedures
- [ ] Migration guide and documentation
- [ ] Performance benchmarks

### 11.3 Files to Create

**Immediate (Week 1):**
1. `plugins/mycelium-core/skills/registry.json` - Skill registry
2. `plugins/mycelium-core/skills/base_skill.py` - Base interface
3. `plugins/mycelium-core/skills/skill_loader.py` - JIT loader
4. `plugins/mycelium-core/skills/skill_executor.py` - Execution engine
5. `plugins/mycelium-core/config/feature_flags.json` - Feature flags

**Phase 3A (Weeks 1-4):**
6. `skills/agent-discovery/` - S1 implementation
7. `skills/coordination-protocol/` - S2 implementation (8 files)
8. `skills/prompt-compressor/` - S3 implementation
9. `skills/token-budget-optimizer/` - S4 implementation
10. `skills/context-diff/` - S5 implementation
11. `skills/mycelium-orchestrator/` - S6 implementation
12. `skills/analytics-queries/` - S7 implementation
13. `skills/compression-pipeline/` - S8 implementation

**Documentation:**
14. `docs/SKILL_DEVELOPMENT_GUIDE.md` - How to create skills
15. `docs/MIGRATION_GUIDE_SKILLS.md` - Agent → Skill migration
16. `docs/CONTRIBUTING_SKILLS.md` - Community contributions

**Testing:**
17. `tests/skills/` - Unit tests for all skills
18. `tests/integration/` - Integration test suite
19. `tests/benchmark/` - Performance benchmarks
20. `tests/ab_testing/` - A/B comparison tests

### 11.4 Key Metrics to Track

**Phase 3A Success Metrics:**
- Token reduction: Target 40-65%, measure via Phase 2 analytics
- Latency reduction: Target 30-50%, measure p95
- Coordination overhead: Target 20% → 5%
- Cache hit rate: Target >90%
- Error rate: Target <0.5%
- User satisfaction: Target >95%

**Continuous Monitoring:**
- Skill execution latency (p50/p95/p99)
- Skill cache hit rates
- Skill error rates and failure modes
- Fallback activation frequency
- Token consumption trends
- User adoption rates

### 11.5 Developer Handoff

**This document provides:**
✅ Clear file locations and structure
✅ Complete code patterns and examples
✅ Integration points with existing systems
✅ Comprehensive testing strategy
✅ Risk mitigation and rollback procedures

**A developer can now:**
1. Create skill infrastructure (Week 1)
2. Implement S1-S8 skills (Weeks 1-4)
3. Write comprehensive tests (95% coverage)
4. Integrate with Phase 1 & Phase 2 systems
5. Deploy with feature flags and monitoring
6. Roll back if needed (emergency procedures)

**Project Manager can now:**
1. Create detailed project plan with milestones
2. Estimate effort and timeline (4 weeks Phase 3A)
3. Define demo scenarios (skills in action)
4. Set acceptance criteria (gate criteria)
5. Track progress against metrics
6. Make Go/No-Go decisions for Phase 3B/3C

---

**Document Status:** COMPLETE - Ready for PM Review
**Next Action:** PM to create project plan incorporating this architecture
**Questions:** Contact @claude-code-developer for technical clarifications

---

*This architecture specification transforms Mycelium's 130-agent ecosystem using Claude Code skills, delivering 40-65% token reduction in Phase 3A (4 weeks) with minimal risk, then enabling architectural transformation (Phase 3B) and advanced intelligence (Phase 3C) based on validated success.*
