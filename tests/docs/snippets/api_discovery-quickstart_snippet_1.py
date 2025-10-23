# Source: api/discovery-quickstart.md
# Line: 176
# Valid syntax: True
# Has imports: True
# Has assignments: True

import requests

# Step 1: Discover agents
response = requests.post(
    "http://localhost:8000/api/v1/agents/discover",
    json={
        "query": "secure API authentication implementation",
        "limit": 3,
        "threshold": 0.8
    }
)

matches = response.json()["matches"]

# Step 2: Get top match
if matches:
    best_agent = matches[0]
    print(f"Best match: {best_agent['agent']['name']}")
    print(f"Confidence: {best_agent['confidence']}")
    print(f"Reason: {best_agent['match_reason']}")