# Source: wizard-reference.md
# Line: 695
# Valid syntax: True
# Has imports: False
# Has assignments: True

class WizardValidator:
    """Validates wizard state and user inputs."""

    def __init__(self, state: WizardState) -> None:
        """Initialize validator with wizard state."""
        self.state = state
        self.errors: list[ValidationError] = []
