# Source: wizard-reference.md
# Line: 387
# Valid syntax: True
# Has imports: False
# Has assignments: True

flow = WizardFlow()
flow.state.current_step = WizardStep.REVIEW

# Jump back to edit services
flow.jump_to(WizardStep.SERVICES)