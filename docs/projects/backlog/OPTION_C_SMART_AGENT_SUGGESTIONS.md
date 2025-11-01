# Option C: Smart Agent Suggestions

**Status**: Draft Backlog **Author**: @claude-code-developer + @project-manager **Created**: 2025-10-18 **Estimated
Effort**: 4-5 days (2-person team) **Complexity**: Medium **Dependencies**: Phase 1 (Lazy Loading), Optional: Option A
(Usage Analytics)

______________________________________________________________________

## Executive Summary

Intelligent **context-aware agent recommendation system** that automatically suggests the most relevant agents based on:

- Open files and their extensions
- Git branch names and recent commits
- User query semantics (TF-IDF similarity)
- Historical usage patterns (if Option A complete)

**Value Proposition**:

- **Discovery**: Users find relevant agents without manual search
- **Productivity**: Reduce time spent finding the right specialist
- **Onboarding**: New users discover agent capabilities organically
- **Data-Driven**: Recommendations improve over time with usage data

**Expected Impact**:

- 40-60% reduction in agent discovery time
- 30-50% increase in agent usage diversity
- 90%+ recommendation accuracy (top-5 includes relevant agent)

______________________________________________________________________

## Technical Architecture

### System Overview

```
┌─────────────────────────────────────────────────┐
│   Context Extractor                             │
│   ┌──────────────┐  ┌───────────────┐          │
│   │ File Parser  │  │ Git Analyzer  │          │
│   │ (.tsx→react) │  │ (branch→feat) │          │
│   └──────────────┘  └───────────────┘          │
│   ┌──────────────────────────────────┐         │
│   │  NLP Keyword Extractor (spaCy)   │         │
│   └──────────────────────────────────┘         │
└──────────────────┬──────────────────────────────┘
                   │ context_vector
                   ↓
┌─────────────────────────────────────────────────┐
│   Recommendation Engine (TF-IDF + Cosine Sim)   │
│   ┌──────────────────────────────────┐         │
│   │  Agent Corpus Vectorizer         │         │
│   │  (119 agent descriptions)        │         │
│   └──────────────────────────────────┘         │
│   ┌──────────────────────────────────┐         │
│   │  Similarity Scorer               │         │
│   │  (cosine similarity)             │         │
│   └──────────────────────────────────┘         │
│   ┌──────────────────────────────────┐         │
│   │  Redis Cache (5min TTL)          │         │
│   └──────────────────────────────────┘         │
└──────────────────┬──────────────────────────────┘
                   │ ranked_suggestions
                   ↓
┌─────────────────────────────────────────────────┐
│   CLI Integration (mycelium suggest)            │
│   - Context detection (auto)                    │
│   - Manual query support                        │
│   - Top-K ranking display                       │
└─────────────────────────────────────────────────┘
```

### Data Flow

```
User Query: "help with react components"
     ↓
[Context Extraction]
  - Keywords: react, components, frontend
  - File context: src/components/*.tsx
  - Git: branch=feat/new-component
     ↓
[Vectorization]
  - Context vector: [0.8 react, 0.6 frontend, 0.5 typescript, ...]
  - Agent vectors: pre-computed TF-IDF
     ↓
[Similarity Scoring]
  - Cosine similarity: context_vec · agent_vec
  - Scores: [("react-tanstack-developer", 0.92), ("nextjs-developer", 0.85), ...]
     ↓
[Ranking + Filtering]
  - Top-5 agents
  - Apply usage boost (if Option A available)
  - Filter out recently used (diversity)
     ↓
[Output]
  mycelium suggest
  → 1. react-tanstack-developer (92% match)
    2. nextjs-developer (85% match)
    3. frontend-specialist (78% match)
```

______________________________________________________________________

## Core Components

### 1. Context Extractor

**File**: `/home/gerald/git/mycelium/mycelium_recommender/context_extractor.py`

