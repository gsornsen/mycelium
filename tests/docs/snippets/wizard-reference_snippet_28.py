# Source: wizard-reference.md
# Line: 661
# Valid syntax: True
# Has imports: False
# Has assignments: True

@dataclass
class ValidationError:
    """Validation error with field and message."""
    field: str
    message: str
    severity: str = "error"  # "error" or "warning"
