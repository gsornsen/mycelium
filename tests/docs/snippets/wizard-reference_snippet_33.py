# Source: wizard-reference.md
# Line: 755
# Valid syntax: True
# Has imports: False
# Has assignments: True

validator = WizardValidator(state)
if not validator.validate_services():
    print("No services enabled!")