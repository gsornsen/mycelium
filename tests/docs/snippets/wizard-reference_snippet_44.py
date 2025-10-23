# Source: wizard-reference.md
# Line: 950
# Valid syntax: True
# Has imports: False
# Has assignments: True

class WizardStatePersistence:
    """Manages saving and loading wizard state."""

    def __init__(self, state_dir: Path | None = None) -> None:
        """Initialize persistence manager."""
        self.state_dir = state_dir or get_state_dir()
        self.state_file = self.state_dir / "wizard_state.json"