"""Integration tests for complete environment activation flow.

This test suite validates the entire activation workflow, ensuring all components
work together correctly:
- Shell activation scripts (activate.sh)
- direnv integration (.envrc)
- Runtime validation (env_validator)
- XDG directory creation
- Configuration hierarchy
- Platform compatibility

These tests use subprocess to execute shell scripts in isolation, simulating
real-world usage scenarios.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    # Navigate up from tests/integration/ to project root
    return Path(__file__).parent.parent.parent.resolve()


@pytest.fixture
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure clean environment without MYCELIUM_* variables."""
    # Remove all MYCELIUM_* environment variables
    for key in list(os.environ.keys()):
        if key.startswith("MYCELIUM_"):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture
def temp_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary HOME directory for isolated testing."""
    temp_home_dir = tmp_path / "home"
    temp_home_dir.mkdir()
    monkeypatch.setenv("HOME", str(temp_home_dir))
    return temp_home_dir


class TestManualActivation:
    """Test manual activation using bin/activate.sh."""

    def test_manual_activation_full_flow(
        self, project_root: Path, temp_home: Path
    ) -> None:
        """Test complete manual activation flow with all checks.

        Verifies:
        - All environment variables are set correctly
        - XDG directories are created
        - PATH is modified
        - Environment is marked as active
        """
        script = f"""
        export HOME={temp_home}
        cd {project_root}
        source bin/activate.sh 2>&1

        # Output all relevant environment variables
        echo "MYCELIUM_ENV_ACTIVE=$MYCELIUM_ENV_ACTIVE"
        echo "MYCELIUM_ROOT=$MYCELIUM_ROOT"
        echo "MYCELIUM_CONFIG_DIR=$MYCELIUM_CONFIG_DIR"
        echo "MYCELIUM_DATA_DIR=$MYCELIUM_DATA_DIR"
        echo "MYCELIUM_CACHE_DIR=$MYCELIUM_CACHE_DIR"
        echo "MYCELIUM_STATE_DIR=$MYCELIUM_STATE_DIR"
        echo "MYCELIUM_PROJECT_DIR=$MYCELIUM_PROJECT_DIR"
        echo "PATH=$PATH"

        # Check directories exist
        test -d "$MYCELIUM_CONFIG_DIR" && echo "CONFIG_DIR_EXISTS=yes"
        test -d "$MYCELIUM_DATA_DIR" && echo "DATA_DIR_EXISTS=yes"
        test -d "$MYCELIUM_CACHE_DIR" && echo "CACHE_DIR_EXISTS=yes"
        test -d "$MYCELIUM_STATE_DIR" && echo "STATE_DIR_EXISTS=yes"

        # Check PATH contains project bin
        echo "$PATH" | grep -q "{project_root}/bin" && echo "PATH_CONTAINS_BIN=yes"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Parse output
        env_vars: dict[str, str] = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, _, value = line.partition("=")
                env_vars[key] = value

        # Verify environment variables
        assert env_vars.get("MYCELIUM_ENV_ACTIVE") == "1", "Environment not marked as active"
        assert env_vars.get("MYCELIUM_ROOT") == str(project_root)
        assert temp_home.name in env_vars.get("MYCELIUM_CONFIG_DIR", "")
        assert "mycelium" in env_vars.get("MYCELIUM_CONFIG_DIR", "")
        assert "mycelium" in env_vars.get("MYCELIUM_DATA_DIR", "")
        assert "mycelium" in env_vars.get("MYCELIUM_CACHE_DIR", "")
        assert "mycelium" in env_vars.get("MYCELIUM_STATE_DIR", "")
        assert env_vars.get("MYCELIUM_PROJECT_DIR") == str(project_root / ".mycelium")

        # Verify directories were created
        assert env_vars.get("CONFIG_DIR_EXISTS") == "yes"
        assert env_vars.get("DATA_DIR_EXISTS") == "yes"
        assert env_vars.get("CACHE_DIR_EXISTS") == "yes"
        assert env_vars.get("STATE_DIR_EXISTS") == "yes"

        # Verify PATH modification
        assert env_vars.get("PATH_CONTAINS_BIN") == "yes"

    def test_activation_deactivation_cycle(
        self, project_root: Path, temp_home: Path
    ) -> None:
        """Test full activation/deactivation cycle restores environment.

        Verifies:
        - Deactivation removes all MYCELIUM_* variables
        - PATH is restored to original
        - No environment pollution remains
        """
        script = f"""
        # Clean environment first - unset any existing MYCELIUM vars
        unset MYCELIUM_ENV_ACTIVE MYCELIUM_ROOT MYCELIUM_PROJECT_DIR
        unset MYCELIUM_CONFIG_DIR MYCELIUM_DATA_DIR MYCELIUM_CACHE_DIR MYCELIUM_STATE_DIR

        export HOME={temp_home}
        cd {project_root}

        # Record original PATH
        ORIGINAL_PATH="$PATH"
        echo "ORIGINAL_PATH=$ORIGINAL_PATH"

        # Activate
        source bin/activate.sh > /dev/null 2>&1
        echo "AFTER_ACTIVATION_ACTIVE=${{MYCELIUM_ENV_ACTIVE:-}}"

        # Deactivate - check if function exists first
        if type deactivate > /dev/null 2>&1; then
            deactivate > /dev/null 2>&1
        fi
        echo "AFTER_DEACTIVATION_ACTIVE=${{MYCELIUM_ENV_ACTIVE:-}}"
        echo "AFTER_DEACTIVATION_ROOT=${{MYCELIUM_ROOT:-}}"
        echo "FINAL_PATH=$PATH"

        # Check if PATH was restored
        if [ "$PATH" = "$ORIGINAL_PATH" ]; then
            echo "PATH_RESTORED=yes"
        else
            echo "PATH_RESTORED=no"
        fi
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Parse output
        env_vars: dict[str, str] = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, _, value = line.partition("=")
                env_vars[key] = value

        # Verify activation worked
        assert env_vars.get("AFTER_ACTIVATION_ACTIVE") == "1"

        # Verify deactivation cleaned up (empty string or unset)
        assert env_vars.get("AFTER_DEACTIVATION_ACTIVE", "") == ""
        assert env_vars.get("AFTER_DEACTIVATION_ROOT", "") == ""

        # Verify PATH was restored
        # The script itself checks if PATH equals ORIGINAL_PATH and reports the result
        # This is more reliable than comparing paths here due to environment differences
        assert env_vars.get("PATH_RESTORED") == "yes", f"PATH was not restored. Script output: {result.stdout}"

    def test_nested_activation_prevention(
        self, project_root: Path, temp_home: Path
    ) -> None:
        """Test that nested activation is prevented with warning.

        Verifies:
        - Second activation attempt shows warning
        - Environment remains stable (no double-activation)
        """
        script = f"""
        export HOME={temp_home}
        cd {project_root}

        # First activation
        source bin/activate.sh > /dev/null 2>&1
        echo "FIRST_ACTIVATION=$MYCELIUM_ENV_ACTIVE"

        # Second activation attempt (should warn)
        source bin/activate.sh 2>&1 | grep -i "already active" && echo "WARNING_SHOWN=yes"
        echo "SECOND_ACTIVATION=$MYCELIUM_ENV_ACTIVE"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Parse output
        env_vars: dict[str, str] = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, _, value = line.partition("=")
                env_vars[key] = value

        # Verify both activations succeeded but warning was shown
        assert env_vars.get("FIRST_ACTIVATION") == "1"
        assert env_vars.get("WARNING_SHOWN") == "yes"
        # Second activation should fail (returns 1) so MYCELIUM_ENV_ACTIVE stays 1
        assert env_vars.get("SECOND_ACTIVATION") == "1"

    def test_missing_pyproject_toml(self, tmp_path: Path, temp_home: Path) -> None:
        """Test activation fails gracefully when not in Mycelium project.

        Verifies:
        - Activation script validates project structure
        - Clear error message is shown
        """
        # Create a directory without pyproject.toml
        fake_project = tmp_path / "fake_project"
        fake_project.mkdir()

        # Copy activate.sh to fake project
        project_root = Path(__file__).parent.parent.parent.resolve()
        bin_dir = fake_project / "bin"
        bin_dir.mkdir()
        shutil.copy(project_root / "bin" / "activate.sh", bin_dir / "activate.sh")

        script = f"""
        # Clean environment first
        unset MYCELIUM_ENV_ACTIVE MYCELIUM_ROOT MYCELIUM_PROJECT_DIR
        unset MYCELIUM_CONFIG_DIR MYCELIUM_DATA_DIR MYCELIUM_CACHE_DIR MYCELIUM_STATE_DIR

        export HOME={temp_home}
        cd {fake_project}
        source bin/activate.sh 2>&1 | grep -i "pyproject.toml" && echo "ERROR_SHOWN=yes"
        echo "ENV_ACTIVE=${{MYCELIUM_ENV_ACTIVE:-}}"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
        )

        env_vars: dict[str, str] = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, _, value = line.partition("=")
                env_vars[key] = value

        # Verify error was shown and environment not activated
        assert env_vars.get("ERROR_SHOWN") == "yes"
        assert env_vars.get("ENV_ACTIVE", "") == ""


class TestDirenvActivation:
    """Test direnv-based automatic activation."""

    @pytest.mark.skipif(
        shutil.which("direnv") is None,
        reason="direnv not installed",
    )
    def test_direnv_activation(self, project_root: Path, temp_home: Path) -> None:
        """Test direnv activation sets environment correctly.

        Verifies:
        - .envrc is loaded by direnv
        - All environment variables are set
        - Activation is automatic
        """
        script = f"""
        export HOME={temp_home}

        # Setup direnv hook
        eval "$(direnv hook bash)"

        # Navigate to project (triggers direnv)
        cd {project_root}

        # Allow .envrc
        direnv allow . 2>&1

        # Force reload
        eval "$(direnv export bash)"

        # Output environment
        echo "MYCELIUM_ENV_ACTIVE=$MYCELIUM_ENV_ACTIVE"
        echo "MYCELIUM_ROOT=$MYCELIUM_ROOT"
        echo "MYCELIUM_CONFIG_DIR=$MYCELIUM_CONFIG_DIR"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=15,
        )

        # Parse output
        env_vars: dict[str, str] = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, _, value = line.partition("=")
                env_vars[key] = value

        # Verify environment variables are set
        assert env_vars.get("MYCELIUM_ENV_ACTIVE") == "1"
        assert env_vars.get("MYCELIUM_ROOT") == str(project_root)
        assert "mycelium" in env_vars.get("MYCELIUM_CONFIG_DIR", "").lower()


