# Source: wizard-reference.md
# Line: 187
# Valid syntax: True
# Has imports: False
# Has assignments: True

state = WizardState()
state.setup_mode = "quick"
state.current_step = WizardStep.DEPLOYMENT

next_step = state.get_next_step()
# Returns WizardStep.REVIEW (skips ADVANCED)