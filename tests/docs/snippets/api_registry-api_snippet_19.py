# Source: api/registry-api.md
# Line: 373
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Generate embedding for query
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
query_embedding = model.encode("backend API development").tolist()

# Search for similar agents
results = await registry.similarity_search(
    embedding=query_embedding,
    limit=5,
    threshold=0.7
)

for agent, similarity in results:
    print(f"{agent['name']}: {similarity:.2%} match")
