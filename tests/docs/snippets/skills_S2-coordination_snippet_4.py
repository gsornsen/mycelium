# Source: skills/S2-coordination.md
# Line: 196
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Simple handoff with context
result = await handoff_to_agent(
    target_agent="security-expert",
    task="Review authentication implementation in auth.py",
    context={
        "files": ["auth.py", "models/user.py"],
        "concerns": ["password hashing", "session management"]
    }
)

# Handoff without waiting
result = await handoff_to_agent(
    target_agent="documentation-specialist",
    task="Update API documentation",
    wait_for_completion=False
)
# Returns immediately with handoff_id for later status check