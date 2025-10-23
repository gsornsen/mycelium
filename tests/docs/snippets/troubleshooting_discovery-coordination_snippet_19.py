# Source: troubleshooting/discovery-coordination.md
# Line: 436
# Valid syntax: True
# Has imports: False
# Has assignments: True

result = handoff_to_agent(
    target_agent="security-expert",
    task="Review auth.py",
    context={"file": "auth.py", "issues": [...]}
)
# result["context_preserved"] == False
# Or target agent doesn't have expected information