# Source: troubleshooting/discovery-coordination.md
# Line: 822
# Valid syntax: True
# Has imports: False
# Has assignments: True

context = {"large_data": [...]}
result = handoff_to_agent("agent", "task", context=context)
# ContextSerializationError: Context too large to serialize