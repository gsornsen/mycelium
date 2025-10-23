# Source: wizard-integration.md
# Line: 657
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Provide helpful error messages
try:
    config = state.to_config()
except ValueError as e:
    print(f"Configuration error: {e}")
    print("Please check your settings and try again.")
    # Keep state for retry
