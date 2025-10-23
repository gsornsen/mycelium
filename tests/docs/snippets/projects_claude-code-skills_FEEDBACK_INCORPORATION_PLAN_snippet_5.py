# Source: projects/claude-code-skills/FEEDBACK_INCORPORATION_PLAN.md
# Line: 824
# Valid syntax: True
# Has imports: True
# Has assignments: True

"""
TF-IDF Vectorizer for agent search with pgvector integration.
Hybrid approach: TF-IDF for explainability + embeddings for semantic search.
"""

from pathlib import Path
from typing import Any, Optional

from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer


class AgentVectorizer:
    """Hybrid TF-IDF + Embeddings agent similarity ranking."""

    def __init__(self, index_path: str, db_manager: Optional['DatabaseManager'] = None):
        """Initialize vectorizer.

        Args:
            index_path: Path to agents/index.json
            db_manager: Database manager for pgvector (optional)
        """
        self.index_path = Path(index_path)
        self.db_manager = db_manager
        self.agents = self._load_agents()

        # TF-IDF for keyword matching (explainability)
        self.vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        self.agent_vectors = self._vectorize_agents()

        # Sentence embeddings for semantic search (accuracy)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self._ensure_embeddings()

    def _ensure_embeddings(self):
        """Ensure all agents have embeddings in database."""
        if not self.db_manager:
            return  # Skip if no database

        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()

            # Check which agents need embeddings
            cursor.execute("""
                SELECT id FROM skills
                WHERE id NOT IN (SELECT skill_id FROM skill_embeddings)
            """)
            missing = [row[0] for row in cursor.fetchall()]

            if missing:
                print(f"Generating embeddings for {len(missing)} agents...")
                for agent in self.agents:
                    if agent['id'] in missing:
                        # Generate embedding
                        text = f"{agent.get('description', '')} {' '.join(agent.get('keywords', []))}"
                        embedding = self.embedding_model.encode(text)

                        # Store in database
                        cursor.execute("""
                            INSERT INTO skill_embeddings (skill_id, embedding)
                            VALUES (%s, %s)
                        """, (agent['id'], embedding.tolist()))

                conn.commit()
                print(f"✅ Generated {len(missing)} embeddings")
        finally:
            self.db_manager.return_connection(conn)

    def search(
        self,
        query: str,
        max_results: int = 5,
        category_filter: str | None = None,
        min_score: float = 0.0,
        use_embeddings: bool = True
    ) -> list[dict[str, Any]]:
        """Hybrid search using TF-IDF + embeddings.

        Args:
            query: Search query
            max_results: Max results to return
            category_filter: Optional category filter
            min_score: Minimum similarity score
            use_embeddings: Use pgvector semantic search (default: True)

        Returns:
            List of matching agents with scores
        """
        # TF-IDF search (fast, explainable)
        tfidf_results = self._tfidf_search(query, max_results * 2, category_filter)

        # Embedding search (accurate, semantic)
        if use_embeddings and self.db_manager:
            embedding_results = self._embedding_search(query, max_results * 2, category_filter)

            # Combine results (weighted average)
            combined = self._combine_results(tfidf_results, embedding_results, weights=(0.3, 0.7))
        else:
            combined = tfidf_results

        # Filter and return top results
        filtered = [r for r in combined if r['score'] >= min_score]
        return filtered[:max_results]

    def _embedding_search(
        self,
        query: str,
        max_results: int,
        category_filter: str | None
    ) -> list[dict[str, Any]]:
        """Search using pgvector embeddings."""
        conn = self.db_manager.get_connection()
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query)

            # Similarity search using pgvector
            cursor = conn.cursor()
            sql = """
                SELECT s.id, s.name, s.description, s.category,
                       1 - (e.embedding <=> %s::vector) as similarity
                FROM skills s
                JOIN skill_embeddings e ON e.skill_id = s.id
            """
            params = [query_embedding.tolist()]

            if category_filter:
                sql += " WHERE s.category = %s"
                params.append(category_filter)

            sql += " ORDER BY e.embedding <=> %s::vector LIMIT %s"
            params.extend([query_embedding.tolist(), max_results])

            cursor.execute(sql, params)

            results = []
            for row in cursor.fetchall():
                agent_id, name, description, category, similarity = row
                results.append({
                    'agent_id': agent_id,
                    'score': float(similarity),
                    'explanation': f"Semantic match (embedding similarity: {similarity:.3f})",
                    'category': category or 'uncategorized'
                })

            return results
        finally:
            self.db_manager.return_connection(conn)

    def _combine_results(
        self,
        tfidf_results: list[dict],
        embedding_results: list[dict],
        weights: tuple = (0.3, 0.7)
    ) -> list[dict]:
        """Combine TF-IDF and embedding results with weighted scores."""
        # Create maps for quick lookup
        tfidf_map = {r['agent_id']: r for r in tfidf_results}
        embedding_map = {r['agent_id']: r for r in embedding_results}

        # Get all unique agent IDs
        all_ids = set(tfidf_map.keys()) | set(embedding_map.keys())

        # Combine scores
        combined = []
        for agent_id in all_ids:
            tfidf_score = tfidf_map.get(agent_id, {}).get('score', 0.0)
            embedding_score = embedding_map.get(agent_id, {}).get('score', 0.0)

            # Weighted average
            final_score = weights[0] * tfidf_score + weights[1] * embedding_score

            # Use embedding result as template (better explanation)
            result = embedding_map.get(agent_id, tfidf_map.get(agent_id))
            result['score'] = final_score
            result['explanation'] = f"Hybrid match (TF-IDF: {tfidf_score:.3f}, Embedding: {embedding_score:.3f})"

            combined.append(result)

        # Sort by combined score
        combined.sort(key=lambda x: x['score'], reverse=True)
        return combined
