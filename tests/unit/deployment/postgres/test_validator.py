"""Comprehensive tests for PostgreSQL-Temporal validation engine.

This test suite validates the PostgresValidator's ability to check compatibility
between PostgreSQL and Temporal versions with clear, actionable feedback.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mycelium_onboarding.deployment.postgres.validator import (
    PostgresValidator,
    ValidationResult,
    validate_postgres_for_temporal,
)


@pytest.fixture
def tmp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory for tests.

    Args:
        tmp_path: Pytest temporary path fixture

    Returns:
        Path to temporary project directory
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def validator(tmp_project_dir: Path) -> PostgresValidator:
    """Create PostgresValidator instance for testing.

    Args:
        tmp_project_dir: Temporary project directory

    Returns:
        PostgresValidator instance
    """
    return PostgresValidator(tmp_project_dir)


class TestValidationResult:
    """Test ValidationResult NamedTuple and formatting."""

    def test_validation_result_creation(self):
        """Test creating ValidationResult with all fields."""
        result = ValidationResult(
            is_compatible=True,
            temporal_version="1.22.0",
            postgres_version="15.3",
            warning_message=None,
            error_message=None,
            recommended_action="Deployment can proceed",
            can_proceed=True,
            support_level="active",
            requires_postgres_upgrade=False,
            requires_temporal_downgrade=False,
        )

        assert result.is_compatible is True
        assert result.temporal_version == "1.22.0"
        assert result.postgres_version == "15.3"
        assert result.can_proceed is True

    def test_format_message_compatible(self):
        """Test formatting message for compatible versions."""
        result = ValidationResult(
            is_compatible=True,
            temporal_version="1.22.0",
            postgres_version="15.0",
            warning_message=None,
            error_message=None,
            recommended_action="Deployment can proceed. Versions are compatible.",
            can_proceed=True,
            support_level="active",
        )

        formatted = result.format_message()
        assert "✓ PostgreSQL Compatibility Check: PASSED" in formatted
        assert "Temporal Version: 1.22.0" in formatted
        assert "PostgreSQL Version: 15.0" in formatted
        assert "Deployment can proceed" in formatted

    def test_format_message_incompatible(self):
        """Test formatting message for incompatible versions."""
        result = ValidationResult(
            is_compatible=False,
            temporal_version="1.22.0",
            postgres_version="12.0",
            warning_message="PostgreSQL 12.0 is too old",
            error_message="Version mismatch",
            recommended_action="Upgrade PostgreSQL to 13.0+",
            can_proceed=True,
            support_level="active",
        )

        formatted = result.format_message()
        assert "✗ PostgreSQL Compatibility Check: FAILED" in formatted
        assert "PostgreSQL 12.0 is too old" in formatted
        assert "Upgrade PostgreSQL to 13.0+" in formatted
        assert "--force-version" in formatted

    def test_format_message_with_warning(self):
        """Test formatting message with compatibility warning."""
        result = ValidationResult(
            is_compatible=True,
            temporal_version="1.5.0",
            postgres_version="15.0",
            warning_message="Temporal 1.5.0 is deprecated (EOL: 2022-09-01)",
            error_message=None,
            recommended_action="Consider upgrading Temporal",
            can_proceed=True,
            support_level="deprecated",
        )

        formatted = result.format_message()
        assert "✓ PostgreSQL Compatibility Check: PASSED" in formatted
        assert "⚠️  Warning: Temporal 1.5.0 is deprecated" in formatted


class TestPostgresValidatorBasic:
    """Test basic PostgresValidator functionality."""

    def test_validator_initialization(self, tmp_project_dir: Path):
        """Test validator initialization with project directory."""
        validator = PostgresValidator(tmp_project_dir)
        assert validator.project_dir == tmp_project_dir
        assert validator.compatibility_checker is not None

    def test_validator_initialization_default_dir(self):
        """Test validator initialization with default (current) directory."""
        validator = PostgresValidator()
        assert validator.project_dir == Path.cwd()

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_no_temporal_detected(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test validation when Temporal version cannot be detected."""
        mock_detect.return_value = None

        result = validator.validate_deployment("15.0")

        assert result.is_compatible is False
        assert result.temporal_version == "unknown"
        assert result.postgres_version == "15.0"
        assert "Cannot detect Temporal version" in result.error_message
        assert result.can_proceed is False
        assert "dependencies" in result.recommended_action


