"""Tests for CLI init command integration.

This module tests the `mycelium init` command, which provides an interactive
wizard for onboarding users to the Mycelium project. Tests cover all wizard
flows, state persistence, validation, and error handling.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner

from mycelium_onboarding.cli import cli
from mycelium_onboarding.wizard.flow import WizardState, WizardStep
from mycelium_onboarding.detection.orchestrator import DetectionSummary


class TestInitCommand:
    """Test suite for the init command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Provide Click test runner with clean environment."""
        # Create runner with isolated environment (no MYCELIUM_* vars)
        return CliRunner(env={
            k: v for k, v in __import__('os').environ.items()
            if not k.startswith('MYCELIUM_')
        })

    @pytest.fixture
    def mock_state(self) -> WizardState:
        """Provide a mock wizard state."""
        state = WizardState()
        state.project_name = "test-project"
        state.services_enabled = {"redis": True, "postgres": True, "temporal": False}
        state.deployment_method = "docker-compose"
        state.postgres_database = "test_db"
        return state

    @pytest.fixture
    def mock_detection_summary(self) -> DetectionSummary:
        """Provide mock detection summary."""
        return Mock(spec=DetectionSummary)

    def test_init_fresh_start(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test init command with fresh start (no saved state)."""
        with patch(
            "mycelium_onboarding.wizard.persistence.WizardStatePersistence"
        ) as mock_persistence_class:
            # Setup mock persistence
            mock_persistence = MagicMock()
            mock_persistence.exists.return_value = False
            mock_persistence_class.return_value = mock_persistence

            # Setup mock screens to exit quickly
            with patch("mycelium_onboarding.wizard.screens.WizardScreens") as mock_screens:
                mock_screens.return_value.show_welcome.side_effect = SystemExit(0)

                # Run command
                result = runner.invoke(cli, ["init", "--no-resume"])

                # Verify persistence was checked
                mock_persistence.exists.assert_called()

    def test_init_with_resume_flag(self, runner: CliRunner, mock_state: WizardState) -> None:
        """Test init command with --resume flag when state exists."""
        with patch(
            "mycelium_onboarding.wizard.persistence.WizardStatePersistence"
        ) as mock_persistence_class:
            # Setup mock persistence with saved state
            mock_persistence = MagicMock()
            mock_persistence.exists.return_value = True
            mock_persistence.load.return_value = mock_state
            mock_persistence_class.return_value = mock_persistence

            # Setup mock screens to exit quickly
            with patch("mycelium_onboarding.wizard.screens.WizardScreens") as mock_screens:
                mock_screens.return_value.show_welcome.side_effect = SystemExit(0)

                # Run command
                result = runner.invoke(cli, ["init", "--resume"])

                # Verify state was loaded
                mock_persistence.load.assert_called_once()

    def test_init_with_reset_flag(self, runner: CliRunner) -> None:
        """Test init command with --reset flag clears saved state."""
        with patch(
            "mycelium_onboarding.wizard.persistence.WizardStatePersistence"
        ) as mock_persistence_class:
            # Setup mock persistence
            mock_persistence = MagicMock()
            mock_persistence.exists.return_value = True
            mock_persistence_class.return_value = mock_persistence

            # Setup mock screens to exit quickly
            with patch("mycelium_onboarding.wizard.screens.WizardScreens") as mock_screens:
                mock_screens.return_value.show_welcome.side_effect = SystemExit(0)

                # Run command
                result = runner.invoke(cli, ["init", "--reset", "--no-resume"])

                # Verify state was cleared
                mock_persistence.clear.assert_called()

    def test_init_resume_confirmation_yes(
        self, runner: CliRunner, mock_state: WizardState
    ) -> None:
        """Test init command with resume confirmation (user selects yes)."""
        with patch(
            "mycelium_onboarding.wizard.persistence.WizardStatePersistence"
        ) as mock_persistence_class:
            # Setup mock persistence with saved state
            mock_persistence = MagicMock()
            mock_persistence.exists.return_value = True
            mock_persistence.load.return_value = mock_state
            mock_persistence_class.return_value = mock_persistence

            # Setup mock screens to exit quickly
            with patch("mycelium_onboarding.wizard.screens.WizardScreens") as mock_screens:
                mock_screens.return_value.show_welcome.side_effect = SystemExit(0)

                # Run command with "yes" input
                result = runner.invoke(cli, ["init"], input="y\n")

                # Verify state was loaded
                mock_persistence.load.assert_called()

    def test_init_resume_confirmation_no(self, runner: CliRunner) -> None:
        """Test init command with resume confirmation (user selects no)."""
        with patch(
            "mycelium_onboarding.wizard.persistence.WizardStatePersistence"
        ) as mock_persistence_class:
            # Setup mock persistence
            mock_persistence = MagicMock()
            mock_persistence.exists.return_value = True
            mock_persistence_class.return_value = mock_persistence

            # Setup mock screens to exit quickly
            with patch("mycelium_onboarding.wizard.screens.WizardScreens") as mock_screens:
                mock_screens.return_value.show_welcome.side_effect = SystemExit(0)

                # Run command with "no" input
                result = runner.invoke(cli, ["init"], input="n\n")

                # Verify load was not called
                mock_persistence.load.assert_not_called()

    def test_init_keyboard_interrupt(self, runner: CliRunner) -> None:
        """Test init command handles keyboard interrupt gracefully."""
        with patch(
            "mycelium_onboarding.wizard.persistence.WizardStatePersistence"
        ) as mock_persistence_class:
            # Setup mock persistence
            mock_persistence = MagicMock()
            mock_persistence.exists.return_value = False
            mock_persistence_class.return_value = mock_persistence

            # Setup mock screens to raise KeyboardInterrupt
            with patch("mycelium_onboarding.wizard.screens.WizardScreens") as mock_screens:
                mock_screens.return_value.show_welcome.side_effect = KeyboardInterrupt()

                # Run command
                result = runner.invoke(cli, ["init"])

                # Verify state was saved before exit
                assert mock_persistence.save.called
                assert result.exit_code == 1

    def test_init_complete_wizard_flow(
        self, runner: CliRunner, mock_detection_summary: DetectionSummary
    ) -> None:
        """Test complete wizard flow from welcome to completion."""
        with patch(
            "mycelium_onboarding.wizard.persistence.WizardStatePersistence"
        ) as mock_persistence_class:
            # Setup mock persistence
            mock_persistence = MagicMock()
            mock_persistence.exists.return_value = False
            mock_persistence_class.return_value = mock_persistence

            # Setup mock screens
            with patch("mycelium_onboarding.wizard.screens.WizardScreens") as mock_screens:
                screens = mock_screens.return_value
                screens.show_welcome.return_value = "quick"
                screens.show_detection.return_value = mock_detection_summary
                screens.show_services.return_value = {
                    "redis": True,
                    "postgres": True,
                    "temporal": False,
                }
                screens.show_deployment.return_value = "docker-compose"
                screens.show_review.return_value = "confirm"

                # Setup mock validator
                with patch("mycelium_onboarding.wizard.validation.WizardValidator") as mock_validator:
                    validator = mock_validator.return_value
                    validator.validate_state.return_value = True

                    # Setup mock config manager
                    with patch("mycelium_onboarding.config.manager.ConfigManager") as mock_manager:
                        manager = mock_manager.return_value
                        manager._determine_save_path.return_value = Path("/tmp/config.yaml")

                        # Run command with required inputs
                        result = runner.invoke(
                            cli, ["init", "--no-resume"], input="test-project\n"
                        )

                        # Verify wizard completed
                        assert screens.show_complete.called
                        # Verify state was cleared after completion
                        assert mock_persistence.clear.called

    def test_init_validation_errors(self, runner: CliRunner) -> None:
        """Test init command handles validation errors properly."""
        with patch(
            "mycelium_onboarding.wizard.persistence.WizardStatePersistence"
        ) as mock_persistence_class:
            # Setup mock persistence
            mock_persistence = MagicMock()
            mock_persistence.exists.return_value = False
            mock_persistence_class.return_value = mock_persistence

            # Setup mock screens
            with patch("mycelium_onboarding.wizard.screens.WizardScreens") as mock_screens:
                screens = mock_screens.return_value
                screens.show_welcome.return_value = "quick"
                screens.show_detection.return_value = Mock(spec=DetectionSummary)
                screens.show_services.return_value = {
                    "redis": True,
                    "postgres": False,
                    "temporal": False,
                }
                screens.show_deployment.return_value = "docker-compose"
                # First review returns confirm (triggers validation)
                # Then exit to avoid infinite loop
                screens.show_review.side_effect = ["confirm", SystemExit(0)]

                # Setup mock validator with errors
                with patch("mycelium_onboarding.wizard.validation.WizardValidator") as mock_validator:
                    validator = mock_validator.return_value
                    validator.validate_state.return_value = False
                    validator.get_error_messages.return_value = [
                        "Project name is required"
                    ]

                    # Run command
                    result = runner.invoke(cli, ["init"], input="\n")

                    # Verify validation was called
                    assert validator.validate_state.called

    def test_init_quick_mode_skips_advanced(
        self, runner: CliRunner, mock_detection_summary: DetectionSummary
    ) -> None:
        """Test quick mode skips advanced configuration screen."""
        with patch(
            "mycelium_onboarding.wizard.persistence.WizardStatePersistence"
        ) as mock_persistence_class:
            # Setup mock persistence
            mock_persistence = MagicMock()
            mock_persistence.exists.return_value = False
            mock_persistence_class.return_value = mock_persistence

            # Setup mock screens
            with patch("mycelium_onboarding.wizard.screens.WizardScreens") as mock_screens:
                screens = mock_screens.return_value
                screens.show_welcome.return_value = "quick"  # Quick mode
                screens.show_detection.return_value = mock_detection_summary
                screens.show_services.return_value = {
                    "redis": True,
                    "postgres": True,
                    "temporal": False,
                }
                screens.show_deployment.return_value = "docker-compose"
                screens.show_review.return_value = "confirm"

                # Setup mock validator
                with patch("mycelium_onboarding.wizard.validation.WizardValidator") as mock_validator:
                    validator = mock_validator.return_value
                    validator.validate_state.return_value = True

                    # Setup mock config manager
                    with patch("mycelium_onboarding.config.manager.ConfigManager") as mock_manager:
                        manager = mock_manager.return_value
                        manager._determine_save_path.return_value = Path("/tmp/config.yaml")

                        # Run command
                        result = runner.invoke(
                            cli, ["init", "--no-resume"], input="test-project\n"
                        )

                        # Verify advanced was NOT called
                        screens.show_advanced.assert_not_called()

    def test_init_custom_mode_shows_advanced(
        self, runner: CliRunner, mock_detection_summary: DetectionSummary
    ) -> None:
        """Test custom mode shows advanced configuration screen."""
        with patch(
            "mycelium_onboarding.wizard.persistence.WizardStatePersistence"
        ) as mock_persistence_class:
            # Setup mock persistence
            mock_persistence = MagicMock()
            mock_persistence.exists.return_value = False
            mock_persistence_class.return_value = mock_persistence

            # Setup mock screens
            with patch("mycelium_onboarding.wizard.screens.WizardScreens") as mock_screens:
                screens = mock_screens.return_value
                screens.show_welcome.return_value = "custom"  # Custom mode
                screens.show_detection.return_value = mock_detection_summary
                screens.show_services.return_value = {
                    "redis": True,
                    "postgres": True,
                    "temporal": False,
                }
                screens.show_deployment.return_value = "docker-compose"
                screens.show_advanced.return_value = None
                screens.show_review.return_value = "confirm"

                # Setup mock validator
                with patch("mycelium_onboarding.wizard.validation.WizardValidator") as mock_validator:
                    validator = mock_validator.return_value
                    validator.validate_state.return_value = True

                    # Setup mock config manager
                    with patch("mycelium_onboarding.config.manager.ConfigManager") as mock_manager:
                        manager = mock_manager.return_value
                        manager._determine_save_path.return_value = Path("/tmp/config.yaml")

                        # Run command
                        result = runner.invoke(
                            cli, ["init", "--no-resume"], input="test-project\n"
                        )

                        # Verify advanced WAS called
                        screens.show_advanced.assert_called_once()

    def test_init_state_persistence_on_each_step(
        self, runner: CliRunner, mock_detection_summary: DetectionSummary
    ) -> None:
        """Test that state is saved after each wizard step."""
        with patch(
            "mycelium_onboarding.wizard.persistence.WizardStatePersistence"
        ) as mock_persistence_class:
            # Setup mock persistence
            mock_persistence = MagicMock()
            mock_persistence.exists.return_value = False
            mock_persistence_class.return_value = mock_persistence

            # Setup mock screens
            with patch("mycelium_onboarding.wizard.screens.WizardScreens") as mock_screens:
                screens = mock_screens.return_value
                screens.show_welcome.return_value = "quick"
                screens.show_detection.return_value = mock_detection_summary
                screens.show_services.return_value = {
                    "redis": True,
                    "postgres": True,
                    "temporal": False,
                }
                screens.show_deployment.return_value = "docker-compose"
                screens.show_review.return_value = "confirm"

                # Setup mock validator
                with patch("mycelium_onboarding.wizard.validation.WizardValidator") as mock_validator:
                    validator = mock_validator.return_value
                    validator.validate_state.return_value = True

                    # Setup mock config manager
                    with patch("mycelium_onboarding.config.manager.ConfigManager") as mock_manager:
                        manager = mock_manager.return_value
                        manager._determine_save_path.return_value = Path("/tmp/config.yaml")

                        # Run command
                        result = runner.invoke(
                            cli, ["init", "--no-resume"], input="test-project\n"
                        )

                        # Verify save was called multiple times (once per step)
                        assert mock_persistence.save.call_count >= 4

    def test_init_config_generation_and_save(
        self, runner: CliRunner, mock_detection_summary: DetectionSummary
    ) -> None:
        """Test that configuration is generated and saved correctly."""
        with patch(
            "mycelium_onboarding.wizard.persistence.WizardStatePersistence"
        ) as mock_persistence_class:
            # Setup mock persistence
            mock_persistence = MagicMock()
            mock_persistence.exists.return_value = False
            mock_persistence_class.return_value = mock_persistence

            # Setup mock screens
            with patch("mycelium_onboarding.wizard.screens.WizardScreens") as mock_screens:
                screens = mock_screens.return_value
                screens.show_welcome.return_value = "quick"
                screens.show_detection.return_value = mock_detection_summary
                screens.show_services.return_value = {
                    "redis": True,
                    "postgres": True,
                    "temporal": False,
                }
                screens.show_deployment.return_value = "docker-compose"
                screens.show_review.return_value = "confirm"

                # Setup mock validator
                with patch("mycelium_onboarding.wizard.validation.WizardValidator") as mock_validator:
                    validator = mock_validator.return_value
                    validator.validate_state.return_value = True

                    # Setup mock config manager
                    with patch("mycelium_onboarding.config.manager.ConfigManager") as mock_manager:
                        manager = mock_manager.return_value
                        manager._determine_save_path.return_value = Path("/tmp/config.yaml")

                        # Run command
                        result = runner.invoke(
                            cli, ["init", "--no-resume"], input="test-project\n"
                        )

                        # Verify wizard completed successfully
                        assert result.exit_code == 0, f"Wizard failed: {result.output}"

    def test_init_corrupted_state_handling(self, runner: CliRunner) -> None:
        """Test handling of corrupted saved state."""
        with patch(
            "mycelium_onboarding.wizard.persistence.WizardStatePersistence"
        ) as mock_persistence_class:
            # Setup mock persistence that returns None (corrupted state)
            mock_persistence = MagicMock()
            mock_persistence.exists.return_value = True
            mock_persistence.load.return_value = None  # Corrupted
            mock_persistence_class.return_value = mock_persistence

            # Setup mock screens to exit quickly
            with patch("mycelium_onboarding.wizard.screens.WizardScreens") as mock_screens:
                mock_screens.return_value.show_welcome.side_effect = SystemExit(0)

                # Run command with resume
                result = runner.invoke(cli, ["init"], input="y\n")

                # Verify load was attempted
                assert mock_persistence.load.called

    def test_init_error_handling_with_state_save(self, runner: CliRunner) -> None:
        """Test that state is saved when an unexpected error occurs."""
        with patch(
            "mycelium_onboarding.wizard.persistence.WizardStatePersistence"
        ) as mock_persistence_class:
            # Setup mock persistence
            mock_persistence = MagicMock()
            mock_persistence.exists.return_value = False
            mock_persistence_class.return_value = mock_persistence

            # Setup mock screens to raise exception
            with patch("mycelium_onboarding.wizard.screens.WizardScreens") as mock_screens:
                mock_screens.return_value.show_welcome.side_effect = RuntimeError(
                    "Test error"
                )

                # Run command
                result = runner.invoke(cli, ["init"])

                # Verify state was saved before re-raising error
                assert mock_persistence.save.called
                assert result.exit_code != 0


class TestInitCommandSimple:
    """Simple tests for init command basics."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Provide Click test runner with clean environment."""
        # Create runner with isolated environment (no MYCELIUM_* vars)
        return CliRunner(env={
            k: v for k, v in __import__('os').environ.items()
            if not k.startswith('MYCELIUM_')
        })

    def test_init_command_exists(self, runner: CliRunner) -> None:
        """Test that init command is registered."""
        result = runner.invoke(cli, ["--help"])
        assert "init" in result.output

    def test_init_has_resume_options(self, runner: CliRunner) -> None:
        """Test that init command has resume options."""
        result = runner.invoke(cli, ["init", "--help"])
        assert "--resume" in result.output or "--no-resume" in result.output
        assert "--reset" in result.output
