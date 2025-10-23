# Source: api/discovery-quickstart.md
# Line: 306
# Valid syntax: True
# Has imports: True
# Has assignments: True

import time

import requests


def discover_with_retry(query: str, max_retries: int = 3):
    """Discover agents with rate limit retry."""

    for attempt in range(max_retries):
        response = requests.post(
            "http://localhost:8000/api/v1/agents/discover",
            json={"query": query}
        )

        if response.status_code == 429:
            # Rate limited
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"Rate limited, waiting {retry_after}s...")
            time.sleep(retry_after)
            continue

        return response.json()

    raise Exception("Max retries exceeded")
