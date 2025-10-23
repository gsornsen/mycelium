# Source: wizard-reference.md
# Line: 447
# Valid syntax: True
# Has imports: False
# Has assignments: True

class WizardScreens:
    """All wizard screen implementations."""

    def __init__(self, state: WizardState) -> None:
        """Initialize wizard screens with state."""
        self.state = state
