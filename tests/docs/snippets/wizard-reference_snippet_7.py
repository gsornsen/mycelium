# Source: wizard-reference.md
# Line: 225
# Valid syntax: True
# Has imports: False
# Has assignments: True

state = WizardState()
state.current_step = WizardStep.COMPLETE
state.completed = True

if state.is_complete():
    print("Wizard is complete!")
