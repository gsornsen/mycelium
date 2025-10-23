# Source: wizard-integration.md
# Line: 668
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Don't silently fail
try:
    config = state.to_config()
except ValueError:
    pass  # User has no idea what went wrong!