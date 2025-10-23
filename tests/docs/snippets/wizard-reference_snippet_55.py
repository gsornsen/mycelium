# Source: wizard-reference.md
# Line: 1174
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.wizard.validation import WizardValidator

validator = WizardValidator(state)

# Validate specific fields
if not validator.validate_project_name(state.project_name):
    print("Invalid project name")

# Validate port range
if not validator.validate_port(state.redis_port, "redis"):
    print("Invalid Redis port")

# Comprehensive validation
if not validator.validate_state():
    for error in validator.get_errors():
        print(f"Error in {error.field}: {error.message}")