```python
"""Context extraction from files, git, and user queries.

Analyzes working directory context to extract relevant keywords for
agent recommendation. Supports file type detection, git branch/commit
parsing, and NLP-based query understanding.

Author: @claude-code-developer + @ml-engineer
Date: 2025-10-18
"""

import subprocess
from pathlib import Path
from typing import Any
import re


class ContextExtractor:
    """Extracts context keywords from environment.

    Analyzes open files, git state, and user queries to build a semantic
    context vector for agent recommendation.

    Example:
        >>> extractor = ContextExtractor()
        >>> context = extractor.extract_from_files([Path("src/components/Button.tsx")])
        >>> "react" in context
        True
        >>> "typescript" in context
        True
    """

    # File extension → keyword mapping
    FILE_TYPE_KEYWORDS = {
        # Frontend
        ".tsx": ["react", "typescript", "frontend", "component"],
        ".jsx": ["react", "javascript", "frontend", "component"],
        ".ts": ["typescript", "javascript"],
        ".js": ["javascript"],
        ".vue": ["vue", "frontend", "component"],
        ".svelte": ["svelte", "frontend", "component"],
        ".css": ["css", "styling", "frontend"],
        ".scss": ["sass", "css", "styling", "frontend"],
        ".html": ["html", "frontend", "markup"],

        # Backend
        ".py": ["python", "backend"],
        ".go": ["golang", "backend"],
        ".rs": ["rust", "backend"],
        ".java": ["java", "backend"],
        ".rb": ["ruby", "backend"],
        ".php": ["php", "backend"],

        # Infrastructure
        ".yaml": ["yaml", "config", "infrastructure"],
        ".yml": ["yaml", "config", "infrastructure"],
        ".toml": ["toml", "config"],
        ".json": ["json", "config"],
        ".dockerfile": ["docker", "container", "infrastructure"],
        "Dockerfile": ["docker", "container", "infrastructure"],
        "docker-compose.yml": ["docker", "compose", "infrastructure"],

        # Data
        ".sql": ["sql", "database", "data"],
        ".graphql": ["graphql", "api", "data"],
        ".proto": ["protobuf", "grpc", "api"],

        # ML/AI
        ".ipynb": ["jupyter", "python", "data-science", "ml"],
        ".pkl": ["python", "ml", "model"],
        ".h5": ["keras", "tensorflow", "ml"],
        ".pt": ["pytorch", "ml"],

        # Documentation
        ".md": ["documentation", "markdown"],
        ".rst": ["documentation", "restructuredtext"],
        ".tex": ["latex", "documentation"],

        # Testing
        "test_*.py": ["testing", "pytest", "python"],
        "*_test.go": ["testing", "golang"],
        "*.test.ts": ["testing", "typescript", "jest"],
        "*.spec.ts": ["testing", "typescript", "jest"],
    }

    # Directory name → keyword mapping
    DIR_KEYWORDS = {
        "src": ["source", "code"],
        "tests": ["testing", "quality"],
        "docs": ["documentation"],
        "frontend": ["frontend", "ui"],
        "backend": ["backend", "api"],
        "api": ["api", "backend"],
        "components": ["react", "vue", "component", "frontend"],
        "services": ["backend", "service"],
        "models": ["data", "database", "ml"],
        "utils": ["utility", "helper"],
        "config": ["configuration", "settings"],
        "scripts": ["automation", "tooling"],
        "infra": ["infrastructure", "devops"],
        "infrastructure": ["infrastructure", "devops"],
        ".github": ["ci-cd", "github", "automation"],
        ".gitlab": ["ci-cd", "gitlab", "automation"],
    }

    def extract_from_files(self, file_paths: list[Path]) -> str:
        """Extract keywords from open files.

        Analyzes file extensions and directory names to infer context.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            Space-separated keyword string

        Example:
            >>> extractor = ContextExtractor()
            >>> context = extractor.extract_from_files([
            ...     Path("src/components/Button.tsx"),
            ...     Path("tests/unit/test_button.py")
            ... ])
            >>> "react" in context and "testing" in context
            True
        """
        keywords = set()

        for path in file_paths:
            # Extract from file extension
            suffix = path.suffix.lower()
            if suffix in self.FILE_TYPE_KEYWORDS:
                keywords.update(self.FILE_TYPE_KEYWORDS[suffix])

            # Special case: full filename patterns
            filename = path.name
            if filename.startswith("test_") or filename.endswith("_test.py"):
                keywords.update(["testing", "pytest", "python"])
            if filename == "Dockerfile":
                keywords.update(["docker", "container", "infrastructure"])

            # Extract from directory names
            for part in path.parts:
                part_lower = part.lower()
                if part_lower in self.DIR_KEYWORDS:
                    keywords.update(self.DIR_KEYWORDS[part_lower])

        return " ".join(keywords)

    def extract_from_git(self) -> str:
        """Extract context from git branch and recent commits.

        Parses branch name and commit messages for semantic keywords.

        Returns:
            Space-separated keyword string

        Example:
            >>> extractor = ContextExtractor()
            >>> context = extractor.extract_from_git()
            >>> len(context) > 0  # May be empty if not in git repo
            True
        """
        keywords = set()

        try:
            # Get current branch name
            branch = subprocess.check_output(
                ["git", "branch", "--show-current"],
                stderr=subprocess.DEVNULL
            ).decode().strip()

            # Parse branch name (e.g., feat/api-redesign → api, redesign)
            branch_keywords = re.findall(r'[a-z]+', branch.lower())
            keywords.update(branch_keywords)

            # Get recent commit messages (last 5)
            commits = subprocess.check_output(
                ["git", "log", "--oneline", "-5"],
                stderr=subprocess.DEVNULL
            ).decode().strip().split('\n')

            for commit in commits:
                # Extract words from commit message
                commit_words = re.findall(r'[a-z]{3,}', commit.lower())
                keywords.update(commit_words)

        except (subprocess.CalledProcessError, FileNotFoundError):
            # Not a git repo or git not available
            pass

        return " ".join(keywords)

    def extract_from_query(self, query: str) -> str:
        """Extract keywords from user query using NLP.

        Uses simple word extraction for now. Can be enhanced with spaCy
        for entity recognition and keyword extraction.

        Args:
            query: User's natural language query

        Returns:
            Space-separated keyword string

        Example:
            >>> extractor = ContextExtractor()
            >>> context = extractor.extract_from_query("help with react components")
            >>> "react" in context and "components" in context
            True
        """
        # Simple approach: extract alphanumeric words
        keywords = re.findall(r'\b[a-z]{3,}\b', query.lower())

        # TODO: Enhance with spaCy for:
        # - Named entity recognition
        # - Keyword extraction (RAKE, TF-IDF)
        # - Synonym expansion

        return " ".join(keywords)

    def extract_full_context(
        self,
        query: str | None = None,
        file_paths: list[Path] | None = None,
        include_git: bool = True
    ) -> str:
        """Extract comprehensive context from all sources.

        Combines query, file, and git context into single keyword string.

        Args:
            query: Optional user query
            file_paths: Optional file paths
            include_git: Whether to include git context

        Returns:
            Combined keyword string

        Example:
            >>> extractor = ContextExtractor()
            >>> context = extractor.extract_full_context(
            ...     query="optimize database queries",
            ...     file_paths=[Path("src/models/user.py")]
            ... )
            >>> "database" in context and "python" in context
            True
        """
        all_keywords = []

        if query:
            all_keywords.append(self.extract_from_query(query))

        if file_paths:
            all_keywords.append(self.extract_from_files(file_paths))

        if include_git:
            all_keywords.append(self.extract_from_git())

        # Combine and deduplicate
        combined = " ".join(all_keywords)
        unique_keywords = list(dict.fromkeys(combined.split()))  # Preserve order

        return " ".join(unique_keywords)
```

