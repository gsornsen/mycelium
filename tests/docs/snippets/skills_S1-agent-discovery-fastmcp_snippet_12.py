# Source: skills/S1-agent-discovery-fastmcp.md
# Line: 825
# Valid syntax: True
# Has imports: True
# Has assignments: True

from functools import lru_cache
from typing import Dict, Any

class CachedNLPMatcher(NLPMatcher):
    """NLP matcher with LRU caching."""

    @lru_cache(maxsize=1000)
    def _get_query_embedding(self, query: str) -> np.ndarray:
        """Cache query embeddings."""
        return self.model.encode([query])[0]

    async def match(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Match with cached embeddings."""
        # Use cached query embedding
        query_embedding = self._get_query_embedding(query)

        # Rest of matching logic...