# Source: wizard-reference.md
# Line: 302
# Valid syntax: True
# Has imports: False
# Has assignments: True

class WizardFlow:
    """Manages wizard flow logic."""

    def __init__(self, state: WizardState | None = None) -> None:
        """Initialize wizard flow."""
        self.state = state or WizardState()
