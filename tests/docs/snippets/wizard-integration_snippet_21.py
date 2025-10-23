# Source: wizard-integration.md
# Line: 810
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.wizard.flow import WizardState


class WizardOrchestrator:
    """Orchestrate multiple related wizards."""

    def __init__(self):
        self.wizards = {}

    def run_sequential_wizards(self, wizard_specs: list[dict]):
        """Run multiple wizards in sequence, passing state."""
        results = []

        for spec in wizard_specs:
            wizard_type = spec["type"]
            state = self.create_wizard_state(wizard_type)

            # Pass data from previous wizard
            if results:
                self.apply_previous_results(state, results[-1])

            # Run wizard
            result = self.run_wizard(state)
            results.append(result)

        return results

    def create_wizard_state(self, wizard_type: str) -> WizardState:
        """Create wizard state based on type."""
        # Factory pattern for different wizard types
        pass

    def apply_previous_results(self, state: WizardState, previous: dict):
        """Apply results from previous wizard to current state."""
        # Data flow between wizards
        pass
