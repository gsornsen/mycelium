"""Tests for wizard validation logic.

This module tests comprehensive validation of wizard state and user inputs,
ensuring data integrity throughout the onboarding process.
"""

from __future__ import annotations

from mycelium_onboarding.wizard.flow import WizardState
from mycelium_onboarding.wizard.validation import ValidationError, WizardValidator


class TestValidationError:
    """Test ValidationError dataclass."""

    def test_validation_error_creation(self) -> None:
        """Test creating validation error."""
        error = ValidationError(field="test", message="Test error")
        assert error.field == "test"
        assert error.message == "Test error"
        assert error.severity == "error"

    def test_validation_error_with_severity(self) -> None:
        """Test creating validation error with custom severity."""
        error = ValidationError(
            field="test", message="Test warning", severity="warning"
        )
        assert error.severity == "warning"

    def test_validation_error_str(self) -> None:
        """Test string representation of validation error."""
        error = ValidationError(field="test_field", message="Test error message")
        assert str(error) == "test_field: Test error message"


class TestProjectNameValidation:
    """Test project name validation."""

    def test_validate_project_name_valid(self) -> None:
        """Test valid project names."""
        state = WizardState()
        validator = WizardValidator(state)

        assert validator.validate_project_name("mycelium")
        assert validator.validate_project_name("my-project")
        assert validator.validate_project_name("project_123")
        assert validator.validate_project_name("test-app-v2")
        assert validator.validate_project_name("MyProject123")
        assert len(validator.errors) == 0

    def test_validate_project_name_empty(self) -> None:
        """Test empty project name."""
        state = WizardState()
        validator = WizardValidator(state)

        assert not validator.validate_project_name("")
        assert len(validator.errors) == 1
        assert validator.errors[0].field == "project_name"
        assert "cannot be empty" in validator.errors[0].message

    def test_validate_project_name_with_spaces(self) -> None:
        """Test project name with spaces."""
        state = WizardState()
        validator = WizardValidator(state)

        assert not validator.validate_project_name("my project")
        assert len(validator.errors) == 1
        assert "alphanumeric" in validator.errors[0].message.lower()

    def test_validate_project_name_with_special_chars(self) -> None:
        """Test project name with special characters."""
        state = WizardState()
        validator = WizardValidator(state)

        assert not validator.validate_project_name("my@project")
        assert not validator.validate_project_name("project!")
        assert not validator.validate_project_name("test.app")
        assert len(validator.errors) == 3

    def test_validate_project_name_too_long(self) -> None:
        """Test project name exceeding max length."""
        state = WizardState()
        validator = WizardValidator(state)

        long_name = "a" * 101
        assert not validator.validate_project_name(long_name)
        assert len(validator.errors) == 1
        assert "too long" in validator.errors[0].message


class TestServicesValidation:
    """Test services validation."""

    def test_validate_services_at_least_one_enabled(self) -> None:
        """Test at least one service must be enabled."""
        state = WizardState()
        state.services_enabled = {"redis": True, "postgres": True}
        validator = WizardValidator(state)

        assert validator.validate_services()
        assert len(validator.errors) == 0

    def test_validate_services_none_enabled(self) -> None:
        """Test validation fails when no services enabled."""
        state = WizardState()
        state.services_enabled = {"redis": False, "postgres": False, "temporal": False}
        validator = WizardValidator(state)

        assert not validator.validate_services()
        assert len(validator.errors) == 1
        assert validator.errors[0].field == "services"
        assert "at least one" in validator.errors[0].message.lower()

    def test_validate_services_empty_dict(self) -> None:
        """Test validation fails when services dict is empty."""
        state = WizardState()
        state.services_enabled = {}
        validator = WizardValidator(state)

        assert not validator.validate_services()
        assert len(validator.errors) == 1


