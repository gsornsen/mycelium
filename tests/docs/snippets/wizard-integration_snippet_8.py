# Source: wizard-integration.md
# Line: 523
# Valid syntax: True
# Has imports: True
# Has assignments: True

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from mycelium_onboarding.cli import cli


def test_wizard_quick_mode_e2e(tmp_path: Path):
    """End-to-end test for quick mode wizard."""
    runner = CliRunner()

    with patch("mycelium_onboarding.wizard.persistence.WizardStatePersistence") as mock_pers:
        # Setup persistence mock
        mock_persistence = MagicMock()
        mock_persistence.exists.return_value = False
        mock_pers.return_value = mock_persistence

        # Mock all prompts
        with patch("mycelium_onboarding.wizard.screens.inquirer") as mock_inquirer:
            mock_inquirer.select.side_effect = [
                MagicMock(execute=lambda: "quick"),  # Setup mode
                MagicMock(execute=lambda: "docker-compose"),  # Deployment
                MagicMock(execute=lambda: "confirm"),  # Review
            ]

            mock_inquirer.confirm.side_effect = [
                MagicMock(execute=lambda: False),  # Don't re-run detection
                MagicMock(execute=lambda: True),  # Auto-start
            ]

            mock_inquirer.checkbox.return_value = MagicMock(
                execute=lambda: ["redis", "postgres"]
            )

            mock_inquirer.text.return_value = MagicMock(
                execute=lambda: "test_db"
            )

            # Mock detection
            with patch("mycelium_onboarding.wizard.screens.detect_all") as mock_detect:
                mock_detect.return_value = Mock()

                # Mock config manager
                with patch("mycelium_onboarding.config.manager.ConfigManager") as mock_cfg:
                    mock_config = MagicMock()
                    mock_config._determine_save_path.return_value = tmp_path / "config.yaml"
                    mock_cfg.return_value = mock_config

                    # Mock project name prompt
                    with patch("click.prompt", return_value="test-project"):
                        # Execute wizard
                        result = runner.invoke(cli, ["init", "--no-resume"])

                    # Verify
                    assert result.exit_code == 0
                    mock_config.save.assert_called_once()
