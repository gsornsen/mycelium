# Source: skills/S1-agent-discovery.md
# Line: 329
# Valid syntax: True
# Has imports: False
# Has assignments: True

try:
    result = await discover_agents("Python development")
    if not result["agents"]:
        print("No agents found for query")
        # Provide fallback or ask user to refine
    else:
        # Use discovered agents
        pass
except DiscoveryTimeoutError:
    print("Discovery timed out, try again")
except DiscoveryAPIError as e:
    print(f"Discovery failed: {e}")
    # Fall back to known agents or manual selection