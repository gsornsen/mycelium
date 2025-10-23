# Source: wizard-reference.md
# Line: 881
# Valid syntax: True
# Has imports: False
# Has assignments: True

validator = WizardValidator(state)
if not validator.validate_state():
    for error in validator.get_errors():
        print(f"{error.field}: {error.message}")