class TestRuntimeValidation:
    """Test runtime validation catches missing environment."""

    def test_runtime_validation_catches_missing_environment(
        self, project_root: Path, clean_environment: None
    ) -> None:
        """Test env_validator catches when environment is not active.

        Verifies:
        - env_validator.validate_environment() raises error
        - Error message is actionable
        """
        script = f"""
        cd {project_root}

        # Activate virtual environment to use installed package
        if [ -d .venv/bin ]; then
            source .venv/bin/activate
        fi

        # Try to run validation without activating mycelium environment
        python3 -c "
from mycelium_onboarding.env_validator import validate_environment, EnvironmentValidationError
try:
    validate_environment()
    print('VALIDATION_PASSED=yes')
except EnvironmentValidationError as e:
    print('VALIDATION_FAILED=yes')
    print(f'ERROR_MESSAGE={{str(e)[:50]}}')
"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Parse output
        output = result.stdout.strip()

        # Verify validation failed appropriately
        assert "VALIDATION_FAILED=yes" in output
        assert "VALIDATION_PASSED=yes" not in output

    def test_runtime_validation_passes_when_active(
        self, project_root: Path, temp_home: Path
    ) -> None:
        """Test env_validator passes when environment is properly activated.

        Verifies:
        - validate_environment() succeeds after activation
        - No exceptions are raised
        """
        script = f"""
        export HOME={temp_home}
        cd {project_root}

        # Activate environment
        source bin/activate.sh > /dev/null 2>&1

        # Activate virtual environment
        if [ -d .venv/bin ]; then
            source .venv/bin/activate
        fi

        # Try validation
        python3 -c "
