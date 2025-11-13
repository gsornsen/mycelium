"""Tests for PostgreSQL validation integration in deployment commands.

This module tests the integration of PostgreSQL-Temporal compatibility validation
into the deployment flow, including CLI flags and user interactions.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from click.testing import CliRunner

from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.deployment.commands.deploy import DeployCommand, DeploymentPhase, DeploymentPlan
from mycelium_onboarding.deployment.postgres.validator import ValidationResult
from mycelium_onboarding.deployment.strategy.detector import DetectedService, ServiceStatus, ServiceType


@pytest.fixture
def mock_config():
    """Create a mock Mycelium configuration."""
    config = MyceliumConfig()
    config.project_name = "test-project"
    config.services.postgres.enabled = True
    config.services.temporal.enabled = True
    config.services.redis.enabled = False
    return config


@pytest.fixture
def detected_postgres_service():
    """Create a detected PostgreSQL service."""
    return DetectedService(
        name="postgres-15",
        service_type=ServiceType.POSTGRESQL,
        status=ServiceStatus.RUNNING,
        host="localhost",
        port=5432,
        version="15.3",
        connection_string="postgresql://localhost:5432/postgres",
    )


@pytest.fixture
def detected_services_with_postgres(detected_postgres_service):
    """Create list of detected services including PostgreSQL."""
    return [detected_postgres_service]


@pytest.fixture
def deploy_command(tmp_path):
    """Create a DeployCommand instance for testing."""
    return DeployCommand(
        verbose=False,
        dry_run=False,
        force=False,
        force_version=False,
        postgres_version=None,
        temporal_version=None,
        working_dir=tmp_path,
    )


class TestPostgreSQLValidationIntegration:
    """Test PostgreSQL-Temporal validation integration in deployment flow."""

    def test_validation_with_compatible_versions(
        self, deploy_command, mock_config, detected_services_with_postgres, tmp_path
    ):
        """Test deployment with compatible PostgreSQL and Temporal versions."""
        # Create a mock compatible validation result
        compatible_result = ValidationResult(
            is_compatible=True,
            temporal_version="1.24.0",
            postgres_version="15.3",
            warning_message=None,
            error_message=None,
            recommended_action="Deployment can proceed. Versions are compatible.",
            can_proceed=True,
            support_level="active",
        )

        with (
            patch.object(deploy_command, "_load_or_find_config", return_value=mock_config),
            patch("mycelium_onboarding.deployment.commands.deploy.validate_postgres_for_temporal") as mock_validate,
        ):
            mock_validate.return_value = compatible_result

            with patch("mycelium_onboarding.deployment.commands.deploy.WarningFormatter"):
                result = deploy_command._validate_postgres_compatibility(detected_services_with_postgres)

        assert result is True
        mock_validate.assert_called_once()

    def test_validation_with_incompatible_versions_user_cancels(
        self, deploy_command, mock_config, detected_services_with_postgres
    ):
        """Test deployment cancelled when PostgreSQL incompatible and user cancels."""
        # Create a mock incompatible validation result
        incompatible_result = ValidationResult(
            is_compatible=False,
            temporal_version="1.24.0",
            postgres_version="12.0",
            warning_message="PostgreSQL 12.0 is too old for Temporal 1.24.0",
            error_message=None,
            recommended_action="Upgrade PostgreSQL to 13.0+",
            can_proceed=True,
            support_level="deprecated",
            requires_postgres_upgrade=True,
        )

        with (
            patch.object(deploy_command, "_load_or_find_config", return_value=mock_config),
            patch("mycelium_onboarding.deployment.commands.deploy.validate_postgres_for_temporal") as mock_validate,
        ):
            mock_validate.return_value = incompatible_result

            with (
                patch("mycelium_onboarding.deployment.commands.deploy.WarningFormatter"),
                patch("mycelium_onboarding.deployment.commands.deploy.Confirm.ask", return_value=False),
            ):
                result = deploy_command._validate_postgres_compatibility(detected_services_with_postgres)

        assert result is False

    @pytest.mark.asyncio
    async def test_validation_with_incompatible_versions_user_continues(
        self, deploy_command, mock_config, detected_services_with_postgres
    ):
        """Test deployment continues when user confirms despite incompatibility."""
        incompatible_result = ValidationResult(
            is_compatible=False,
            temporal_version="1.24.0",
            postgres_version="12.0",
            warning_message="PostgreSQL 12.0 is too old for Temporal 1.24.0",
            error_message=None,
            recommended_action="Upgrade PostgreSQL to 13.0+",
            can_proceed=True,
            support_level="deprecated",
            requires_postgres_upgrade=True,
        )

        with (
            patch.object(deploy_command, "_load_or_find_config", return_value=mock_config),
            patch("mycelium_onboarding.deployment.commands.deploy.validate_postgres_for_temporal") as mock_validate,
        ):
            mock_validate.return_value = incompatible_result

            with (
                patch("mycelium_onboarding.deployment.commands.deploy.WarningFormatter"),
                patch("mycelium_onboarding.deployment.commands.deploy.Confirm.ask", return_value=True),
            ):
                result = deploy_command._validate_postgres_compatibility(detected_services_with_postgres)

        assert result is True

    def test_validation_with_critical_incompatibility(
        self, deploy_command, mock_config, detected_services_with_postgres
    ):
        """Test deployment blocked when critical incompatibility detected."""
        critical_result = ValidationResult(
            is_compatible=False,
            temporal_version="1.24.0",
            postgres_version="9.6",
            warning_message=None,
            error_message="PostgreSQL 9.6 is fundamentally incompatible",
            recommended_action="Upgrade PostgreSQL to 13.0+ immediately",
            can_proceed=False,
            support_level="unknown",
            requires_postgres_upgrade=True,
        )

        with (
            patch.object(deploy_command, "_load_or_find_config", return_value=mock_config),
            patch("mycelium_onboarding.deployment.commands.deploy.validate_postgres_for_temporal") as mock_validate,
        ):
            mock_validate.return_value = critical_result

            with patch("mycelium_onboarding.deployment.commands.deploy.WarningFormatter"):
                result = deploy_command._validate_postgres_compatibility(detected_services_with_postgres)

        assert result is False

    @pytest.mark.asyncio
    async def test_validation_skipped_with_force_version_flag(
        self, deploy_command, mock_config, detected_services_with_postgres
    ):
        """Test validation skipped when --force-version flag set."""
        # Set force_version flag
        deploy_command.force_version = True

        with (
            patch.object(deploy_command, "_load_or_find_config", return_value=mock_config),
            patch("mycelium_onboarding.deployment.commands.deploy.validate_postgres_for_temporal") as mock_validate,
        ):
            result = deploy_command._validate_postgres_compatibility(detected_services_with_postgres)

        # Validation should be skipped
        assert result is True
        mock_validate.assert_not_called()

    def test_validation_with_explicit_postgres_version(self, deploy_command, mock_config):
        """Test validation with explicitly provided PostgreSQL version."""
        # Set explicit version
        deploy_command.postgres_version = "14.5"

        compatible_result = ValidationResult(
            is_compatible=True,
            temporal_version="1.23.0",
            postgres_version="14.5",
            warning_message=None,
            error_message=None,
            recommended_action="Deployment can proceed.",
            can_proceed=True,
        )

        with (
            patch.object(deploy_command, "_load_or_find_config", return_value=mock_config),
            patch("mycelium_onboarding.deployment.commands.deploy.validate_postgres_for_temporal") as mock_validate,
        ):
            mock_validate.return_value = compatible_result

            with patch("mycelium_onboarding.deployment.commands.deploy.WarningFormatter"):
                result = deploy_command._validate_postgres_compatibility([])

        assert result is True
        # Should use explicit version
        call_args = mock_validate.call_args
        assert call_args[1]["postgres_version"] == "14.5"

    def test_validation_with_explicit_temporal_version(
        self, deploy_command, mock_config, detected_services_with_postgres
    ):
        """Test validation with explicitly provided Temporal version."""
        # Set explicit Temporal version
        deploy_command.temporal_version = "1.25.0"

        compatible_result = ValidationResult(
            is_compatible=True,
            temporal_version="1.25.0",
            postgres_version="15.3",
            warning_message=None,
            error_message=None,
            recommended_action="Deployment can proceed.",
            can_proceed=True,
        )

        with (
            patch.object(deploy_command, "_load_or_find_config", return_value=mock_config),
            patch("mycelium_onboarding.deployment.commands.deploy.validate_postgres_for_temporal") as mock_validate,
        ):
            mock_validate.return_value = compatible_result

            with patch("mycelium_onboarding.deployment.commands.deploy.WarningFormatter"):
                result = deploy_command._validate_postgres_compatibility(detected_services_with_postgres)

        assert result is True
        # Should use explicit Temporal version
        call_args = mock_validate.call_args
        assert call_args[1]["temporal_version"] == "1.25.0"

    @pytest.mark.asyncio
    async def test_validation_skipped_when_no_postgres_detected(self, deploy_command, mock_config):
        """Test validation skipped when PostgreSQL not detected."""
        # Empty detected services (no PostgreSQL)
        detected_services = []

        with (
            patch.object(deploy_command, "_load_or_find_config", return_value=mock_config),
            patch("mycelium_onboarding.deployment.commands.deploy.validate_postgres_for_temporal") as mock_validate,
        ):
            result = deploy_command._validate_postgres_compatibility(detected_services)

        # Should skip validation and return True
        assert result is True
        mock_validate.assert_not_called()

    @pytest.mark.asyncio
    async def test_validation_exception_handling(self, deploy_command, mock_config, detected_services_with_postgres):
        """Test graceful handling of validation exceptions."""
        with (
            patch.object(deploy_command, "_load_or_find_config", return_value=mock_config),
            patch("mycelium_onboarding.deployment.commands.deploy.validate_postgres_for_temporal") as mock_validate,
        ):
            mock_validate.side_effect = Exception("Validation error")

            # Should continue deployment despite exception
            result = deploy_command._validate_postgres_compatibility(detected_services_with_postgres)

        assert result is True  # Gracefully continues

    @pytest.mark.asyncio
    async def test_validation_in_deployment_flow(self, deploy_command, mock_config, detected_services_with_postgres):
        """Test validation integrated into full deployment flow."""
        compatible_result = ValidationResult(
            is_compatible=True,
            temporal_version="1.24.0",
            postgres_version="15.3",
            warning_message=None,
            error_message=None,
            recommended_action="Deployment can proceed.",
            can_proceed=True,
        )

        # Create a proper mock DeploymentPlan
        mock_plan = DeploymentPlan(
            plan_id="test-plan-123",
            detected_services=detected_services_with_postgres,
            reusable_services=[],
            new_services=["postgres", "temporal"],
        )

        # Mock all dependencies
        with (
            patch.object(deploy_command, "_load_or_find_config", return_value=mock_config),
            patch.object(deploy_command, "_detect_services", new_callable=AsyncMock) as mock_detect,
        ):
            mock_detect.return_value = detected_services_with_postgres

            with patch.object(deploy_command, "_create_deployment_plan", new_callable=AsyncMock) as mock_create_plan:
                mock_create_plan.return_value = mock_plan

                with (
                    patch.object(deploy_command, "_confirm_deployment", return_value=False),
                    patch(
                        "mycelium_onboarding.deployment.commands.deploy.validate_postgres_for_temporal"
                    ) as mock_validate,
                    patch("mycelium_onboarding.deployment.commands.deploy.WarningFormatter"),
                ):
                    mock_validate.return_value = compatible_result
                    # Run deployment (will be cancelled at confirmation)
                    success = await deploy_command.start(auto_approve=False)

        # Deployment cancelled at confirmation, but validation should have run
        assert success is False
        mock_validate.assert_called_once()


class TestDeployCommandFlags:
    """Test DeployCommand initialization with various flags."""

    def test_deploy_command_with_force_version(self, tmp_path):
        """Test DeployCommand initialized with --force-version flag."""
        cmd = DeployCommand(force_version=True, working_dir=tmp_path)
        assert cmd.force_version is True

    def test_deploy_command_with_postgres_version(self, tmp_path):
        """Test DeployCommand initialized with --postgres-version flag."""
        cmd = DeployCommand(postgres_version="14.5", working_dir=tmp_path)
        assert cmd.postgres_version == "14.5"

    def test_deploy_command_with_temporal_version(self, tmp_path):
        """Test DeployCommand initialized with --temporal-version flag."""
        cmd = DeployCommand(temporal_version="1.23.0", working_dir=tmp_path)
        assert cmd.temporal_version == "1.23.0"

    def test_deploy_command_with_all_flags(self, tmp_path):
        """Test DeployCommand initialized with all version flags."""
        cmd = DeployCommand(
            force_version=True, postgres_version="15.0", temporal_version="1.24.0", verbose=True, working_dir=tmp_path
        )
        assert cmd.force_version is True
        assert cmd.postgres_version == "15.0"
        assert cmd.temporal_version == "1.24.0"
        assert cmd.verbose is True


class TestDeploymentPhaseIntegration:
    """Test that validation phase is properly integrated into deployment steps."""

    def test_validation_phase_in_deployment_steps(self, deploy_command):
        """Test that validation phase appears in deployment steps."""
        from mycelium_onboarding.deployment.commands.deploy import DeploymentPlan

        plan = DeploymentPlan(plan_id="test-plan")
        deploy_command._generate_deployment_steps(plan)

        # Find validation step
        validation_steps = [step for step in plan.deployment_steps if step.phase == DeploymentPhase.VALIDATION]

        assert len(validation_steps) > 0
        # Check for PostgreSQL compatibility validation step
        postgres_validation = [s for s in validation_steps if "PostgreSQL" in s.name]
        assert len(postgres_validation) > 0
        assert postgres_validation[0].name == "PostgreSQL Compatibility"


class TestCLIIntegration:
    """Test CLI integration with version flags."""

    def test_cli_help_shows_version_flags(self):
        """Test that CLI help displays version-related flags."""
        from mycelium_onboarding.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["deploy", "start", "--help"])

        assert result.exit_code == 0
        assert "--force-version" in result.output
        assert "--postgres-version" in result.output
        assert "--temporal-version" in result.output
        assert "compatibility" in result.output.lower()

    def test_cli_deploy_start_accepts_force_version(self):
        """Test that deploy start accepts --force-version flag."""
        from mycelium_onboarding.cli import cli

        runner = CliRunner()

        # This will fail because no config exists, but it should parse the flag
        with patch("mycelium_onboarding.deployment.commands.deploy.DeployCommand") as mock_cmd_class:
            mock_instance = Mock()
            mock_instance.start = AsyncMock(return_value=True)
            mock_cmd_class.return_value = mock_instance

            # Need to mock asyncio.run
            with patch("asyncio.run", return_value=True):
                runner.invoke(cli, ["deploy", "start", "--force-version", "--dry-run"], catch_exceptions=False)

        # Check that DeployCommand was instantiated with force_version=True
        call_kwargs = mock_cmd_class.call_args[1]
        assert call_kwargs.get("force_version") is True

    def test_cli_deploy_start_accepts_postgres_version(self):
        """Test that deploy start accepts --postgres-version flag."""
        from mycelium_onboarding.cli import cli

        runner = CliRunner()

        with patch("mycelium_onboarding.deployment.commands.deploy.DeployCommand") as mock_cmd_class:
            mock_instance = Mock()
            mock_instance.start = AsyncMock(return_value=True)
            mock_cmd_class.return_value = mock_instance

            with patch("asyncio.run", return_value=True):
                runner.invoke(
                    cli, ["deploy", "start", "--postgres-version", "15.3", "--dry-run"], catch_exceptions=False
                )

        call_kwargs = mock_cmd_class.call_args[1]
        assert call_kwargs.get("postgres_version") == "15.3"

    def test_cli_deploy_start_accepts_temporal_version(self):
        """Test that deploy start accepts --temporal-version flag."""
        from mycelium_onboarding.cli import cli

        runner = CliRunner()

        with patch("mycelium_onboarding.deployment.commands.deploy.DeployCommand") as mock_cmd_class:
            mock_instance = Mock()
            mock_instance.start = AsyncMock(return_value=True)
            mock_cmd_class.return_value = mock_instance

            with patch("asyncio.run", return_value=True):
                runner.invoke(
                    cli, ["deploy", "start", "--temporal-version", "1.24.0", "--dry-run"], catch_exceptions=False
                )

        call_kwargs = mock_cmd_class.call_args[1]
        assert call_kwargs.get("temporal_version") == "1.24.0"


class TestSafetyChecklist:
    """Test safety requirements - NO auto-upgrade functionality."""

    def test_no_auto_upgrade_in_validation_result(self):
        """Test that ValidationResult never triggers auto-upgrade."""
        # This is a documentation test - ensure ValidationResult only provides warnings
        result = ValidationResult(
            is_compatible=False,
            temporal_version="1.24.0",
            postgres_version="12.0",
            warning_message="PostgreSQL too old",
            error_message=None,
            recommended_action="Manually upgrade PostgreSQL to 13.0+",
            can_proceed=True,
            requires_postgres_upgrade=True,
        )

        # Verify recommended action is manual
        assert "manual" in result.recommended_action.lower() or "upgrade" in result.recommended_action.lower()
        # Should not contain automatic/auto
        assert "automatic" not in result.recommended_action.lower()
        assert "auto-upgrade" not in result.recommended_action.lower()

    def test_no_upgrade_execution_in_deploy_command(self, deploy_command):
        """Test that DeployCommand has no auto-upgrade methods."""
        # Check that there are no upgrade-related methods
        methods = [m for m in dir(deploy_command) if not m.startswith("_")]
        upgrade_methods = [m for m in methods if "upgrade" in m.lower() and "postgres" in m.lower()]

        # Should have no PostgreSQL upgrade methods
        assert len(upgrade_methods) == 0

    def test_force_version_only_skips_validation(self, deploy_command, detected_services_with_postgres):
        """Test that --force-version only bypasses checks, doesn't upgrade."""
        deploy_command.force_version = True

        with patch("mycelium_onboarding.deployment.commands.deploy.validate_postgres_for_temporal") as mock_validate:
            result = deploy_command._validate_postgres_compatibility(detected_services_with_postgres)

        # Should skip validation, not perform upgrade
        assert result is True
        mock_validate.assert_not_called()
