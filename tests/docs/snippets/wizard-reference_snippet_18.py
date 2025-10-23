# Source: wizard-reference.md
# Line: 433
# Valid syntax: True
# Has imports: False
# Has assignments: True

flow = WizardFlow()
flow.mark_complete()
assert flow.state.is_complete()