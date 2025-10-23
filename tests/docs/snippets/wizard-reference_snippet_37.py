# Source: wizard-reference.md
# Line: 844
# Valid syntax: True
# Has imports: False
# Has assignments: True

validator = WizardValidator(state)
if not validator.validate_temporal_namespace("production"):
    print("Invalid namespace")
