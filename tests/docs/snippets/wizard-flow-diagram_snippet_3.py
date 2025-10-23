# Source: wizard-flow-diagram.md
# Line: 408
# Valid syntax: True
# Has imports: False
# Has assignments: True

def get_next_step(self) -> Optional[WizardStep]:
    if (self.setup_mode == "quick" and
        self.current_step == WizardStep.DEPLOYMENT):
        return WizardStep.REVIEW  # Skip ADVANCED

    # Normal progression
    step_order = list(WizardStep)
    current_index = step_order.index(self.current_step)
    return step_order[current_index + 1]