class TestCompatibilityValidation:
    """Test PostgreSQL-Temporal compatibility validation scenarios."""

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_compatible_versions(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test validation with compatible versions (pass scenario)."""
        # Mock Temporal detection
        temporal_version = MagicMock()
        temporal_version.version = "1.22.0"
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        result = validator.validate_deployment("15.0")

        assert result.is_compatible is True
        assert result.temporal_version == "1.22.0"
        assert result.postgres_version == "15.0"
        assert result.error_message is None
        assert result.can_proceed is True
        assert result.support_level == "active"

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_postgres_too_old(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test validation with PostgreSQL version too old."""
        # Mock Temporal 1.22.0 which requires PostgreSQL 13+
        temporal_version = MagicMock()
        temporal_version.version = "1.22.0"
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        result = validator.validate_deployment("12.0")

        assert result.is_compatible is False
        assert result.temporal_version == "1.22.0"
        assert result.postgres_version == "12.0"
        assert result.requires_postgres_upgrade is True
        assert result.requires_temporal_downgrade is False
        assert "too old" in result.warning_message
        assert result.can_proceed is True  # Can force proceed
        assert "Upgrade PostgreSQL" in result.recommended_action

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_postgres_too_new(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test validation with PostgreSQL version too new."""
        # Mock Temporal 1.5.0 which has max PostgreSQL 15
        temporal_version = MagicMock()
        temporal_version.version = "1.5.0"
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        result = validator.validate_deployment("17.0")

        assert result.is_compatible is False
        assert result.temporal_version == "1.5.0"
        assert result.postgres_version == "17.0"
        assert result.requires_postgres_upgrade is False
        assert result.requires_temporal_downgrade is True
        assert "too new" in result.warning_message
        assert result.can_proceed is True
        assert "Upgrade Temporal" in result.recommended_action

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_deprecated_temporal_warning(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test warning for deprecated Temporal version."""
        # Mock deprecated Temporal 1.0.0
        temporal_version = MagicMock()
        temporal_version.version = "1.0.0"
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        result = validator.validate_deployment("13.0")

        assert result.is_compatible is True  # Still compatible
        assert result.support_level == "deprecated"
        assert result.warning_message is not None
        assert "deprecated" in result.warning_message.lower()
        assert "Consider upgrading" in result.recommended_action

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_unknown_temporal_version(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test handling of unknown Temporal version."""
        # Mock unknown Temporal version
        temporal_version = MagicMock()
        temporal_version.version = "99.99.99"
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        result = validator.validate_deployment("15.0")

        # Should use default compatibility matrix
        assert result.temporal_version == "99.99.99"
        assert result.support_level == "unknown"
        assert "Manually verify" in result.recommended_action

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_eol_postgres_warning(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test warning for EOL PostgreSQL version."""
        # Mock Temporal 1.10.0 which supports PostgreSQL 12
        temporal_version = MagicMock()
        temporal_version.version = "1.10.0"
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        result = validator.validate_deployment("12.0")

        # PostgreSQL 12 is compatible but EOL
        assert result.is_compatible is True
        assert result.warning_message is not None
        assert "deprecated" in result.warning_message.lower() or "eol" in result.warning_message.lower()


class TestExplicitTemporalVersion:
    """Test validation with explicitly provided Temporal version."""

    def test_explicit_temporal_version(self, validator: PostgresValidator):
        """Test validation with explicit Temporal version (no detection)."""
        result = validator.validate_deployment("15.0", temporal_version="1.22.0")

        assert result.is_compatible is True
        assert result.temporal_version == "1.22.0"
        assert result.postgres_version == "15.0"

    def test_explicit_temporal_overrides_detection(self, validator: PostgresValidator, tmp_project_dir: Path):
        """Test that explicit Temporal version overrides detection."""
        # Create a pyproject.toml with different version
        pyproject = tmp_project_dir / "pyproject.toml"
        pyproject.write_text('[project]\ndependencies = ["temporalio==1.5.0"]\n')

        # Explicitly provide different version
        result = validator.validate_deployment("15.0", temporal_version="1.24.0")

        # Should use explicit version, not detected
        assert result.temporal_version == "1.24.0"


class TestUpgradePathValidation:
    """Test PostgreSQL upgrade path validation."""

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_valid_upgrade_path(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test validation of valid PostgreSQL upgrade path."""
        temporal_version = MagicMock()
        temporal_version.version = "1.22.0"
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        result = validator.validate_upgrade_path("14.0", "16.0")

        assert result.is_compatible is True
        assert result.temporal_version == "1.22.0"
        assert "14.0 → 16.0" in result.postgres_version
        assert "compatible" in result.recommended_action.lower()
        assert "backup" in result.recommended_action.lower()

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_invalid_upgrade_path(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test validation of invalid PostgreSQL upgrade path."""
        # Temporal 1.0.0 doesn't support PostgreSQL 17
        temporal_version = MagicMock()
        temporal_version.version = "1.0.0"
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        result = validator.validate_upgrade_path("12.0", "17.0")

        assert result.is_compatible is False
        assert "incompatible" in result.warning_message.lower()
        assert "Choose a PostgreSQL version" in result.recommended_action


class TestCanProceedLogic:
    """Test can_proceed flag logic for --force scenarios."""

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_can_proceed_true_when_compatible(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test can_proceed is True for compatible versions."""
        temporal_version = MagicMock()
        temporal_version.version = "1.22.0"
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        result = validator.validate_deployment("15.0")

        assert result.is_compatible is True
        assert result.can_proceed is True

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_can_proceed_true_for_version_mismatch(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test can_proceed is True for version mismatches (allow --force)."""
        temporal_version = MagicMock()
        temporal_version.version = "1.22.0"
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        # PostgreSQL too old - should allow force
        result = validator.validate_deployment("12.0")

        assert result.is_compatible is False
        assert result.can_proceed is True  # Can force proceed
        assert "--force-version" in result.format_message()

    def test_can_proceed_false_for_detection_failure(self, validator: PostgresValidator):
        """Test can_proceed is False when Temporal cannot be detected."""
        with patch(
            "mycelium_onboarding.deployment.postgres.validator.detect_temporal_version",
            return_value=None,
        ):
            result = validator.validate_deployment("15.0")

            assert result.is_compatible is False
            assert result.can_proceed is False
            assert "--force-version" not in result.format_message()


class TestRecommendedActions:
    """Test recommended action messages are clear and actionable."""

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_postgres_upgrade_recommended_actions(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test recommended actions for PostgreSQL upgrade scenario."""
        temporal_version = MagicMock()
        temporal_version.version = "1.22.0"
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        result = validator.validate_deployment("12.0")

        actions = result.recommended_action
        assert "Option 1: Upgrade PostgreSQL" in actions
        assert "Backup your database" in actions
        assert "https://www.postgresql.org" in actions
        assert "Option 2: Downgrade Temporal" in actions
        assert "Check compatibility matrix" in actions

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_temporal_upgrade_recommended_actions(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test recommended actions for Temporal upgrade scenario."""
        temporal_version = MagicMock()
        temporal_version.version = "1.5.0"
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        result = validator.validate_deployment("17.0")

        actions = result.recommended_action
        assert "Option 1: Use PostgreSQL" in actions
        assert "Option 2: Upgrade Temporal" in actions
        assert "Update Temporal SDK" in actions

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_no_auto_upgrade_suggestion(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test that recommendations NEVER suggest auto-upgrading PostgreSQL."""
        temporal_version = MagicMock()
        temporal_version.version = "1.22.0"
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        result = validator.validate_deployment("12.0")

        actions = result.recommended_action.lower()
        # Should NOT contain auto-upgrade suggestions
        assert "automatically upgrade" not in actions
        assert "auto-upgrade" not in actions
        # Should contain manual upgrade instructions
        assert "backup" in actions
        assert "follow postgresql upgrade guide" in actions


class TestConvenienceFunction:
    """Test the convenience function validate_postgres_for_temporal."""

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_convenience_function(self, mock_detect: MagicMock, tmp_project_dir: Path):
        """Test the standalone validation convenience function."""
        temporal_version = MagicMock()
        temporal_version.version = "1.22.0"
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        result = validate_postgres_for_temporal(postgres_version="15.0", project_dir=tmp_project_dir)

        assert isinstance(result, ValidationResult)
        assert result.is_compatible is True
        assert result.temporal_version == "1.22.0"

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_convenience_function_with_explicit_temporal(self, mock_detect: MagicMock, tmp_project_dir: Path):
        """Test convenience function with explicit Temporal version."""
        result = validate_postgres_for_temporal(
            postgres_version="15.0",
            project_dir=tmp_project_dir,
            temporal_version="1.24.0",
        )

        assert result.temporal_version == "1.24.0"
        # Should not call detect function
        mock_detect.assert_not_called()


class TestEdgeCases:
    """Test edge cases and error handling."""

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_version_parsing_with_different_formats(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test validation handles different version formats."""
        temporal_version = MagicMock()
        temporal_version.version = "1.22.0"
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        # Test different PostgreSQL version formats
        test_versions = ["15", "15.0", "15.3", "v15.3"]

        for pg_version in test_versions:
            result = validator.validate_deployment(pg_version)
            # All should normalize and validate successfully
            assert result.temporal_version == "1.22.0"

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_metadata_in_validation_result(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test that validation result contains all required metadata."""
        temporal_version = MagicMock()
        temporal_version.version = "1.22.0"
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        result = validator.validate_deployment("15.0")

        # Verify all required fields are present
        assert hasattr(result, "is_compatible")
        assert hasattr(result, "temporal_version")
        assert hasattr(result, "postgres_version")
        assert hasattr(result, "warning_message")
        assert hasattr(result, "error_message")
        assert hasattr(result, "recommended_action")
        assert hasattr(result, "can_proceed")
        assert hasattr(result, "support_level")
        assert hasattr(result, "requires_postgres_upgrade")
        assert hasattr(result, "requires_temporal_downgrade")


class TestIntegrationWithCompatibilityMatrix:
    """Test integration with PostgresCompatibilityChecker."""

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_uses_compatibility_matrix_data(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test that validator uses data from compatibility.yaml."""
        temporal_version = MagicMock()
        temporal_version.version = "1.24.0"
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        result = validator.validate_deployment("16.0")

        # Should use compatibility matrix data
        assert result.is_compatible is True
        assert result.support_level == "active"

    @patch("mycelium_onboarding.deployment.postgres.validator.detect_temporal_version")
    def test_handles_version_ranges(self, mock_detect: MagicMock, validator: PostgresValidator):
        """Test that validator handles version ranges correctly."""
        # Test Temporal 1.22.x series
        temporal_version = MagicMock()
        temporal_version.version = "1.22.3"  # Patch version
        temporal_version.source_file = Path("pyproject.toml")
        mock_detect.return_value = temporal_version

        result = validator.validate_deployment("15.0")

        # Should map to 1.22.0 compatibility entry
        assert result.temporal_version == "1.22.3"
        assert result.is_compatible is True
