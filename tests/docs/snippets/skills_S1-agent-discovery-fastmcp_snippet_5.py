# Source: skills/S1-agent-discovery-fastmcp.md
# Line: 491
# Valid syntax: True
# Has imports: True
# Has assignments: True

from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class NLPMatcher:
    """NLP-based agent matching using sentence embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize matcher with sentence transformer.

        Args:
            model_name: HuggingFace model name
        """
        self.model = SentenceTransformer(model_name)
        self.agent_embeddings = {}

    async def match(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Match query against candidate agents.

        Args:
            query: Search query
            candidates: Agent candidates
            threshold: Minimum confidence

        Returns:
            Matched agents with confidence scores
        """
        # Generate query embedding
        query_embedding = self.model.encode([query])[0]

        matches = []
        for agent in candidates:
            # Generate or retrieve agent embedding
            agent_key = agent["id"]
            if agent_key not in self.agent_embeddings:
                agent_text = self._prepare_agent_text(agent)
                agent_embedding = self.model.encode([agent_text])[0]
                self.agent_embeddings[agent_key] = agent_embedding
            else:
                agent_embedding = self.agent_embeddings[agent_key]

            # Compute similarity
            similarity = cosine_similarity(
                [query_embedding],
                [agent_embedding]
            )[0][0]

            # Apply threshold
            if similarity >= threshold:
                matches.append({
                    **agent,
                    "confidence": float(similarity),
                    "match_reason": self._explain_match(query, agent, similarity)
                })

        return matches

    def _prepare_agent_text(self, agent: Dict[str, Any]) -> str:
        """
        Prepare agent text for embedding.

        Args:
            agent: Agent metadata

        Returns:
            Combined text representation
        """
        parts = [
            agent.get("name", ""),
            agent.get("description", ""),
            " ".join(agent.get("capabilities", [])),
            " ".join(agent.get("keywords", []))
        ]
        return " ".join(filter(None, parts))

    def _explain_match(
        self,
        query: str,
        agent: Dict[str, Any],
        score: float
    ) -> str:
        """
        Generate match explanation.

        Args:
            query: Search query
            agent: Agent metadata
            score: Similarity score

        Returns:
            Human-readable explanation
        """
        query_words = set(query.lower().split())
        agent_keywords = set(agent.get("keywords", []))

        matches = query_words.intersection(agent_keywords)

        if matches:
            return f"Matches keywords: {', '.join(matches)}"
        else:
            return agent.get("description", "")[:100]