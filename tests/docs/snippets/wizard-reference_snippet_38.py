# Source: wizard-reference.md
# Line: 862
# Valid syntax: True
# Has imports: False
# Has assignments: True

validator = WizardValidator(state)
if not validator.validate_port_conflicts():
    print("Port conflicts detected!")