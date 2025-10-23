# Source: wizard-flow-diagram.md
# Line: 359
# Valid syntax: True
# Has imports: False
# Has assignments: True

class WizardFlow:
    def __init__(self, state: WizardState = None):
        self.state = state or WizardState()

    def advance(self) -> WizardStep:
        """Move to next step"""
        next_step = self.state.get_next_step()
        if next_step:
            self.state.current_step = next_step
        return self.state.current_step

    def go_back(self) -> WizardStep:
        """Move to previous step"""
        prev_step = self.state.get_previous_step()
        if prev_step:
            self.state.current_step = prev_step
        return self.state.current_step

    def jump_to(self, step: WizardStep) -> WizardStep:
        """Jump to specific step (from review)"""
        if self.state.can_proceed_to(step):
            self.state.current_step = step
        return self.state.current_step
