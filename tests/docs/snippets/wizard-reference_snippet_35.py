# Source: wizard-reference.md
# Line: 799
# Valid syntax: True
# Has imports: False
# Has assignments: True

validator = WizardValidator(state)
if not validator.validate_port(6379, "redis"):
    print("Invalid port")
