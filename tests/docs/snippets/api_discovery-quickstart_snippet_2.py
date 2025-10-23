# Source: api/discovery-quickstart.md
# Line: 201
# Valid syntax: True
# Has imports: True
# Has assignments: True

import requests

# Get all categories
response = requests.get("http://localhost:8000/api/v1/agents/search?limit=100")
agents = response.json()["agents"]

categories = set(agent["category"] for agent in agents)

# Browse each category
for category in categories:
    response = requests.get(
        f"http://localhost:8000/api/v1/agents/search?category={category}"
    )
    print(f"\n{category} ({response.json()['total_count']} agents)")