______________________________________________________________________

### 2. Recommendation Engine

**File**: `/home/gerald/git/mycelium/mycelium_recommender/recommender.py`

```python
"""TF-IDF based agent recommendation engine.

Uses scikit-learn TF-IDF vectorization and cosine similarity to rank
agents by relevance to user context. Includes Redis caching for fast
repeated queries.

Author: @claude-code-developer + @ml-engineer
Date: 2025-10-18
"""

from pathlib import Path
from typing import Any
import pickle
import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from scripts.agent_discovery import AgentDiscovery


class AgentRecommender:
    """Recommends agents based on TF-IDF similarity.

    Pre-computes TF-IDF vectors for all agent descriptions, then scores
    context queries against the corpus using cosine similarity.

    Attributes:
        discovery: AgentDiscovery instance
        vectorizer: TfidfVectorizer for text vectorization
        agent_vectors: Pre-computed agent TF-IDF vectors
        agent_ids: Ordered list of agent IDs

    Example:
        >>> discovery = AgentDiscovery(Path("plugins/mycelium-core/agents/index.json"))
        >>> recommender = AgentRecommender(discovery)
        >>> suggestions = recommender.suggest("react typescript frontend", top_k=5)
        >>> len(suggestions) == 5
        True
        >>> suggestions[0][1] > suggestions[-1][1]  # Scores descending
        True
    """

    def __init__(
        self,
        discovery: AgentDiscovery,
        cache_ttl_seconds: int = 300,  # 5 minutes
        use_redis: bool = True
    ):
        """Initialize recommender with agent discovery.

        Args:
            discovery: AgentDiscovery instance
            cache_ttl_seconds: Cache TTL for recommendations
            use_redis: Whether to use Redis for caching

        Example:
            >>> discovery = AgentDiscovery(Path("plugins/mycelium-core/agents/index.json"))
            >>> recommender = AgentRecommender(discovery)
            >>> recommender.agent_ids is not None
            True
        """
        self.discovery = discovery
        self.cache_ttl = cache_ttl_seconds
        self.use_redis = use_redis

        # Initialize TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=500,  # Limit vocabulary size
            ngram_range=(1, 2),  # Unigrams and bigrams
            stop_words='english',
            lowercase=True,
        )

        # Build corpus and vectorize
        self._build_corpus()

        # Initialize Redis client if available
        self.redis_client = None
        if use_redis:
            try:
                import redis
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    decode_responses=False  # Binary for pickle
                )
            except Exception:
                # Redis unavailable - continue without cache
                pass

    def _build_corpus(self) -> None:
        """Build TF-IDF corpus from agent descriptions.

        Loads all agent metadata and vectorizes descriptions + keywords
        into TF-IDF feature vectors.
        """
        agents = self.discovery.list_agents()

        # Build corpus: description + keywords
        self.corpus = []
        self.agent_ids = []
        self.agent_metadata = []

        for agent in agents:
            # Combine description and keywords for richer matching
            description = agent.get('description', '')
            keywords = ' '.join(agent.get('keywords', []))
            category = agent.get('category', '')

            combined = f"{description} {keywords} {category}"
            self.corpus.append(combined)
            self.agent_ids.append(agent['id'])
            self.agent_metadata.append(agent)

        # Vectorize corpus
        self.agent_vectors = self.vectorizer.fit_transform(self.corpus)

    def suggest(
        self,
        context: str,
        top_k: int = 5,
        min_similarity: float = 0.1,
        exclude_agents: list[str] | None = None,
        usage_boost: bool = False
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """Suggest top-k agents based on context.

        Args:
            context: Context string (keywords from ContextExtractor)
            top_k: Number of suggestions to return
            min_similarity: Minimum similarity threshold (0-1)
            exclude_agents: Optional list of agent IDs to exclude
            usage_boost: Boost scores using usage analytics (requires Option A)

        Returns:
            List of (agent_id, similarity_score, metadata) tuples:
            [
                ("react-tanstack-developer", 0.92, {...}),
                ("nextjs-developer", 0.85, {...}),
                ...
            ]

        Example:
            >>> recommender = AgentRecommender(discovery)
            >>> suggestions = recommender.suggest("python testing pytest", top_k=3)
            >>> len(suggestions) <= 3
            True
            >>> all(0 <= score <= 1 for _, score, _ in suggestions)
            True
        """
        # Check cache first
        cache_key = self._get_cache_key(context, top_k, exclude_agents)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        # Vectorize context query
        context_vector = self.vectorizer.transform([context])

        # Compute cosine similarity
        similarities = cosine_similarity(context_vector, self.agent_vectors)[0]

        # Create (agent_id, score, metadata) tuples
        scored_agents = [
            (self.agent_ids[i], similarities[i], self.agent_metadata[i])
            for i in range(len(self.agent_ids))
        ]

        # Filter by minimum similarity
        scored_agents = [
            (aid, score, meta)
            for aid, score, meta in scored_agents
            if score >= min_similarity
        ]

        # Exclude agents
        if exclude_agents:
            scored_agents = [
                (aid, score, meta)
                for aid, score, meta in scored_agents
                if aid not in exclude_agents
            ]

        # Apply usage boost (if Option A available)
        if usage_boost:
            scored_agents = self._apply_usage_boost(scored_agents)

        # Sort by score (descending)
        scored_agents.sort(key=lambda x: x[1], reverse=True)

        # Take top-k
        suggestions = scored_agents[:top_k]

        # Cache results
        self._put_in_cache(cache_key, suggestions)

        return suggestions

    def suggest_by_category(
        self,
        context: str,
        category: str,
        top_k: int = 3
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """Suggest agents within specific category.

        Args:
            context: Context string
            category: Agent category to filter
            top_k: Number of suggestions

        Returns:
            List of (agent_id, score, metadata) tuples

        Example:
            >>> recommender = AgentRecommender(discovery)
            >>> suggestions = recommender.suggest_by_category(
            ...     "api design",
            ...     category="core-development",
            ...     top_k=3
            ... )
            >>> all(s[2]['category'] == 'core-development' for s in suggestions)
            True
        """
        # Get all suggestions
        all_suggestions = self.suggest(context, top_k=100, min_similarity=0.0)

        # Filter by category
        category_suggestions = [
            (aid, score, meta)
            for aid, score, meta in all_suggestions
            if meta.get('category') == category
        ]

        return category_suggestions[:top_k]

    def explain_suggestion(
        self,
        agent_id: str,
        context: str
    ) -> dict[str, Any]:
        """Explain why agent was suggested.

        Returns feature weights and matched keywords.

        Args:
            agent_id: Agent ID to explain
            context: Context used for recommendation

        Returns:
            Explanation dictionary:
            {
                "agent_id": "react-tanstack-developer",
                "similarity_score": 0.92,
                "matched_keywords": ["react", "typescript", "frontend"],
                "top_features": [("react", 0.45), ("frontend", 0.32), ...],
            }

        Example:
            >>> recommender = AgentRecommender(discovery)
            >>> explanation = recommender.explain_suggestion(
            ...     "react-tanstack-developer",
            ...     "react typescript"
            ... )
            >>> "matched_keywords" in explanation
            True
        """
        # Get agent index
        try:
            agent_idx = self.agent_ids.index(agent_id)
        except ValueError:
            return {"error": f"Agent not found: {agent_id}"}

        # Vectorize context
        context_vector = self.vectorizer.transform([context])
        agent_vector = self.agent_vectors[agent_idx]

        # Compute similarity
        similarity = cosine_similarity(context_vector, agent_vector)[0][0]

        # Get feature names and weights
        feature_names = self.vectorizer.get_feature_names_out()
        context_features = context_vector.toarray()[0]
        agent_features = agent_vector.toarray()[0]

        # Find matched features (both context and agent have non-zero weight)
        matched_features = [
            (feature_names[i], context_features[i] * agent_features[i])
            for i in range(len(feature_names))
            if context_features[i] > 0 and agent_features[i] > 0
        ]

        # Sort by weight (descending)
        matched_features.sort(key=lambda x: x[1], reverse=True)

        # Extract matched keywords
        matched_keywords = [kw for kw, _ in matched_features[:10]]

        return {
            "agent_id": agent_id,
            "similarity_score": round(similarity, 4),
            "matched_keywords": matched_keywords,
            "top_features": [(kw, round(weight, 4)) for kw, weight in matched_features[:5]],
        }

    def _apply_usage_boost(
        self,
        scored_agents: list[tuple[str, float, dict]]
    ) -> list[tuple[str, float, dict]]:
        """Boost scores based on usage popularity (requires Option A).

        Args:
            scored_agents: List of (agent_id, score, metadata)

        Returns:
            Boosted list of (agent_id, adjusted_score, metadata)
        """
        try:
            from mycelium_analytics import EventStorage
            from mycelium_analytics.metrics import UsageAnalyzer

            storage = EventStorage()
            usage_analyzer = UsageAnalyzer(storage)
            ranking = usage_analyzer.get_popularity_ranking(days=30)

            # Create usage score map (percentile)
            usage_scores = {}
            for i, agent_data in enumerate(ranking):
                percentile = (len(ranking) - i) / len(ranking)
                usage_scores[agent_data['agent_id_hash']] = percentile

            # Apply boost (multiply similarity by usage percentile)
            boosted = []
            for agent_id, score, meta in scored_agents:
                # Hash agent_id to match analytics
                agent_hash = hashlib.sha256(agent_id.encode()).hexdigest()[:8]
                usage_percentile = usage_scores.get(agent_hash, 0.5)  # Default: median

                # Boost formula: score * (1 + 0.2 * usage_percentile)
                # Top agents get +20% boost, bottom agents get 0% boost
                boosted_score = score * (1 + 0.2 * usage_percentile)
                boosted.append((agent_id, boosted_score, meta))

            return boosted

        except Exception:
            # Usage analytics unavailable - return original scores
            return scored_agents

    def _get_cache_key(
        self,
        context: str,
        top_k: int,
        exclude_agents: list[str] | None
    ) -> str:
        """Generate cache key for recommendation request."""
        exclude_str = ",".join(sorted(exclude_agents)) if exclude_agents else ""
        key_input = f"{context}|{top_k}|{exclude_str}"
        return hashlib.sha256(key_input.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> list | None:
        """Retrieve recommendations from Redis cache."""
        if self.redis_client is None:
            return None

        try:
            cached_data = self.redis_client.get(f"mycelium:rec:{cache_key}")
            if cached_data:
                return pickle.loads(cached_data)
        except Exception:
            pass

        return None

    def _put_in_cache(self, cache_key: str, suggestions: list) -> None:
        """Store recommendations in Redis cache."""
        if self.redis_client is None:
            return

        try:
            serialized = pickle.dumps(suggestions)
            self.redis_client.setex(
                f"mycelium:rec:{cache_key}",
                self.cache_ttl,
                serialized
            )
        except Exception:
            pass  # Cache write failure - not critical
```