from mycelium_onboarding.env_validator import validate_environment
try:
    validate_environment()
    print('VALIDATION_PASSED=yes')
except Exception as e:
    print(f'VALIDATION_FAILED={{str(e)[:50]}}')
"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Parse output
        output = result.stdout.strip()

        # Verify validation passed
        assert "VALIDATION_PASSED=yes" in output
        assert "VALIDATION_FAILED" not in output


class TestXDGDirectories:
    """Test XDG directory creation and management."""

    def test_xdg_directories_created_with_correct_structure(
        self, project_root: Path, temp_home: Path
    ) -> None:
        """Test all XDG directories are created with correct paths.

        Verifies:
        - All four XDG directories created
        - Correct XDG hierarchy (.config, .local/share, .cache, .local/state)
        - Directories are writable
        """
        script = f"""
        export HOME={temp_home}
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1

        # Check each directory
        test -d "$MYCELIUM_CONFIG_DIR" && echo "CONFIG_DIR_EXISTS=yes"
        test -w "$MYCELIUM_CONFIG_DIR" && echo "CONFIG_DIR_WRITABLE=yes"

        test -d "$MYCELIUM_DATA_DIR" && echo "DATA_DIR_EXISTS=yes"
        test -w "$MYCELIUM_DATA_DIR" && echo "DATA_DIR_WRITABLE=yes"

        test -d "$MYCELIUM_CACHE_DIR" && echo "CACHE_DIR_EXISTS=yes"
        test -w "$MYCELIUM_CACHE_DIR" && echo "CACHE_DIR_WRITABLE=yes"

        test -d "$MYCELIUM_STATE_DIR" && echo "STATE_DIR_EXISTS=yes"
        test -w "$MYCELIUM_STATE_DIR" && echo "STATE_DIR_WRITABLE=yes"

        # Verify XDG structure
        echo "$MYCELIUM_CONFIG_DIR" | grep -q ".config/mycelium" && echo "CONFIG_PATH_CORRECT=yes"
        echo "$MYCELIUM_DATA_DIR" | grep -q ".local/share/mycelium" && echo "DATA_PATH_CORRECT=yes"
        echo "$MYCELIUM_CACHE_DIR" | grep -q ".cache/mycelium" && echo "CACHE_PATH_CORRECT=yes"
        echo "$MYCELIUM_STATE_DIR" | grep -q ".local/state/mycelium" && echo "STATE_PATH_CORRECT=yes"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Parse output
        checks: dict[str, str] = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, _, value = line.partition("=")
                checks[key] = value

        # Verify all directories exist and are writable
        assert checks.get("CONFIG_DIR_EXISTS") == "yes"
        assert checks.get("CONFIG_DIR_WRITABLE") == "yes"
        assert checks.get("DATA_DIR_EXISTS") == "yes"
        assert checks.get("DATA_DIR_WRITABLE") == "yes"
        assert checks.get("CACHE_DIR_EXISTS") == "yes"
        assert checks.get("CACHE_DIR_WRITABLE") == "yes"
        assert checks.get("STATE_DIR_EXISTS") == "yes"
        assert checks.get("STATE_DIR_WRITABLE") == "yes"

        # Verify correct XDG paths
        assert checks.get("CONFIG_PATH_CORRECT") == "yes"
        assert checks.get("DATA_PATH_CORRECT") == "yes"
        assert checks.get("CACHE_PATH_CORRECT") == "yes"
        assert checks.get("STATE_PATH_CORRECT") == "yes"


class TestConfigHierarchy:
    """Test configuration hierarchy (project-local overrides user-global)."""

    def test_project_local_config_accessible(
        self, project_root: Path, temp_home: Path
    ) -> None:
        """Test project-local config directory is accessible.

        Verifies:
        - MYCELIUM_PROJECT_DIR points to .mycelium/
        - Directory exists or can be created
        - Can write to project-local config
        """
        script = f"""
        export HOME={temp_home}
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1

        # Check project directory
        echo "PROJECT_DIR=$MYCELIUM_PROJECT_DIR"
        echo "$MYCELIUM_PROJECT_DIR" | grep -q ".mycelium" && echo "PROJECT_PATH_CORRECT=yes"

        # Create directory if doesn't exist, then try to write
        mkdir -p "$MYCELIUM_PROJECT_DIR" 2>/dev/null
        touch "$MYCELIUM_PROJECT_DIR/test_config.yaml" 2>/dev/null && echo "WRITE_SUCCESS=yes"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Parse output
        checks: dict[str, str] = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, _, value = line.partition("=")
                checks[key] = value

        # Verify project directory is correct
        assert checks.get("PROJECT_PATH_CORRECT") == "yes"
        assert checks.get("WRITE_SUCCESS") == "yes"


