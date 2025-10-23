# Source: wizard-reference.md
# Line: 896
# Valid syntax: True
# Has imports: False
# Has assignments: True

validator = WizardValidator(state)
validator.validate_state()
errors = validator.get_errors()