______________________________________________________________________

### 3. CLI Integration

**File**: `/home/gerald/git/mycelium/scripts/mycelium_suggest.py`

```python
#!/usr/bin/env python3
"""CLI tool for smart agent suggestions.

Usage:
    # Auto-detect context from working directory
    mycelium suggest

    # Manual query
    mycelium suggest "help with react components"

    # Suggest within category
    mycelium suggest "api design" --category core-development

    # Explain why agent was suggested
    mycelium suggest --explain react-tanstack-developer --query "react frontend"

Author: @claude-code-developer
Date: 2025-10-18
"""

import argparse
import subprocess
from pathlib import Path
from mycelium_recommender.context_extractor import ContextExtractor
from mycelium_recommender.recommender import AgentRecommender
from scripts.agent_discovery import AgentDiscovery


def auto_detect_files() -> list[Path]:
    """Auto-detect recently modified files in working directory.

    Returns:
        List of recently modified file paths (last 10)
    """
    try:
        # Get recently modified files (git-aware)
        result = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()

        if result:
            return [Path(p) for p in result.split('\n')[:10]]
        else:
            # Fallback: list files in current directory
            return list(Path.cwd().rglob("*.py"))[:10]
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not a git repo - use current directory
        return list(Path.cwd().rglob("*.*"))[:10]


def cmd_suggest(args):
    """Suggest agents based on context."""
    # Initialize components
    index_path = Path("plugins/mycelium-core/agents/index.json")
    discovery = AgentDiscovery(index_path)
    recommender = AgentRecommender(discovery, use_redis=True)
    extractor = ContextExtractor()

    # Extract context
    if args.query:
        # Manual query
        context = extractor.extract_from_query(args.query)
    else:
        # Auto-detect from environment
        file_paths = auto_detect_files()
        context = extractor.extract_full_context(
            file_paths=file_paths,
            include_git=True
        )

    print(f"\n=== Agent Suggestions ===\n")
    print(f"Context: {context}\n")

    # Get suggestions
    if args.category:
        suggestions = recommender.suggest_by_category(
            context,
            category=args.category,
            top_k=args.top_k
        )
    else:
        suggestions = recommender.suggest(
            context,
            top_k=args.top_k,
            usage_boost=args.use_analytics
        )

    if not suggestions:
        print("No suggestions found. Try a different query or context.")
        return

    # Display suggestions
    for i, (agent_id, score, metadata) in enumerate(suggestions, 1):
        percentage = int(score * 100)
        print(f"{i}. {agent_id}")
        print(f"   Match: {percentage}%")
        print(f"   Category: {metadata.get('category', 'unknown')}")
        print(f"   Description: {metadata.get('description', '')[:80]}...")
        print()

    # Show how to invoke
    top_agent = suggestions[0][0]
    print(f"To use top suggestion: claude --agents {top_agent}")


def cmd_explain(args):
    """Explain why agent was suggested."""
    index_path = Path("plugins/mycelium-core/agents/index.json")
    discovery = AgentDiscovery(index_path)
    recommender = AgentRecommender(discovery)
    extractor = ContextExtractor()

    # Extract context
    context = extractor.extract_from_query(args.query)

    # Get explanation
    explanation = recommender.explain_suggestion(args.agent_id, context)

    print(f"\n=== Explanation: {args.agent_id} ===\n")
    print(f"Similarity Score: {explanation['similarity_score']:.2%}")
    print(f"\nMatched Keywords:")
    for keyword in explanation['matched_keywords']:
        print(f"  - {keyword}")
    print(f"\nTop Features:")
    for feature, weight in explanation['top_features']:
        print(f"  - {feature}: {weight:.4f}")


def main():
    parser = argparse.ArgumentParser(description="Smart agent suggestions")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Suggest command
    suggest_parser = subparsers.add_parser("suggest", help="Suggest agents")
    suggest_parser.add_argument("query", nargs="?", help="Optional query (auto-detect if omitted)")
    suggest_parser.add_argument("--category", help="Filter by category")
    suggest_parser.add_argument("--top-k", type=int, default=5, help="Number of suggestions")
    suggest_parser.add_argument("--use-analytics", action="store_true", help="Boost with usage data")

    # Explain command
    explain_parser = subparsers.add_parser("explain", help="Explain suggestion")
    explain_parser.add_argument("--agent-id", required=True, help="Agent ID to explain")
    explain_parser.add_argument("--query", required=True, help="Query context")

    args = parser.parse_args()

    if args.command == "suggest" or args.command is None:
        # Default to suggest if no command
        if not hasattr(args, 'query'):
            args.query = None
            args.category = None
            args.top_k = 5
            args.use_analytics = False
        cmd_suggest(args)
    elif args.command == "explain":
        cmd_explain(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

______________________________________________________________________

## Testing Strategy

### Unit Tests

```python
"""Unit tests for recommendation system."""

