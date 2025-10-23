# Source: environment-activation.md
# Line: 650
# Valid syntax: True
# Has imports: True
# Has assignments: False

from mycelium_onboarding.env_validator import (
    is_environment_active,
    validate_environment,
)

# Quick boolean check
if is_environment_active():
    print("Environment is active")

# Comprehensive validation (raises exception if invalid)
try:
    validate_environment()
    print("Environment is valid")
except EnvironmentValidationError as e:
    print(f"Environment error: {e}")
