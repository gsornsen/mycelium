# Source: projects/backlog/OPTION_C_SMART_AGENT_SUGGESTIONS.md
# Line: 953
# Valid syntax: True
# Has imports: True
# Has assignments: True

"""Unit tests for recommendation system."""

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
