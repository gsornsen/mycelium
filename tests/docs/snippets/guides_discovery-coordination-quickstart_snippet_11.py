# Source: guides/discovery-coordination-quickstart.md
# Line: 406
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Problem: Target agent missing context
result = handoff_to_agent("agent", "task", context=large_object)
# result["context_preserved"] == False

# Solution: Use file references instead
result = handoff_to_agent(
    "agent",
    "task",
    context={
        "files": ["path/to/data.json"],  # Reference, not embed
        "summary": "key points only"  # Small, structured
    }
)
