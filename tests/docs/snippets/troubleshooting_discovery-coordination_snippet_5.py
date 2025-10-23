# Source: troubleshooting/discovery-coordination.md
# Line: 101
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Check what keywords agents actually have
from plugins.mycelium_core.agent_discovery import get_agent_details

for agent in result["agents"]:
    details = get_agent_details(agent["id"])
    print(f"\n{agent['name']}:")
    print(f"  Keywords: {details['agent']['keywords']}")
    print(f"  Description: {details['agent']['description'][:100]}...")
    print(f"  Confidence: {agent['confidence']}")

# Compare your query terms with agent keywords
