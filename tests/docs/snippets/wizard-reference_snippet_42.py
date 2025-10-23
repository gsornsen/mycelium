# Source: wizard-reference.md
# Line: 925
# Valid syntax: True
# Has imports: False
# Has assignments: True

validator = WizardValidator(state)
validator.validate_state()
if validator.has_errors():
    print("Validation failed!")