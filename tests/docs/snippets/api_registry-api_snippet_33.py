# Source: api/registry-api.md
# Line: 615
# Valid syntax: True
# Has imports: True
# Has assignments: True

from sentence_transformers import SentenceTransformer
from plugins.mycelium_core.registry import AgentRegistry

async def semantic_agent_discovery(query: str):
    # Initialize embedding model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    async with AgentRegistry() as registry:
        # Generate query embedding
        query_embedding = model.encode(query).tolist()

        # Perform similarity search
        results = await registry.similarity_search(
            embedding=query_embedding,
            limit=5,
            threshold=0.6
        )

        print(f"Top agents for '{query}':")
        for agent, similarity in results:
            print(f"  {similarity:.1%} - {agent['name']}: {agent['description']}")

# Usage
import asyncio
asyncio.run(semantic_agent_discovery(
    "I need to build a REST API with authentication"
))