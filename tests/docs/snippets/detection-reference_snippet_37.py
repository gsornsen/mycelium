# Source: detection-reference.md
# Line: 768
# Valid syntax: True
# Has imports: False
# Has assignments: True

result = detect_docker()
if not result.available:
    # Handle unavailable service
    print(f"Error: {result.error_message}")
