# Source: api/discovery-quickstart.md
# Line: 286
# Valid syntax: True
# Has imports: True
# Has assignments: True

from functools import lru_cache

import requests


@lru_cache(maxsize=100)
def get_agent(agent_id: str):
    response = requests.get(f"http://localhost:8000/api/v1/agents/{agent_id}")
    return response.json()
