"""Tests for direnv setup functionality.

This module tests direnv detection, installation verification, shell hook detection,
and .envrc template copying.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import mycelium_onboarding.setup_direnv as direnv_module
from mycelium_onboarding.setup_direnv import (
    DirenvError,
    check_direnv_hook_installed,
    check_direnv_installed,
    copy_envrc_template,
    detect_shell,
    get_direnv_version,
    get_hook_install_instructions,
    get_shell_config_path,
    setup_direnv,
)


class TestDirenvDetection:
    """Tests for direnv installation detection."""

    def test_check_direnv_installed_when_available(self) -> None:
        """Test direnv detection when direnv is installed."""
        with patch("shutil.which", return_value="/usr/bin/direnv"):
            assert check_direnv_installed() is True

    def test_check_direnv_installed_when_not_available(self) -> None:
        """Test direnv detection when direnv is not installed."""
        with patch("shutil.which", return_value=None):
            assert check_direnv_installed() is False

    def test_get_direnv_version_when_installed(self) -> None:
        """Test getting direnv version when installed."""
        mock_result = MagicMock()
        mock_result.stdout = "2.32.1\n"
        mock_result.returncode = 0

        with (
            patch("shutil.which", return_value="/usr/bin/direnv"),
            patch("subprocess.run", return_value=mock_result),
        ):
            version = get_direnv_version()
            assert version == "2.32.1"

    def test_get_direnv_version_when_not_installed(self) -> None:
        """Test getting direnv version when not installed."""
        with patch("shutil.which", return_value=None):
            assert get_direnv_version() is None

    def test_get_direnv_version_command_fails(self) -> None:
        """Test version detection when direnv command fails."""
        with (
            patch("shutil.which", return_value="/usr/bin/direnv"),
            patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(1, "direnv"),
            ),
        ):
            version = get_direnv_version()
            assert version is None


class TestShellDetection:
    """Tests for shell detection and configuration."""

    def test_detect_shell_bash(self) -> None:
        """Test shell detection for bash."""
        with patch.dict("os.environ", {"SHELL": "/bin/bash"}):
            assert detect_shell() == "bash"

    def test_detect_shell_zsh(self) -> None:
        """Test shell detection for zsh."""
        with patch.dict("os.environ", {"SHELL": "/usr/bin/zsh"}):
            assert detect_shell() == "zsh"

    def test_detect_shell_fish(self) -> None:
        """Test shell detection for fish."""
        with patch.dict("os.environ", {"SHELL": "/usr/local/bin/fish"}):
            assert detect_shell() == "fish"

    def test_detect_shell_unknown(self) -> None:
        """Test shell detection for unknown shell."""
        with patch.dict("os.environ", {"SHELL": "/bin/dash"}):
            assert detect_shell() is None

    def test_detect_shell_not_set(self) -> None:
        """Test shell detection when SHELL not set."""
        with patch.dict("os.environ", {}, clear=True):
            assert detect_shell() is None

    def test_get_shell_config_path_bash_existing(self, tmp_path: Path) -> None:
        """Test getting bash config path when .bashrc exists."""
        bashrc = tmp_path / ".bashrc"
        bashrc.touch()

        with patch("pathlib.Path.home", return_value=tmp_path):
            config_path = get_shell_config_path("bash")
            assert config_path == bashrc

    def test_get_shell_config_path_bash_fallback(self, tmp_path: Path) -> None:
        """Test getting bash config path fallback when none exist."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            config_path = get_shell_config_path("bash")
            assert config_path == tmp_path / ".bashrc"

    def test_get_shell_config_path_unknown_shell(self) -> None:
        """Test getting config path for unknown shell."""
        assert get_shell_config_path("unknown") is None