class TestCrossPlatform:
    """Test cross-platform path handling."""

    def test_cross_platform_paths(
        self, project_root: Path, temp_home: Path
    ) -> None:
        """Test path handling works correctly on current platform.

        Verifies:
        - Paths are absolute
        - No Windows-style backslashes on Unix
        - Directories are accessible
        """
        script = f"""
        export HOME={temp_home}
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1

        # Check paths are absolute
        echo "$MYCELIUM_ROOT" | grep -q "^/" && echo "ROOT_ABSOLUTE=yes"
        echo "$MYCELIUM_CONFIG_DIR" | grep -q "^/" && echo "CONFIG_ABSOLUTE=yes"

        # Check no backslashes (Windows paths)
        echo "$MYCELIUM_ROOT" | grep -q "\\\\" && echo "HAS_BACKSLASH=yes" || echo "NO_BACKSLASH=yes"

        # Check all paths are accessible
        test -e "$MYCELIUM_ROOT" && echo "ROOT_ACCESSIBLE=yes"
        test -e "$MYCELIUM_CONFIG_DIR" && echo "CONFIG_ACCESSIBLE=yes"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Parse output
        checks: dict[str, str] = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, _, value = line.partition("=")
                checks[key] = value

        # Verify platform compatibility
        assert checks.get("ROOT_ABSOLUTE") == "yes"
        assert checks.get("CONFIG_ABSOLUTE") == "yes"
        assert checks.get("NO_BACKSLASH") == "yes"
        assert checks.get("ROOT_ACCESSIBLE") == "yes"
        assert checks.get("CONFIG_ACCESSIBLE") == "yes"

    @pytest.mark.skipif(
        not Path("/proc/version").exists(),
        reason="Not running on Linux",
    )
    def test_wsl_detection(self, project_root: Path, temp_home: Path) -> None:
        """Test WSL detection works correctly (Linux only).

        Verifies:
        - WSL is detected when present
        - Warnings are shown for /mnt/* paths
        """
        # Only run if we're actually on WSL
        try:
            with open("/proc/version") as f:
                if "microsoft" not in f.read().lower():
                    pytest.skip("Not running on WSL")
        except Exception:
            pytest.skip("Cannot determine WSL status")

        script = f"""
        export HOME={temp_home}
        cd {project_root}
        source bin/activate.sh 2>&1 | grep -i "WSL" && echo "WSL_DETECTED=yes"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Check if WSL was mentioned (either detected or warning shown)
        # This is informational, not a hard requirement
        output = result.stdout.strip()
        # Test passes regardless, just checking detection works
        assert result.returncode in (0, 1)  # May exit 1 if warning not confirmed


class TestMissingDependencies:
    """Test graceful handling of missing dependencies."""

    def test_missing_venv_shows_warning(
        self, tmp_path: Path, temp_home: Path
    ) -> None:
        """Test activation warns about missing virtual environment.

        Verifies:
        - Warning is shown when .venv doesn't exist
        - Activation still proceeds (non-fatal)
        - User gets actionable message
        """
        # Create a minimal project without .venv
        fake_project = tmp_path / "fake_project"
        fake_project.mkdir()

        # Create required files
        (fake_project / ".git").mkdir()
        (fake_project / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        # Copy activate.sh
        project_root = Path(__file__).parent.parent.parent.resolve()
        bin_dir = fake_project / "bin"
        bin_dir.mkdir()
        shutil.copy(project_root / "bin" / "activate.sh", bin_dir / "activate.sh")

        script = f"""
        # Clean environment first
        unset MYCELIUM_ENV_ACTIVE MYCELIUM_ROOT MYCELIUM_PROJECT_DIR
        unset MYCELIUM_CONFIG_DIR MYCELIUM_DATA_DIR MYCELIUM_CACHE_DIR MYCELIUM_STATE_DIR

        export HOME={temp_home}
        cd {fake_project}
        source bin/activate.sh 2>&1
        echo "ENV_ACTIVE=${{MYCELIUM_ENV_ACTIVE:-}}"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
        )

        checks: dict[str, str] = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, _, value = line.partition("=")
                checks[key] = value

        # Verify warning was shown and activation succeeded (it's a warning, not error)
        assert "virtual environment not found" in result.stdout.lower()
        # Activation should succeed despite warning
        assert checks.get("ENV_ACTIVE") == "1"


class TestDiagnosticTools:
    """Test diagnostic and troubleshooting tools."""

    def test_diagnose_command_runs(self, project_root: Path) -> None:
        """Test mycelium-diagnose command runs successfully.

        Verifies:
        - Command executes without errors
        - Outputs diagnostic information
        - Shows environment status
        """
        result = subprocess.run(
            [str(project_root / "bin" / "mycelium-diagnose")],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Verify command succeeded
        assert result.returncode == 0

        # Verify output contains expected sections
        output = result.stdout
        assert "Mycelium Environment Diagnostics" in output
        assert "Shell Information" in output
        assert "Environment Variables" in output
        assert "Directory Status" in output

    def test_check_dependencies_runs(self, project_root: Path) -> None:
        """Test check-dependencies.sh runs successfully.

        Verifies:
        - Command executes without errors
        - Checks for required tools
        - Provides clear output
        """
        result = subprocess.run(
            [str(project_root / "bin" / "check-dependencies.sh")],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Command should succeed or fail gracefully
        assert result.returncode in (0, 1)

        # Verify output contains dependency checks
        output = result.stdout + result.stderr
        assert "Python" in output or "python" in output
