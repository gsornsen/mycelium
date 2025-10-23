# Source: wizard-integration.md
# Line: 356
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.wizard.validation import WizardValidator, ValidationError

class ExtendedWizardValidator(WizardValidator):
    """Extended validator with custom rules."""

    def validate_custom_naming_convention(self, name: str) -> bool:
        """Validate project name follows company naming convention."""
        # Example: Must start with "proj-" or "svc-"
        valid_prefixes = ["proj-", "svc-"]

        if not any(name.startswith(prefix) for prefix in valid_prefixes):
            self.errors.append(
                ValidationError(
                    field="project_name",
                    message=f"Project name must start with one of: {', '.join(valid_prefixes)}",
                    severity="error",
                )
            )
            return False
        return True

    def validate_production_requirements(self) -> bool:
        """Validate production deployment requirements."""
        if self.state.deployment_method == "kubernetes":
            # Require persistence for production
            if not self.state.enable_persistence:
                self.errors.append(
                    ValidationError(
                        field="enable_persistence",
                        message="Persistence must be enabled for Kubernetes deployment",
                        severity="error",
                    )
                )
                return False
        return True

    def validate_state(self) -> bool:
        """Override to include custom validations."""
        # Run base validations
        if not super().validate_state():
            return False

        # Add custom validations
        if self.state.project_name:
            self.validate_custom_naming_convention(self.state.project_name)

        self.validate_production_requirements()

        return len(self.errors) == 0

# Usage
state = WizardState()
state.project_name = "proj-myapp"
validator = ExtendedWizardValidator(state)
if validator.validate_state():
    print("Validation passed!")