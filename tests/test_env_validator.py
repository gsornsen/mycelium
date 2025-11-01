"""Tests for runtime environment validation.

This test suite provides comprehensive coverage of the environment validator,
including validation logic, error messages, and edge cases.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from mycelium_onboarding.env_validator import (
    EnvironmentValidationError,
    get_environment_info,
    get_missing_vars,
    is_environment_active,
    validate_environment,
)


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear all Mycelium environment variables."""
    env_vars = [
        "MYCELIUM_ROOT",
        "MYCELIUM_CONFIG_DIR",
        "MYCELIUM_DATA_DIR",
        "MYCELIUM_CACHE_DIR",
        "MYCELIUM_STATE_DIR",
        "MYCELIUM_PROJECT_DIR",
        "MYCELIUM_ENV_ACTIVE",
    ]

    for var in env_vars:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def mock_mycelium_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """Create a complete mock Mycelium environment.

    Returns:
        Dictionary mapping environment variable names to their paths
    """
    # Create project root with required files
    project_root = tmp_path / "mycelium"
    project_root.mkdir()

    # Create .git directory to simulate git repository
    (project_root / ".git").mkdir()

    # Create pyproject.toml to simulate Python project
    (project_root / "pyproject.toml").write_text("[project]\nname = 'mycelium'\n")

    # Create XDG directories
    config_dir = tmp_path / "config" / "mycelium"
    config_dir.mkdir(parents=True)

    data_dir = tmp_path / "data" / "mycelium"
    data_dir.mkdir(parents=True)

    cache_dir = tmp_path / "cache" / "mycelium"
    cache_dir.mkdir(parents=True)

    state_dir = tmp_path / "state" / "mycelium"
    state_dir.mkdir(parents=True)

    project_dir = project_root / ".mycelium"
    project_dir.mkdir()

    # Set environment variables
    env_vars = {
        "MYCELIUM_ROOT": project_root,
        "MYCELIUM_CONFIG_DIR": config_dir,
        "MYCELIUM_DATA_DIR": data_dir,
        "MYCELIUM_CACHE_DIR": cache_dir,
        "MYCELIUM_STATE_DIR": state_dir,
        "MYCELIUM_PROJECT_DIR": project_dir,
        "MYCELIUM_ENV_ACTIVE": "1",
    }

    for var, path in env_vars.items():
        if var == "MYCELIUM_ENV_ACTIVE":
            monkeypatch.setenv(var, str(path))
        else:
            monkeypatch.setenv(var, str(path))

    return env_vars


