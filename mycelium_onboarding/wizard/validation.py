"""Wizard validation logic.

This module provides comprehensive validation for wizard state and user inputs,
ensuring data integrity throughout the onboarding process. All validation rules
align with backend service requirements (PostgreSQL, Redis, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mycelium_onboarding.wizard.flow import WizardState

__all__ = [
    "ValidationError",
    "WizardValidator",
]


@dataclass
class ValidationError:
    """Validation error with field and message.

    Attributes:
        field: Name of the field that failed validation
        message: Human-readable error message
        severity: Error severity level ("error" or "warning")
    """

    field: str
    message: str
    severity: str = "error"  # error, warning

    def __str__(self) -> str:
        """Format error for display."""
        return f"{self.field}: {self.message}"


class WizardValidator:
    """Validates wizard state and user inputs.

    This class provides comprehensive validation for all wizard inputs,
    ensuring they meet format requirements and service constraints.

    Attributes:
        state: The wizard state to validate
        errors: List of validation errors found

    Example:
        >>> from mycelium_onboarding.wizard.flow import WizardState
        >>> state = WizardState()
        >>> state.project_name = "my-project"
        >>> validator = WizardValidator(state)
        >>> if not validator.validate_state():
        ...     print(validator.get_error_messages())
    """

    def __init__(self, state: WizardState) -> None:
        """Initialize validator with wizard state.

        Args:
            state: Wizard state to validate
        """
        self.state = state
        self.errors: list[ValidationError] = []

    def validate_project_name(self, name: str) -> bool:
        """Validate project name format.

        Project names must contain only alphanumeric characters, hyphens,
        and underscores to ensure compatibility with Docker, systemd, etc.

        Args:
            name: Project name to validate

        Returns:
            True if valid, False otherwise
        """
        if not name:
            self.errors.append(
                ValidationError(
                    field="project_name",
                    message="Project name cannot be empty",
                )
            )
            return False

        if not name.replace("-", "").replace("_", "").isalnum():
            self.errors.append(
                ValidationError(
                    field="project_name",
                    message="Project name must contain only alphanumeric characters, hyphens, and underscores",
                )
            )
            return False

        if len(name) > 100:
            self.errors.append(
                ValidationError(
                    field="project_name",
                    message=f"Project name is too long (max 100 characters, got {len(name)})",
                )
            )
            return False

        return True

    def validate_services(self) -> bool:
        """Validate at least one service is selected.

        Returns:
            True if at least one service is enabled, False otherwise
        """
        if not any(self.state.services_enabled.values()):
            self.errors.append(
                ValidationError(
                    field="services",
                    message="At least one service must be enabled",
                )
            )
            return False
        return True

    def validate_postgres_database(self, db_name: str) -> bool:
        """Validate PostgreSQL database name.

        PostgreSQL database names have specific requirements:
        - Must start with a letter
        - Can only contain alphanumeric and underscores (no hyphens)
        - Maximum 63 characters

        Args:
            db_name: Database name to validate

        Returns:
            True if valid, False otherwise
        """
        if not db_name:
            self.errors.append(
                ValidationError(
                    field="postgres_database",
                    message="Database name cannot be empty",
                )
            )
            return False

        # PostgreSQL rules: alphanumeric + underscores, no hyphens
        if not db_name.replace("_", "").isalnum():
            self.errors.append(
                ValidationError(
                    field="postgres_database",
                    message="Database name can only contain alphanumeric characters and underscores",
                )
            )
            return False

        # Cannot start with number
        if db_name[0].isdigit():
            self.errors.append(
                ValidationError(
                    field="postgres_database",
                    message="Database name cannot start with a number",
                )
            )
            return False

        # Must start with letter
        if not db_name[0].isalpha():
            self.errors.append(
                ValidationError(
                    field="postgres_database",
                    message="Database name must start with a letter",
                )
            )
            return False

        # Length check
        if len(db_name) > 63:
            self.errors.append(
                ValidationError(
                    field="postgres_database",
                    message=f"Database name is too long (max 63 characters, got {len(db_name)})",
                )
            )
            return False

        return True

    def validate_port(self, port: int, service: str) -> bool:
        """Validate port number range.

        Ports must be in the non-privileged range (1024-65535) to avoid
        requiring root permissions.

        Args:
            port: Port number to validate
            service: Service name for error message

        Returns:
            True if valid, False otherwise
        """
        if port < 1024 or port > 65535:
            self.errors.append(
                ValidationError(
                    field=f"{service}_port",
                    message=f"Port must be between 1024 and 65535 (got {port})",
                )
            )
            return False
        return True

    def validate_deployment_method(self, method: str) -> bool:
        """Validate deployment method is supported.

        Args:
            method: Deployment method to validate

        Returns:
            True if valid, False otherwise
        """
        valid_methods = ["docker-compose", "kubernetes", "systemd", "manual"]
        if method not in valid_methods:
            self.errors.append(
                ValidationError(
                    field="deployment_method",
                    message=f"Deployment method must be one of: {', '.join(valid_methods)}",
                )
            )
            return False
        return True

    def validate_temporal_namespace(self, namespace: str) -> bool:
        """Validate Temporal namespace format.

        Args:
            namespace: Namespace to validate

        Returns:
            True if valid, False otherwise
        """
        if not namespace:
            self.errors.append(
                ValidationError(
                    field="temporal_namespace",
                    message="Temporal namespace cannot be empty",
                )
            )
            return False

        if not namespace.replace("-", "").replace("_", "").isalnum():
            self.errors.append(
                ValidationError(
                    field="temporal_namespace",
                    message="Temporal namespace must contain only alphanumeric characters, hyphens, and underscores",
                )
            )
            return False

        if len(namespace) > 255:
            self.errors.append(
                ValidationError(
                    field="temporal_namespace",
                    message=f"Temporal namespace is too long (max 255 characters, got {len(namespace)})",
                )
            )
            return False

        return True

    def validate_port_conflicts(self) -> bool:
        """Validate that no ports conflict.

        Returns:
            True if no conflicts, False otherwise
        """
        ports_used: dict[int, str] = {}

        # Check Redis port
        if self.state.services_enabled.get("redis"):
            ports_used[self.state.redis_port] = "redis"

        # Check PostgreSQL port
        if self.state.services_enabled.get("postgres"):
            if self.state.postgres_port in ports_used:
                self.errors.append(
                    ValidationError(
                        field="postgres_port",
                        message=f"Port {self.state.postgres_port} conflicts with " f"{ports_used[self.state.postgres_port]} service",
                    )
                )
                return False
            ports_used[self.state.postgres_port] = "postgres"

        # Check Temporal ports
        if self.state.services_enabled.get("temporal"):
            if self.state.temporal_ui_port in ports_used:
                self.errors.append(
                    ValidationError(
                        field="temporal_ui_port",
                        message=f"Port {self.state.temporal_ui_port} conflicts with " f"{ports_used[self.state.temporal_ui_port]} service",
                    )
                )
                return False
            ports_used[self.state.temporal_ui_port] = "temporal_ui"

            if self.state.temporal_frontend_port in ports_used:
                self.errors.append(
                    ValidationError(
                        field="temporal_frontend_port",
                        message=f"Port {self.state.temporal_frontend_port} conflicts with " f"{ports_used[self.state.temporal_frontend_port]} service",
                    )
                )
                return False
            ports_used[self.state.temporal_frontend_port] = "temporal_frontend"

        return True

    def validate_state(self) -> bool:
        """Validate complete wizard state.

        Performs comprehensive validation of all wizard state fields.

        Returns:
            True if all validations pass, False otherwise
        """
        self.errors = []  # Reset errors

        # Validate project name
        if self.state.project_name:
            self.validate_project_name(self.state.project_name)

        # Validate services
        self.validate_services()

        # Validate service-specific settings
        if self.state.services_enabled.get("postgres"):
            if self.state.postgres_database:
                self.validate_postgres_database(self.state.postgres_database)
            self.validate_port(self.state.postgres_port, "postgres")

        if self.state.services_enabled.get("redis"):
            self.validate_port(self.state.redis_port, "redis")

        if self.state.services_enabled.get("temporal"):
            self.validate_port(self.state.temporal_ui_port, "temporal_ui")
            self.validate_port(self.state.temporal_frontend_port, "temporal_frontend")
            if self.state.temporal_namespace:
                self.validate_temporal_namespace(self.state.temporal_namespace)

        # Validate deployment method
        if self.state.deployment_method:
            self.validate_deployment_method(self.state.deployment_method)

        # Validate port conflicts
        self.validate_port_conflicts()

        return len(self.errors) == 0

    def get_errors(self) -> list[ValidationError]:
        """Get all validation errors.

        Returns:
            List of validation errors
        """
        return self.errors

    def get_error_messages(self) -> list[str]:
        """Get formatted error messages.

        Returns:
            List of formatted error messages
        """
        return [f"{err.field}: {err.message}" for err in self.errors]

    def has_errors(self) -> bool:
        """Check if there are any validation errors.

        Returns:
            True if errors exist, False otherwise
        """
        return len(self.errors) > 0
