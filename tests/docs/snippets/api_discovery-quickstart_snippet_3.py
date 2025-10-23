# Source: api/discovery-quickstart.md
# Line: 220
# Valid syntax: True
# Has imports: True
# Has assignments: True

import requests

def discover_agent(query: str, min_confidence: float = 0.8):
    """Discover agent with fallback to lower confidence."""

    # Try high confidence first
    response = requests.post(
        "http://localhost:8000/api/v1/agents/discover",
        json={"query": query, "threshold": min_confidence}
    )

    matches = response.json()["matches"]

    if not matches and min_confidence > 0.5:
        # Fallback to lower confidence
        print(f"No high-confidence matches, trying threshold 0.5...")
        return discover_agent(query, min_confidence=0.5)

    return matches

# Usage
agents = discover_agent("machine learning model training")
if agents:
    print(f"Found {len(agents)} agents")
else:
    print("No agents found for this query")