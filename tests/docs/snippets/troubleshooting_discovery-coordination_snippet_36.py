# Source: troubleshooting/discovery-coordination.md
# Line: 881
# Valid syntax: True
# Has imports: False
# Has assignments: True

result = handoff_to_agent("agent", "task", context={"foo": "bar"})
# Agent expects different context structure
# Agent returns error or incomplete results