class TestPostgresValidation:
    """Test PostgreSQL database name validation."""

    def test_validate_postgres_database_valid(self) -> None:
        """Test valid PostgreSQL database names."""
        state = WizardState()
        validator = WizardValidator(state)

        assert validator.validate_postgres_database("mycelium_db")
        assert validator.validate_postgres_database("db123")
        assert validator.validate_postgres_database("test_database")
        assert validator.validate_postgres_database("mydb")
        assert len(validator.errors) == 0

    def test_validate_postgres_database_empty(self) -> None:
        """Test empty database name."""
        state = WizardState()
        validator = WizardValidator(state)

        assert not validator.validate_postgres_database("")
        assert len(validator.errors) == 1
        assert "cannot be empty" in validator.errors[0].message

    def test_validate_postgres_database_starts_with_number(self) -> None:
        """Test database name starting with number."""
        state = WizardState()
        validator = WizardValidator(state)

        assert not validator.validate_postgres_database("123db")
        # Returns after first check, so only one error
        assert len(validator.errors) == 1
        assert "cannot start with a number" in validator.errors[0].message

    def test_validate_postgres_database_with_hyphen(self) -> None:
        """Test database name with hyphen."""
        state = WizardState()
        validator = WizardValidator(state)

        assert not validator.validate_postgres_database("my-db")
        assert len(validator.errors) == 1
        assert "alphanumeric" in validator.errors[0].message.lower()

    def test_validate_postgres_database_with_special_chars(self) -> None:
        """Test database name with special characters."""
        state = WizardState()
        validator = WizardValidator(state)

        assert not validator.validate_postgres_database("my@db")
        assert not validator.validate_postgres_database("test.db")
        assert len(validator.errors) == 2

    def test_validate_postgres_database_too_long(self) -> None:
        """Test database name exceeding max length."""
        state = WizardState()
        validator = WizardValidator(state)

        long_name = "a" * 64
        assert not validator.validate_postgres_database(long_name)
        assert len(validator.errors) == 1
        assert "too long" in validator.errors[0].message


class TestPortValidation:
    """Test port number validation."""

    def test_validate_port_valid(self) -> None:
        """Test valid port numbers."""
        state = WizardState()
        validator = WizardValidator(state)

        assert validator.validate_port(5432, "postgres")
        assert validator.validate_port(6379, "redis")
        assert validator.validate_port(8080, "temporal_ui")
        assert validator.validate_port(65535, "test")
        assert validator.validate_port(1024, "test")
        assert len(validator.errors) == 0

    def test_validate_port_too_low(self) -> None:
        """Test port number below minimum."""
        state = WizardState()
        validator = WizardValidator(state)

        assert not validator.validate_port(80, "redis")
        assert not validator.validate_port(1023, "postgres")
        assert len(validator.errors) == 2

    def test_validate_port_too_high(self) -> None:
        """Test port number above maximum."""
        state = WizardState()
        validator = WizardValidator(state)

        assert not validator.validate_port(70000, "postgres")
        assert not validator.validate_port(65536, "redis")
        assert len(validator.errors) == 2


class TestDeploymentMethodValidation:
    """Test deployment method validation."""

    def test_validate_deployment_method_valid(self) -> None:
        """Test valid deployment methods."""
        state = WizardState()
        validator = WizardValidator(state)

        assert validator.validate_deployment_method("docker-compose")
        assert validator.validate_deployment_method("kubernetes")
        assert validator.validate_deployment_method("systemd")
        assert validator.validate_deployment_method("manual")
        assert len(validator.errors) == 0

    def test_validate_deployment_method_invalid(self) -> None:
        """Test invalid deployment method."""
        state = WizardState()
        validator = WizardValidator(state)

        assert not validator.validate_deployment_method("invalid")
        assert not validator.validate_deployment_method("docker")
        assert len(validator.errors) == 2


class TestTemporalNamespaceValidation:
    """Test Temporal namespace validation."""

    def test_validate_temporal_namespace_valid(self) -> None:
        """Test valid Temporal namespaces."""
        state = WizardState()
        validator = WizardValidator(state)

        assert validator.validate_temporal_namespace("default")
        assert validator.validate_temporal_namespace("my-namespace")
        assert validator.validate_temporal_namespace("test_namespace")
        assert validator.validate_temporal_namespace("ns123")
        assert len(validator.errors) == 0

    def test_validate_temporal_namespace_empty(self) -> None:
        """Test empty Temporal namespace."""
        state = WizardState()
        validator = WizardValidator(state)

        assert not validator.validate_temporal_namespace("")
        assert len(validator.errors) == 1
        assert "cannot be empty" in validator.errors[0].message

    def test_validate_temporal_namespace_with_special_chars(self) -> None:
        """Test Temporal namespace with special characters."""
        state = WizardState()
        validator = WizardValidator(state)

        assert not validator.validate_temporal_namespace("my@namespace")
        assert not validator.validate_temporal_namespace("test.namespace")
        assert len(validator.errors) == 2

    def test_validate_temporal_namespace_too_long(self) -> None:
        """Test Temporal namespace exceeding max length."""
        state = WizardState()
        validator = WizardValidator(state)

        long_name = "a" * 256
        assert not validator.validate_temporal_namespace(long_name)
        assert len(validator.errors) == 1
        assert "too long" in validator.errors[0].message


