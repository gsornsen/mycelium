# Source: wizard-reference.md
# Line: 157
# Valid syntax: True
# Has imports: False
# Has assignments: True

state = WizardState()
state.detection_results = summary

if state.can_proceed_to(WizardStep.SERVICES):
    print("Can proceed to services")