import pytest
from pathlib import Path
from mycelium_recommender.context_extractor import ContextExtractor
from mycelium_recommender.recommender import AgentRecommender
from scripts.agent_discovery import AgentDiscovery


def test_context_extraction_from_files():
    """Test file context extraction."""
    extractor = ContextExtractor()
    context = extractor.extract_from_files([
        Path("src/components/Button.tsx"),
        Path("tests/test_api.py")
    ])

    assert "react" in context
    assert "typescript" in context
    assert "testing" in context


def test_recommendation_ranking():
    """Test recommendation ranking."""
    index_path = Path("plugins/mycelium-core/agents/index.json")
    discovery = AgentDiscovery(index_path)
    recommender = AgentRecommender(discovery)

    suggestions = recommender.suggest("react typescript frontend", top_k=5)

    assert len(suggestions) <= 5
    assert all(0 <= score <= 1 for _, score, _ in suggestions)
    # Scores should be descending
    assert suggestions[0][1] >= suggestions[-1][1]


def test_category_filtering():
    """Test category-specific suggestions."""
    index_path = Path("plugins/mycelium-core/agents/index.json")
    discovery = AgentDiscovery(index_path)
    recommender = AgentRecommender(discovery)

    suggestions = recommender.suggest_by_category(
        "api design",
        category="core-development",
        top_k=3
    )

    assert all(meta['category'] == 'core-development' for _, _, meta in suggestions)


