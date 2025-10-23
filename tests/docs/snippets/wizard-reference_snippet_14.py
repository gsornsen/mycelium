# Source: wizard-reference.md
# Line: 365
# Valid syntax: True
# Has imports: False
# Has assignments: True

flow = WizardFlow()
flow.state.current_step = WizardStep.SERVICES

prev_step = flow.go_back()
# Returns WizardStep.DETECTION