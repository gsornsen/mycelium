# Source: wizard-reference.md
# Line: 910
# Valid syntax: True
# Has imports: False
# Has assignments: True

validator = WizardValidator(state)
validator.validate_state()
for msg in validator.get_error_messages():
    print(msg)
