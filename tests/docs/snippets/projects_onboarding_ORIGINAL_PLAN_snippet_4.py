# Source: projects/onboarding/ORIGINAL_PLAN.md
# Line: 532
# Valid syntax: True
# Has imports: False
# Has assignments: True

# In command execution context
def validate_python_command(cmd: str) -> bool:
    """Ensure python commands use uv"""
    blocked_patterns = [
        r'\bpython\s',
        r'\bpython3\s',
        r'\bpip\s',
        r'\bpip3\s',
    ]

    for pattern in blocked_patterns:
        if re.search(pattern, cmd):
            raise ValueError(
                "Direct python execution blocked. Use: uv run python ..."
            )

    return True
