# Source: troubleshooting/discovery-coordination.md
# Line: 468
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Solution 1: Reduce context size
# Instead of embedding large data:
context = {
    "full_codebase": read_all_files(),  # Too large!
    "git_history": get_git_log()  # Too large!
}

# Use references:
context = {
    "files": ["auth.py", "models/user.py"],  # File paths only
    "summary": "Authentication system with JWT tokens",
    "known_issues": [
        {"type": "security", "file": "auth.py", "line": 42}
    ]
}

# Solution 2: Validate context is serializable
import json

try:
    json.dumps(context)  # Will fail if not serializable
except TypeError as e:
    print(f"Context not serializable: {e}")
    # Fix non-serializable objects

# Solution 3: Use schema validation
from jsonschema import ValidationError, validate

HANDOFF_CONTEXT_SCHEMA = {
    "type": "object",
    "properties": {
        "files": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
        "metadata": {"type": "object"}
    },
    "additionalProperties": False
}

try:
    validate(instance=context, schema=HANDOFF_CONTEXT_SCHEMA)
except ValidationError as e:
    print(f"Invalid context schema: {e}")

# Solution 4: Check handoff result
result = handoff_to_agent(
    target_agent="security-expert",
    task="Review auth.py",
    context=context
)

if not result.get("context_preserved", False):
    print("Warning: Context not fully preserved")
    print(f"Reason: {result.get('preservation_status', {})}")
    # Retry with reduced context or different format
