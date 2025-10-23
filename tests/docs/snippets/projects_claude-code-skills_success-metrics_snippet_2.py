# Source: projects/claude-code-skills/success-metrics.md
# Line: 413
# Valid syntax: True
# Has imports: True
# Has assignments: True

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('all-MiniLM-L6-v2')

original_embedding = model.encode(original_text)
compressed_embedding = model.encode(compressed_text)

similarity = cosine_similarity([original_embedding], [compressed_embedding])[0][0]

# Success: similarity >= 0.95
