# Source: projects/backlog/OPTION_C_SMART_AGENT_SUGGESTIONS.md
# Line: 383
# Valid syntax: True
# Has imports: True
# Has assignments: True

"""TF-IDF based agent recommendation engine.

Uses scikit-learn TF-IDF vectorization and cosine similarity to rank
agents by relevance to user context. Includes Redis caching for fast
repeated queries.

Author: @claude-code-developer + @ml-engineer
Date: 2025-10-18
"""

import hashlib
import pickle
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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
