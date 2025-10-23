# Source: troubleshooting/discovery-coordination.md
# Line: 117
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Solution 1: Use agent's actual keywords
# If agent has keywords: ["ML", "model", "serving"]
# Query: "ML model serving" instead of "machine learning deployment"

# Solution 2: Try multiple query variations
queries = [
    "machine learning deployment",
    "ML model serving",
    "model inference production",
    "deploy ML models"
]

best_result = None
best_confidence = 0

for query in queries:
    result = discover_agents(query, limit=3)
    if result["agents"] and result["agents"][0]["confidence"] > best_confidence:
        best_result = result
        best_confidence = result["agents"][0]["confidence"]

print(f"Best match: {best_result['agents'][0]['name']} ({best_confidence})")

# Solution 3: Request agent description update
# File issue or update agent description to include relevant keywords