class TestHookDetection:
    """Tests for direnv hook detection in shell configs."""

    def test_check_hook_installed_bash_present(self, tmp_path: Path) -> None:
        """Test hook detection when hook is present in bash config."""
        bashrc = tmp_path / ".bashrc"
        bashrc.write_text('eval "$(direnv hook bash)"\n')

        with (
            patch.dict("os.environ", {"SHELL": "/bin/bash"}),
            patch("pathlib.Path.home", return_value=tmp_path),
        ):
            installed, message = check_direnv_hook_installed("bash")
            assert installed is True
            assert "installed" in message.lower()

    def test_check_hook_installed_bash_missing(self, tmp_path: Path) -> None:
        """Test hook detection when hook is missing from bash config."""
        bashrc = tmp_path / ".bashrc"
        bashrc.write_text("# Empty config\n")

        with (
            patch.dict("os.environ", {"SHELL": "/bin/bash"}),
            patch("pathlib.Path.home", return_value=tmp_path),
        ):
            installed, message = check_direnv_hook_installed("bash")
            assert installed is False
            assert "not found" in message.lower()

    def test_check_hook_installed_zsh_present(self, tmp_path: Path) -> None:
        """Test hook detection when hook is present in zsh config."""
        zshrc = tmp_path / ".zshrc"
        zshrc.write_text('eval "$(direnv hook zsh)"\n')

        with (
            patch.dict("os.environ", {"SHELL": "/usr/bin/zsh"}),
            patch("pathlib.Path.home", return_value=tmp_path),
        ):
            installed, message = check_direnv_hook_installed("zsh")
            assert installed is True

    def test_check_hook_installed_config_missing(self, tmp_path: Path) -> None:
        """Test hook detection when config file doesn't exist."""
        with (
            patch.dict("os.environ", {"SHELL": "/bin/bash"}),
            patch("pathlib.Path.home", return_value=tmp_path),
        ):
            installed, message = check_direnv_hook_installed("bash")
            assert installed is False
            assert "not found" in message.lower()

    def test_check_hook_installed_shell_not_detected(self) -> None:
        """Test hook detection when shell cannot be detected."""
        with patch.dict("os.environ", {}, clear=True):
            installed, message = check_direnv_hook_installed()
            assert installed is False
            assert "could not detect" in message.lower()

    def test_get_hook_install_instructions_bash(self, tmp_path: Path) -> None:
        """Test getting installation instructions for bash."""
        with (
            patch.dict("os.environ", {"SHELL": "/bin/bash"}),
            patch("pathlib.Path.home", return_value=tmp_path),
        ):
            instructions = get_hook_install_instructions("bash")
            assert "bashrc" in instructions.lower()
            assert 'eval "$(direnv hook bash)"' in instructions

    def test_get_hook_install_instructions_unknown_shell(self) -> None:
        """Test getting installation instructions when shell is unknown."""
        with patch.dict("os.environ", {}, clear=True):
            instructions = get_hook_install_instructions()
            assert "could not detect" in instructions.lower()
            assert "direnv.net" in instructions


