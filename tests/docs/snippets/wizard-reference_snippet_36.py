# Source: wizard-reference.md
# Line: 822
# Valid syntax: True
# Has imports: False
# Has assignments: True

validator = WizardValidator(state)
if not validator.validate_deployment_method("docker-compose"):
    print("Invalid deployment method")