class TestIsEnvironmentActive:
    """Tests for is_environment_active()."""

    def test_returns_true_when_active(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return True when MYCELIUM_ENV_ACTIVE is '1'."""
        monkeypatch.setenv("MYCELIUM_ENV_ACTIVE", "1")
        assert is_environment_active() is True

    def test_returns_false_when_not_set(self, clean_env: None) -> None:
        """Should return False when MYCELIUM_ENV_ACTIVE is not set."""
        assert is_environment_active() is False

    def test_returns_false_when_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return False when MYCELIUM_ENV_ACTIVE is '0'."""
        monkeypatch.setenv("MYCELIUM_ENV_ACTIVE", "0")
        assert is_environment_active() is False

    def test_returns_false_when_empty_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return False when MYCELIUM_ENV_ACTIVE is empty."""
        monkeypatch.setenv("MYCELIUM_ENV_ACTIVE", "")
        assert is_environment_active() is False


class TestGetMissingVars:
    """Tests for get_missing_vars()."""

    def test_returns_empty_when_all_required_set(self, mock_mycelium_env: dict[str, Path]) -> None:
        """Should return empty list when all required vars are set."""
        missing = get_missing_vars()
        assert missing == []

    def test_returns_missing_required_vars(self, clean_env: None) -> None:
        """Should return list of missing required variables."""
        missing = get_missing_vars()

        expected = [
            "MYCELIUM_ROOT",
            "MYCELIUM_CONFIG_DIR",
            "MYCELIUM_DATA_DIR",
            "MYCELIUM_CACHE_DIR",
            "MYCELIUM_STATE_DIR",
        ]

        assert set(missing) == set(expected)

    def test_returns_some_missing_vars(self, clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return only the missing variables."""
        monkeypatch.setenv("MYCELIUM_ROOT", "/tmp/mycelium")
        monkeypatch.setenv("MYCELIUM_CONFIG_DIR", "/tmp/config")

        missing = get_missing_vars()

        expected = [
            "MYCELIUM_DATA_DIR",
            "MYCELIUM_CACHE_DIR",
            "MYCELIUM_STATE_DIR",
        ]

        assert set(missing) == set(expected)

    def test_excludes_optional_by_default(self, clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should not check optional vars by default."""
        # Set all required vars
        monkeypatch.setenv("MYCELIUM_ROOT", "/tmp/mycelium")
        monkeypatch.setenv("MYCELIUM_CONFIG_DIR", "/tmp/config")
        monkeypatch.setenv("MYCELIUM_DATA_DIR", "/tmp/data")
        monkeypatch.setenv("MYCELIUM_CACHE_DIR", "/tmp/cache")
        monkeypatch.setenv("MYCELIUM_STATE_DIR", "/tmp/state")
        # Don't set optional vars

        missing = get_missing_vars(include_optional=False)
        assert missing == []

    def test_includes_optional_when_requested(self, clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should check optional vars when include_optional=True."""
        # Set all required vars
        monkeypatch.setenv("MYCELIUM_ROOT", "/tmp/mycelium")
        monkeypatch.setenv("MYCELIUM_CONFIG_DIR", "/tmp/config")
        monkeypatch.setenv("MYCELIUM_DATA_DIR", "/tmp/data")
        monkeypatch.setenv("MYCELIUM_CACHE_DIR", "/tmp/cache")
        monkeypatch.setenv("MYCELIUM_STATE_DIR", "/tmp/state")
        # Don't set optional vars

        missing = get_missing_vars(include_optional=True)
        expected = ["MYCELIUM_PROJECT_DIR", "MYCELIUM_ENV_ACTIVE"]
        assert set(missing) == set(expected)


class TestGetEnvironmentInfo:
    """Tests for get_environment_info()."""

    def test_returns_all_vars_when_set(self, mock_mycelium_env: dict[str, Path]) -> None:
        """Should return dict with all environment variables."""
        info = get_environment_info()

        assert "MYCELIUM_ROOT" in info
        assert "MYCELIUM_CONFIG_DIR" in info
        assert "MYCELIUM_DATA_DIR" in info
        assert "MYCELIUM_CACHE_DIR" in info
        assert "MYCELIUM_STATE_DIR" in info
        assert "MYCELIUM_PROJECT_DIR" in info
        assert "MYCELIUM_ENV_ACTIVE" in info

        # All should have values
        assert all(value is not None for value in info.values())

    def test_returns_none_for_unset_vars(self, clean_env: None) -> None:
        """Should return None for unset variables."""
        info = get_environment_info()

        assert all(value is None for value in info.values())

    def test_returns_partial_info(self, clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return mix of set and unset variables."""
        monkeypatch.setenv("MYCELIUM_ROOT", "/tmp/mycelium")
        monkeypatch.setenv("MYCELIUM_ENV_ACTIVE", "1")

        info = get_environment_info()

        assert info["MYCELIUM_ROOT"] == "/tmp/mycelium"
        assert info["MYCELIUM_ENV_ACTIVE"] == "1"
        assert info["MYCELIUM_CONFIG_DIR"] is None
        assert info["MYCELIUM_DATA_DIR"] is None


class TestValidateEnvironment:
    """Tests for validate_environment()."""

    def test_passes_with_valid_environment(self, mock_mycelium_env: dict[str, Path]) -> None:
        """Should not raise exception with valid environment."""
        # Should not raise
        validate_environment()

    def test_fails_with_missing_variables(self, clean_env: None) -> None:
        """Should raise EnvironmentValidationError when vars missing."""
        with pytest.raises(EnvironmentValidationError) as exc_info:
            validate_environment()

        error_msg = str(exc_info.value)
        assert "Missing or empty environment variables" in error_msg
        assert "MYCELIUM_ROOT" in error_msg
        assert "direnv allow" in error_msg
        assert "source bin/activate.sh" in error_msg

    def test_fails_with_some_missing_variables(self, clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should raise error with specific missing variables."""
        monkeypatch.setenv("MYCELIUM_ROOT", "/tmp/mycelium")
        monkeypatch.setenv("MYCELIUM_CONFIG_DIR", "/tmp/config")
        # Missing other vars

        with pytest.raises(EnvironmentValidationError) as exc_info:
            validate_environment()

        error_msg = str(exc_info.value)
        assert "MYCELIUM_DATA_DIR" in error_msg
        assert "MYCELIUM_CACHE_DIR" in error_msg
        assert "MYCELIUM_STATE_DIR" in error_msg

    def test_fails_with_missing_directory(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should raise error when a directory doesn't exist."""
        # Create project root
        project_root = tmp_path / "mycelium"
        project_root.mkdir()
        (project_root / ".git").mkdir()
        (project_root / "pyproject.toml").write_text("[project]\nname='test'\n")

        # Set all vars but don't create all directories
        monkeypatch.setenv("MYCELIUM_ROOT", str(project_root))
        monkeypatch.setenv("MYCELIUM_CONFIG_DIR", str(tmp_path / "config"))
        monkeypatch.setenv("MYCELIUM_DATA_DIR", str(tmp_path / "data"))
        monkeypatch.setenv("MYCELIUM_CACHE_DIR", str(tmp_path / "cache"))
        monkeypatch.setenv("MYCELIUM_STATE_DIR", str(tmp_path / "state"))

        # Only create some directories
        (tmp_path / "config").mkdir()
        # Don't create data, cache, state

        with pytest.raises(EnvironmentValidationError) as exc_info:
            validate_environment()

        error_msg = str(exc_info.value)
        assert "do not exist" in error_msg
        assert "MYCELIUM_DATA_DIR" in error_msg

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_fails_with_unwritable_directory(
        self, mock_mycelium_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should raise error when directory is not writable."""
        # Make config directory read-only
        config_dir = mock_mycelium_env["MYCELIUM_CONFIG_DIR"]
        config_dir.chmod(0o444)  # r--r--r--

        try:
            with pytest.raises(EnvironmentValidationError) as exc_info:
                validate_environment()

            error_msg = str(exc_info.value)
            assert "not writable" in error_msg
            assert str(config_dir) in error_msg
        finally:
            # Restore permissions for cleanup
            config_dir.chmod(0o755)

    def test_fails_without_git_directory(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should raise error when MYCELIUM_ROOT is not a git repo."""
        # Create project root without .git
        project_root = tmp_path / "mycelium"
        project_root.mkdir()
        (project_root / "pyproject.toml").write_text("[project]\nname='test'\n")

        # Create all other directories
        for name in ["config", "data", "cache", "state"]:
            (tmp_path / name).mkdir()

        # Set environment
        monkeypatch.setenv("MYCELIUM_ROOT", str(project_root))
        monkeypatch.setenv("MYCELIUM_CONFIG_DIR", str(tmp_path / "config"))
        monkeypatch.setenv("MYCELIUM_DATA_DIR", str(tmp_path / "data"))
        monkeypatch.setenv("MYCELIUM_CACHE_DIR", str(tmp_path / "cache"))
        monkeypatch.setenv("MYCELIUM_STATE_DIR", str(tmp_path / "state"))

        with pytest.raises(EnvironmentValidationError) as exc_info:
            validate_environment()

        error_msg = str(exc_info.value)
        assert "not a git repository" in error_msg
        assert str(project_root) in error_msg

    def test_fails_without_pyproject_toml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should raise error when pyproject.toml is missing."""
        # Create project root with .git but no pyproject.toml
        project_root = tmp_path / "mycelium"
        project_root.mkdir()
        (project_root / ".git").mkdir()

        # Create all other directories
        for name in ["config", "data", "cache", "state"]:
            (tmp_path / name).mkdir()

        # Set environment
        monkeypatch.setenv("MYCELIUM_ROOT", str(project_root))
        monkeypatch.setenv("MYCELIUM_CONFIG_DIR", str(tmp_path / "config"))
        monkeypatch.setenv("MYCELIUM_DATA_DIR", str(tmp_path / "data"))
        monkeypatch.setenv("MYCELIUM_CACHE_DIR", str(tmp_path / "cache"))
        monkeypatch.setenv("MYCELIUM_STATE_DIR", str(tmp_path / "state"))

        with pytest.raises(EnvironmentValidationError) as exc_info:
            validate_environment()

        error_msg = str(exc_info.value)
        assert "does not contain pyproject.toml" in error_msg
        assert str(project_root) in error_msg

    def test_project_dir_optional_by_default(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should not require MYCELIUM_PROJECT_DIR by default."""
        # Create valid environment without project dir
        project_root = tmp_path / "mycelium"
        project_root.mkdir()
        (project_root / ".git").mkdir()
        (project_root / "pyproject.toml").write_text("[project]\nname='test'\n")

        # Create all required directories
        for name in ["config", "data", "cache", "state"]:
            (tmp_path / name).mkdir()

        # Set all required vars except project dir
        monkeypatch.setenv("MYCELIUM_ROOT", str(project_root))
        monkeypatch.setenv("MYCELIUM_CONFIG_DIR", str(tmp_path / "config"))
        monkeypatch.setenv("MYCELIUM_DATA_DIR", str(tmp_path / "data"))
        monkeypatch.setenv("MYCELIUM_CACHE_DIR", str(tmp_path / "cache"))
        monkeypatch.setenv("MYCELIUM_STATE_DIR", str(tmp_path / "state"))

        # Should not raise
        validate_environment(require_project_dir=False)

    def test_requires_project_dir_when_requested(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should require MYCELIUM_PROJECT_DIR when requested."""
        # Create valid environment without project dir
        project_root = tmp_path / "mycelium"
        project_root.mkdir()
        (project_root / ".git").mkdir()
        (project_root / "pyproject.toml").write_text("[project]\nname='test'\n")

        # Create all required directories
        for name in ["config", "data", "cache", "state"]:
            (tmp_path / name).mkdir()

        # Ensure MYCELIUM_PROJECT_DIR is not set (in case environment already has it)
        monkeypatch.delenv("MYCELIUM_PROJECT_DIR", raising=False)

        # Set all required vars except project dir
        monkeypatch.setenv("MYCELIUM_ROOT", str(project_root))
        monkeypatch.setenv("MYCELIUM_CONFIG_DIR", str(tmp_path / "config"))
        monkeypatch.setenv("MYCELIUM_DATA_DIR", str(tmp_path / "data"))
        monkeypatch.setenv("MYCELIUM_CACHE_DIR", str(tmp_path / "cache"))
        monkeypatch.setenv("MYCELIUM_STATE_DIR", str(tmp_path / "state"))

        with pytest.raises(EnvironmentValidationError) as exc_info:
            validate_environment(require_project_dir=True)

        error_msg = str(exc_info.value)
        assert "MYCELIUM_PROJECT_DIR" in error_msg

    def test_validates_project_dir_when_set(self, mock_mycelium_env: dict[str, Path]) -> None:
        """Should validate project dir when required and set."""
        # Should not raise - project dir is set and exists
        validate_environment(require_project_dir=True)


class TestErrorMessages:
    """Tests for error message quality and actionability."""

    def test_missing_vars_error_includes_fix_instructions(self, clean_env: None) -> None:
        """Error should include how to activate environment."""
        with pytest.raises(EnvironmentValidationError) as exc_info:
            validate_environment()

        error_msg = str(exc_info.value)
        assert "direnv allow" in error_msg
        assert "source bin/activate.sh" in error_msg

    def test_missing_dirs_error_includes_fix_instructions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Error should include how to fix missing directories."""
        project_root = tmp_path / "mycelium"
        project_root.mkdir()
        (project_root / ".git").mkdir()
        (project_root / "pyproject.toml").write_text("[project]\nname='test'\n")

        monkeypatch.setenv("MYCELIUM_ROOT", str(project_root))
        monkeypatch.setenv("MYCELIUM_CONFIG_DIR", str(tmp_path / "config"))
        monkeypatch.setenv("MYCELIUM_DATA_DIR", str(tmp_path / "data"))
        monkeypatch.setenv("MYCELIUM_CACHE_DIR", str(tmp_path / "cache"))
        monkeypatch.setenv("MYCELIUM_STATE_DIR", str(tmp_path / "state"))

        with pytest.raises(EnvironmentValidationError) as exc_info:
            validate_environment()

        error_msg = str(exc_info.value)
        assert "Re-activate" in error_msg or "activate" in error_msg.lower()

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_unwritable_dir_error_includes_chmod_command(self, mock_mycelium_env: dict[str, Path]) -> None:
        """Error should include chmod command for fixing permissions."""
        config_dir = mock_mycelium_env["MYCELIUM_CONFIG_DIR"]
        config_dir.chmod(0o444)

        try:
            with pytest.raises(EnvironmentValidationError) as exc_info:
                validate_environment()

            error_msg = str(exc_info.value)
            assert "chmod" in error_msg
            assert "permissions" in error_msg.lower()
        finally:
            config_dir.chmod(0o755)

    def test_git_error_includes_project_directory_guidance(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Error should guide user to correct project directory."""
        project_root = tmp_path / "mycelium"
        project_root.mkdir()
        (project_root / "pyproject.toml").write_text("[project]\nname='test'\n")

        for name in ["config", "data", "cache", "state"]:
            (tmp_path / name).mkdir()

        monkeypatch.setenv("MYCELIUM_ROOT", str(project_root))
        monkeypatch.setenv("MYCELIUM_CONFIG_DIR", str(tmp_path / "config"))
        monkeypatch.setenv("MYCELIUM_DATA_DIR", str(tmp_path / "data"))
        monkeypatch.setenv("MYCELIUM_CACHE_DIR", str(tmp_path / "cache"))
        monkeypatch.setenv("MYCELIUM_STATE_DIR", str(tmp_path / "state"))

        with pytest.raises(EnvironmentValidationError) as exc_info:
            validate_environment()

        error_msg = str(exc_info.value)
        assert "directory" in error_msg.lower()
        assert str(project_root) in error_msg


class TestEdgeCases:
    """Tests for edge cases and unusual scenarios."""

    def test_handles_relative_paths_in_env_vars(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should handle relative paths correctly."""
        # Change to tmp directory

        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)

            # Create structure with relative path reference
            project_root = tmp_path / "mycelium"
            project_root.mkdir()
            (project_root / ".git").mkdir()
            (project_root / "pyproject.toml").write_text("[project]\nname='test'\n")

            # Set MYCELIUM_ROOT as relative path
            monkeypatch.setenv("MYCELIUM_ROOT", "mycelium")
            monkeypatch.setenv("MYCELIUM_CONFIG_DIR", str(tmp_path / "config"))
            monkeypatch.setenv("MYCELIUM_DATA_DIR", str(tmp_path / "data"))
            monkeypatch.setenv("MYCELIUM_CACHE_DIR", str(tmp_path / "cache"))
            monkeypatch.setenv("MYCELIUM_STATE_DIR", str(tmp_path / "state"))

            for name in ["config", "data", "cache", "state"]:
                (tmp_path / name).mkdir()

            # Should not raise - pathlib handles relative paths
            validate_environment()
        finally:
            os.chdir(original_cwd)

    def test_handles_symlinks(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should handle symlinked directories correctly."""
        # Create real directory
        real_dir = tmp_path / "real_mycelium"
        real_dir.mkdir()
        (real_dir / ".git").mkdir()
        (real_dir / "pyproject.toml").write_text("[project]\nname='test'\n")

        # Create symlink
        symlink_dir = tmp_path / "mycelium_link"
        symlink_dir.symlink_to(real_dir)

        # Create other directories
        for name in ["config", "data", "cache", "state"]:
            (tmp_path / name).mkdir()

        # Use symlink path
        monkeypatch.setenv("MYCELIUM_ROOT", str(symlink_dir))
        monkeypatch.setenv("MYCELIUM_CONFIG_DIR", str(tmp_path / "config"))
        monkeypatch.setenv("MYCELIUM_DATA_DIR", str(tmp_path / "data"))
        monkeypatch.setenv("MYCELIUM_CACHE_DIR", str(tmp_path / "cache"))
        monkeypatch.setenv("MYCELIUM_STATE_DIR", str(tmp_path / "state"))

        # Should work with symlinks
        validate_environment()

    def test_empty_string_env_var_treated_as_missing(self, clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
        """Empty string should be treated as missing variable."""
        monkeypatch.setenv("MYCELIUM_ROOT", "")
        monkeypatch.setenv("MYCELIUM_CONFIG_DIR", "")
        monkeypatch.setenv("MYCELIUM_DATA_DIR", "")
        monkeypatch.setenv("MYCELIUM_CACHE_DIR", "")
        monkeypatch.setenv("MYCELIUM_STATE_DIR", "")

        # Empty strings are falsy in Python, but os.environ still has them
        # So this will try to create Path("") which will fail
        with pytest.raises(EnvironmentValidationError):
            validate_environment()