class TestEnvrcTemplate:
    """Tests for .envrc template copying."""

    def test_copy_envrc_template_success(self, tmp_path: Path) -> None:
        """Test successful template copying."""
        # Create a template file
        template = tmp_path / ".envrc.template"
        template.write_text("# Test template\nexport TEST=1\n")

        # Copy to .envrc
        success, message = copy_envrc_template(tmp_path)

        assert success is True
        assert "created" in message.lower()
        assert (tmp_path / ".envrc").exists()
        assert (tmp_path / ".envrc").read_text() == template.read_text()

    def test_copy_envrc_template_already_exists(self, tmp_path: Path) -> None:
        """Test template copying when .envrc already exists."""
        # Create existing .envrc
        existing = tmp_path / ".envrc"
        existing.write_text("# Existing\n")

        # Try to copy template
        success, message = copy_envrc_template(tmp_path)

        assert success is False
        assert "already exists" in message.lower()

    def test_copy_envrc_template_not_found_no_fallback(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test template copying when template doesn't exist and no fallback."""
        # Mock __file__ attribute on the module itself
        fake_module_path = tmp_path / "fake_module" / "setup_direnv.py"
        fake_module_path.parent.mkdir(parents=True)

        with (
            pytest.raises(DirenvError) as exc_info,
            patch.object(direnv_module, "__file__", str(fake_module_path)),
        ):
            copy_envrc_template(tmp_path)

        assert "not found" in str(exc_info.value).lower()

    def test_copy_envrc_template_uses_mycelium_root(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that copy uses MYCELIUM_ROOT environment variable."""
        template = tmp_path / ".envrc.template"
        template.write_text("# Template\n")

        monkeypatch.setenv("MYCELIUM_ROOT", str(tmp_path))

        success, message = copy_envrc_template()
        assert success is True

    def test_copy_envrc_template_uses_package_template(self, tmp_path: Path) -> None:
        """Test fallback to package template directory."""
        # This test verifies the real package template is used
        target_dir = tmp_path / "project"
        target_dir.mkdir()

        # Should find the actual package template
        success, message = copy_envrc_template(target_dir)
        assert success is True
        assert (target_dir / ".envrc").exists()

        # Verify it contains expected Mycelium content
        content = (target_dir / ".envrc").read_text()
        assert "MYCELIUM_ROOT" in content
        assert "MYCELIUM_ENV_ACTIVE" in content


class TestSetupDirenv:
    """Tests for main setup_direnv function."""

    def test_setup_direnv_not_installed(self) -> None:
        """Test setup when direnv is not installed."""
        with patch("shutil.which", return_value=None):
            success, message = setup_direnv()

            assert success is False
            assert "not installed" in message.lower()
            assert "https://direnv.net" in message

    def test_setup_direnv_hook_not_installed(self, tmp_path: Path) -> None:
        """Test setup when direnv installed but hook not configured."""
        bashrc = tmp_path / ".bashrc"
        bashrc.write_text("# No hook\n")

        with (
            patch("shutil.which", return_value="/usr/bin/direnv"),
            patch.dict("os.environ", {"SHELL": "/bin/bash"}),
            patch("pathlib.Path.home", return_value=tmp_path),
        ):
            success, message = setup_direnv()

            assert success is False
            assert "hook" in message.lower()
            assert "not configured" in message.lower()

    def test_setup_direnv_success_new_envrc(self, tmp_path: Path) -> None:
        """Test successful setup with new .envrc creation."""
        # Setup shell config with hook
        bashrc = tmp_path / ".bashrc"
        bashrc.write_text('eval "$(direnv hook bash)"\n')

        # Create template
        template = tmp_path / ".envrc.template"
        template.write_text("# Template\n")

        with (
            patch("shutil.which", return_value="/usr/bin/direnv"),
            patch.dict("os.environ", {"SHELL": "/bin/bash"}),
            patch("pathlib.Path.home", return_value=tmp_path),
        ):
            success, message = setup_direnv(tmp_path)

            assert success is True
            assert "complete" in message.lower()
            assert "direnv allow" in message

    def test_setup_direnv_success_existing_envrc(self, tmp_path: Path) -> None:
        """Test successful setup when .envrc already exists."""
        # Setup shell config with hook
        bashrc = tmp_path / ".bashrc"
        bashrc.write_text('eval "$(direnv hook bash)"\n')

        # Create existing .envrc
        envrc = tmp_path / ".envrc"
        envrc.write_text("# Existing\n")

        with (
            patch("shutil.which", return_value="/usr/bin/direnv"),
            patch.dict("os.environ", {"SHELL": "/bin/bash"}),
            patch("pathlib.Path.home", return_value=tmp_path),
        ):
            success, message = setup_direnv(tmp_path)

            assert success is True
            assert "already exists" in message.lower()


class TestIntegration:
    """Integration tests for the complete direnv setup workflow."""

    def test_full_setup_workflow(self, tmp_path: Path) -> None:
        """Test complete setup workflow from start to finish."""
        # Create shell config with hook
        bashrc = tmp_path / ".bashrc"
        bashrc.write_text('eval "$(direnv hook bash)"\n')

        # Create template
        template = tmp_path / ".envrc.template"
        template_content = """# Mycelium Environment
export MYCELIUM_ROOT="$PWD"
export MYCELIUM_ENV_ACTIVE=1
"""
        template.write_text(template_content)

        # Create pyproject.toml to pass validation
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\n')

        with (
            patch("shutil.which", return_value="/usr/bin/direnv"),
            patch.dict("os.environ", {"SHELL": "/bin/bash"}),
            patch("pathlib.Path.home", return_value=tmp_path),
        ):
            # Run setup
            success, message = setup_direnv(tmp_path)

            # Verify results
            assert success is True
            assert (tmp_path / ".envrc").exists()

            envrc_content = (tmp_path / ".envrc").read_text()
            assert "MYCELIUM_ROOT" in envrc_content
            assert "MYCELIUM_ENV_ACTIVE" in envrc_content
