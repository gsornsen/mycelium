# Source: wizard-reference.md
# Line: 423
# Valid syntax: True
# Has imports: False
# Has assignments: True

flow = WizardFlow.load_state("/tmp/wizard_state.json")
print(f"Resumed from {flow.state.current_step}")