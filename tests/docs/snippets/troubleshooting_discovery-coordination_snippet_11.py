# Source: troubleshooting/discovery-coordination.md
# Line: 208
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Check API health
import requests
import time

start = time.time()
try:
    response = requests.get(
        "http://localhost:8000/health",
        timeout=5
    )
    print(f"API Health: {response.json()}")
    print(f"Response Time: {(time.time() - start)*1000}ms")
except requests.exceptions.Timeout:
    print("API not responding")
except requests.exceptions.ConnectionError:
    print("Cannot connect to API")