class TestPortConflicts:
    """Test port conflict detection."""

    def test_validate_port_conflicts_none(self) -> None:
        """Test no port conflicts."""
        state = WizardState()
        state.services_enabled = {"redis": True, "postgres": True, "temporal": True}
        state.redis_port = 6379
        state.postgres_port = 5432
        state.temporal_ui_port = 8080
        state.temporal_frontend_port = 7233

        validator = WizardValidator(state)
        assert validator.validate_port_conflicts()
        assert len(validator.errors) == 0

    def test_validate_port_conflicts_redis_postgres(self) -> None:
        """Test conflict between Redis and PostgreSQL ports."""
        state = WizardState()
        state.services_enabled = {"redis": True, "postgres": True}
        state.redis_port = 5432
        state.postgres_port = 5432

        validator = WizardValidator(state)
        assert not validator.validate_port_conflicts()
        assert len(validator.errors) == 1
        assert "conflicts" in validator.errors[0].message

    def test_validate_port_conflicts_temporal_ui(self) -> None:
        """Test conflict with Temporal UI port."""
        state = WizardState()
        state.services_enabled = {"redis": True, "temporal": True}
        state.redis_port = 8080
        state.temporal_ui_port = 8080

        validator = WizardValidator(state)
        assert not validator.validate_port_conflicts()
        assert len(validator.errors) == 1

    def test_validate_port_conflicts_temporal_frontend(self) -> None:
        """Test conflict with Temporal frontend port."""
        state = WizardState()
        state.services_enabled = {"postgres": True, "temporal": True}
        state.postgres_port = 7233
        state.temporal_frontend_port = 7233

        validator = WizardValidator(state)
        assert not validator.validate_port_conflicts()
        assert len(validator.errors) == 1


class TestCompleteStateValidation:
    """Test validation of complete wizard state."""

    def test_validate_state_complete_valid(self) -> None:
        """Test validation of complete valid wizard state."""
        state = WizardState()
        state.project_name = "test-project"
        state.services_enabled = {"redis": True, "postgres": True}
        state.postgres_database = "test_db"
        state.deployment_method = "docker-compose"

        validator = WizardValidator(state)
        assert validator.validate_state()
        assert len(validator.errors) == 0

    def test_validate_state_with_temporal(self) -> None:
        """Test validation with Temporal enabled."""
        state = WizardState()
        state.project_name = "test-project"
        state.services_enabled = {"redis": True, "postgres": True, "temporal": True}
        state.postgres_database = "test_db"
        state.temporal_namespace = "test-namespace"
        state.deployment_method = "docker-compose"

        validator = WizardValidator(state)
        assert validator.validate_state()
        assert len(validator.errors) == 0

    def test_validate_state_multiple_errors(self) -> None:
        """Test validation with multiple errors."""
        state = WizardState()
        state.project_name = "invalid project!"
        state.services_enabled = {}
        state.postgres_database = "123-invalid"
        state.deployment_method = "invalid-method"

        validator = WizardValidator(state)
        assert not validator.validate_state()
        # At least 3 errors: project name, services, deployment method
        assert len(validator.errors) >= 3

    def test_validate_state_port_conflicts(self) -> None:
        """Test state validation detects port conflicts."""
        state = WizardState()
        state.project_name = "test-project"
        state.services_enabled = {"redis": True, "postgres": True}
        state.redis_port = 5432
        state.postgres_port = 5432
        state.postgres_database = "test_db"

        validator = WizardValidator(state)
        assert not validator.validate_state()
        assert any("conflicts" in err.message for err in validator.errors)


class TestValidatorHelpers:
    """Test validator helper methods."""

    def test_get_errors(self) -> None:
        """Test getting validation errors."""
        state = WizardState()
        validator = WizardValidator(state)

        validator.validate_project_name("")
        validator.validate_project_name("invalid!")

        errors = validator.get_errors()
        assert len(errors) == 2
        assert all(isinstance(err, ValidationError) for err in errors)

    def test_get_error_messages(self) -> None:
        """Test getting formatted error messages."""
        state = WizardState()
        validator = WizardValidator(state)

        validator.validate_project_name("")
        validator.validate_port(80, "redis")

        messages = validator.get_error_messages()
        assert len(messages) == 2
        assert all(isinstance(msg, str) for msg in messages)
        assert all(":" in msg for msg in messages)

    def test_has_errors(self) -> None:
        """Test checking if validator has errors."""
        state = WizardState()
        validator = WizardValidator(state)

        assert not validator.has_errors()

        validator.validate_project_name("")
        assert validator.has_errors()

    def test_errors_reset_on_validate_state(self) -> None:
        """Test that errors are reset when validate_state is called."""
        state = WizardState()
        state.project_name = "test-project"
        state.services_enabled = {"redis": True}
        validator = WizardValidator(state)

        # Add some errors
        validator.validate_project_name("")
        assert len(validator.errors) == 1

        # validate_state should reset errors
        validator.validate_state()
        # Should only have errors from validate_state, not the previous call
        assert all(
            err.field != "project_name" or "empty" not in err.message
            for err in validator.errors
        )