def test_cache_hit():
    """Test Redis caching."""
    index_path = Path("plugins/mycelium-core/agents/index.json")
    discovery = AgentDiscovery(index_path)
    recommender = AgentRecommender(discovery, use_redis=True)

    # First call (cache miss)
    suggestions1 = recommender.suggest("python testing", top_k=3)

    # Second call (cache hit)
    suggestions2 = recommender.suggest("python testing", top_k=3)

    assert suggestions1 == suggestions2


def test_min_similarity_threshold():
    """Test minimum similarity filtering."""
    index_path = Path("plugins/mycelium-core/agents/index.json")
    discovery = AgentDiscovery(index_path)
    recommender = AgentRecommender(discovery)

    # Very specific query - should have few high-similarity matches
    suggestions = recommender.suggest(
        "obscure niche technology xyz123",
        min_similarity=0.5,
        top_k=10
    )

    assert all(score >= 0.5 for _, score, _ in suggestions)
```

______________________________________________________________________

## Implementation Timeline

### Day 1: Context Extraction

- Build `ContextExtractor` class
- File type → keyword mapping
- Git branch/commit parsing
- Unit tests (100% coverage)

### Day 2: TF-IDF Recommender

- Build `AgentRecommender` class
- Corpus vectorization
- Cosine similarity scoring
- Unit tests

### Day 3: CLI Integration

- Build `mycelium suggest` CLI
- Auto-detection logic
- Category filtering
- Integration tests

### Day 4: Caching + Optimization

- Redis caching layer
- Performance optimization
- Usage boost integration (Option A)
- Benchmark performance

### Day 5: Polish + Documentation

- Explanation feature
- Edge case handling
- Documentation
- Demo to team

**Total**: 4-5 days for 2-person team

______________________________________________________________________

## Effort Estimate

**Complexity**: Medium (NLP + ML)

**Team Composition**:

- 1x @python-pro (lead developer)
- 1x @ml-engineer (TF-IDF, scikit-learn)

**Breakdown**:

- Context extraction: 1 day
- TF-IDF recommender: 1.5 days
- CLI integration: 1 day
- Caching + optimization: 1 day
- Polish + docs: 0.5 days

**Total**: 4-5 days

______________________________________________________________________

## Dependencies

**Required**:

- Phase 1 (Lazy Loading + AgentDiscovery) (✅ Complete)
- scikit-learn (TF-IDF vectorization)
- Redis (for caching)

**Optional**:

- Option A (Usage Analytics) for usage boost
- spaCy (for advanced NLP - can add later)

**Installation**:

```bash
uv pip install scikit-learn redis
```

______________________________________________________________________

## Success Metrics

**Acceptance Criteria**:

1. ✅ Context extraction from files, git, and queries
1. ✅ TF-IDF recommendation with top-K ranking
1. ✅ CLI tool with auto-detection
1. ✅ Redis caching (5min TTL)
1. ✅ Category filtering support
1. ✅ Explanation feature (matched keywords)
1. ✅ 100% test coverage (unit + integration)

**Performance Targets**:

- Recommendation latency: p95 \< 100ms (cached)
- Recommendation latency: p95 \< 500ms (uncached)
- Accuracy: 90%+ (top-5 includes relevant agent)
- Cache hit rate: >70% for repeat queries

______________________________________________________________________

## Risk Assessment

**Technical Risks**: MEDIUM

- TF-IDF accuracy depends on corpus quality
- Context extraction may miss implicit intent
- Requires Redis for optimal performance

**Blockers**: NONE

- All dependencies available

**Mitigation**:

- Test with diverse queries during development
- Provide manual query override
- Graceful degradation without Redis

______________________________________________________________________

## Future Enhancements

**Phase 2 (Advanced ML)**:

- Replace TF-IDF with BERT embeddings (semantic similarity)
- Add user feedback loop (thumbs up/down on suggestions)
- Personalization based on user's historical agent usage
- Multi-modal context (include code snippets, not just filenames)

______________________________________________________________________

## Conclusion

Option C provides **intelligent agent discovery** using proven NLP techniques (TF-IDF + cosine similarity). Low
complexity, high value, and sets foundation for future ML enhancements.

**Recommendation**: **APPROVED for Sprint Planning** (implement after Phase 1 complete)

______________________________________________________________________

**Next Steps**:

1. Approve backlog item
1. Install dependencies (`scikit-learn`, `redis`)
1. Assign to @python-pro + @ml-engineer
1. Build MVP with file context + TF-IDF
1. Iterate based on user feedback
