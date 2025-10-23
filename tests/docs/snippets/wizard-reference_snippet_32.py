# Source: wizard-reference.md
# Line: 741
# Valid syntax: True
# Has imports: False
# Has assignments: True

validator = WizardValidator(state)
if not validator.validate_project_name("my-project"):
    print(validator.get_error_messages())