# Source: wizard-reference.md
# Line: 209
# Valid syntax: True
# Has imports: False
# Has assignments: True

state = WizardState()
state.current_step = WizardStep.SERVICES

prev_step = state.get_previous_step()
# Returns WizardStep.DETECTION