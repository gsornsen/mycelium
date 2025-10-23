# Source: wizard-integration.md
# Line: 633
# Valid syntax: True
# Has imports: False
# Has assignments: False

# Always save state before potentially failing operations
persistence.save(state)
try:
    risky_operation()
except Exception:
    # State is already saved for resume
    raise