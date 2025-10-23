# Source: troubleshooting/discovery-coordination.md
# Line: 889
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Solution 1: Validate context against schema
from jsonschema import validate, ValidationError

# Get agent's expected context schema
details = get_agent_details("security-expert")
expected_schema = details["metadata"].get("context_schema")

if expected_schema:
    try:
        validate(instance=context, schema=expected_schema)
    except ValidationError as e:
        print(f"Context validation failed: {e}")
        # Fix context structure before retrying

# Solution 2: Use standard context templates
STANDARD_CONTEXT_TEMPLATES = {
    "code_review": {
        "files": List[str],
        "focus_areas": List[str],
        "standards": str
    },
    "security_audit": {
        "files": List[str],
        "focus_areas": List[str],
        "compliance": str,
        "known_issues": List[Dict]
    },
    # ... more templates
}

# Build context from template
context = build_context_from_template(
    template="security_audit",
    files=["auth.py"],
    focus_areas=["authentication"],
    compliance="OWASP_ASVS_4.0"
)

# Solution 3: Get context example from agent
details = get_agent_details("security-expert")
context_example = details["metadata"].get("context_example")

# Use example as guide for structure