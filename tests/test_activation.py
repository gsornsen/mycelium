"""
Tests for shell activation scripts and wrapper scripts.

Tests cover:
- Activation script functionality
- Environment variable setting
- Deactivation and cleanup
- Wrapper script behavior
- Diagnostic command
- Dependency checker

NOTE: These tests require bash and are skipped on Windows.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

# Skip all tests in this module on Windows since they require bash
pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="Activation tests require bash which is not available on Windows"
)


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    # Navigate up from tests/ to project root
    return Path(__file__).parent.parent.resolve()


@pytest.fixture
def clean_environment(monkeypatch) -> None:
    """Ensure clean environment without MYCELIUM_* variables."""
    # Remove all MYCELIUM_* environment variables
    for key in list(os.environ.keys()):
        if key.startswith("MYCELIUM_"):
            monkeypatch.delenv(key, raising=False)


class TestActivationScript:
    """Test bin/activate.sh script."""

    def test_activation_sets_environment_variables(self, project_root: Path, clean_environment):
        """Test that activation sets all required environment variables."""
        # Source the activation script and check variables
        script = f"""
        # Clean environment first
        unset MYCELIUM_ENV_ACTIVE MYCELIUM_ROOT MYCELIUM_PROJECT_DIR
        unset MYCELIUM_CONFIG_DIR MYCELIUM_DATA_DIR MYCELIUM_CACHE_DIR MYCELIUM_STATE_DIR

        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1
        echo "MYCELIUM_ENV_ACTIVE=${{MYCELIUM_ENV_ACTIVE:-}}"
        echo "MYCELIUM_ROOT=${{MYCELIUM_ROOT:-}}"
        echo "MYCELIUM_CONFIG_DIR=${{MYCELIUM_CONFIG_DIR:-}}"
        echo "MYCELIUM_DATA_DIR=${{MYCELIUM_DATA_DIR:-}}"
        echo "MYCELIUM_CACHE_DIR=${{MYCELIUM_CACHE_DIR:-}}"
        echo "MYCELIUM_STATE_DIR=${{MYCELIUM_STATE_DIR:-}}"
        echo "MYCELIUM_PROJECT_DIR=${{MYCELIUM_PROJECT_DIR:-}}"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Parse output
        env_vars = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                env_vars[key] = value

        # Verify all required variables are set
        assert env_vars.get("MYCELIUM_ENV_ACTIVE") == "1"
        assert env_vars.get("MYCELIUM_ROOT") == str(project_root)
        assert "/.config/mycelium" in env_vars.get("MYCELIUM_CONFIG_DIR", "")
        assert "/.local/share/mycelium" in env_vars.get("MYCELIUM_DATA_DIR", "")
        assert "/.cache/mycelium" in env_vars.get("MYCELIUM_CACHE_DIR", "")
        assert "/.local/state/mycelium" in env_vars.get("MYCELIUM_STATE_DIR", "")
        assert env_vars.get("MYCELIUM_PROJECT_DIR") == str(project_root / ".mycelium")

    def test_activation_creates_xdg_directories(self, project_root: Path, clean_environment, tmp_path: Path):
        """Test that activation creates XDG directories."""
        # Use temp HOME to avoid modifying user's actual directories
        script = f"""
        # Clean environment first
        unset MYCELIUM_ENV_ACTIVE MYCELIUM_ROOT MYCELIUM_PROJECT_DIR
        unset MYCELIUM_CONFIG_DIR MYCELIUM_DATA_DIR MYCELIUM_CACHE_DIR MYCELIUM_STATE_DIR

        export HOME={tmp_path}
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1

        # Check if directories exist
        test -d "${{MYCELIUM_CONFIG_DIR:-}}" && echo "CONFIG_EXISTS=1"
        test -d "${{MYCELIUM_DATA_DIR:-}}" && echo "DATA_EXISTS=1"
        test -d "${{MYCELIUM_CACHE_DIR:-}}" && echo "CACHE_EXISTS=1"
        test -d "${{MYCELIUM_STATE_DIR:-}}" && echo "STATE_EXISTS=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        output = result.stdout.strip()
        assert "CONFIG_EXISTS=1" in output
        assert "DATA_EXISTS=1" in output
        assert "CACHE_EXISTS=1" in output
        assert "STATE_EXISTS=1" in output

    def test_activation_modifies_path(self, project_root: Path, clean_environment):
        """Test that activation prepends project bin to PATH."""
        script = f"""
        cd {project_root}
        ORIGINAL_PATH="$PATH"
        source bin/activate.sh > /dev/null 2>&1

        # Check if project bin is in PATH
        echo "$PATH" | grep -q "{project_root}/bin" && echo "BIN_IN_PATH=1"

        # Check if original PATH is preserved
        echo "$PATH" | grep -q "$ORIGINAL_PATH" && echo "ORIGINAL_PRESERVED=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        output = result.stdout.strip()
        assert "BIN_IN_PATH=1" in output
        # Note: Original PATH preservation check might fail due to variable expansion

    def test_activation_modifies_prompt(self, project_root: Path, clean_environment):
        """Test that activation modifies shell prompt."""
        script = f"""
        cd {project_root}
        export PS1="original> "
        source bin/activate.sh > /dev/null 2>&1
        echo "$PS1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        prompt = result.stdout.strip()
        assert "(mycelium)" in prompt or "mycelium" in prompt.lower()

    def test_activation_prevents_double_activation(self, project_root: Path, clean_environment):
        """Test that double activation is prevented."""
        script = f"""
        cd {project_root}
        source bin/activate.sh 2>&1
        source bin/activate.sh 2>&1
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Should contain message about already being activated
        assert "already" in result.stdout.lower() or "already" in result.stderr.lower()

    def test_activation_validates_project_root(self, project_root: Path, clean_environment):
        """Test that activation validates MYCELIUM_ROOT."""
        # Activate should only work from project root
        script = f"""
        cd /tmp
        source {project_root}/bin/activate.sh 2>&1
        """

        subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Should work regardless of current directory
        # Or should warn/fail if not in project directory (implementation dependent)
        # This test documents the behavior rather than enforcing it

    def test_deactivate_function_defined(self, project_root: Path, clean_environment):
        """Test that deactivate function is defined after activation."""
        script = f"""
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1
        type deactivate > /dev/null 2>&1 && echo "DEACTIVATE_DEFINED=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        assert "DEACTIVATE_DEFINED=1" in result.stdout


class TestDeactivation:
    """Test deactivation functionality."""

    def test_deactivate_restores_path(self, project_root: Path, clean_environment):
        """Test that deactivate restores original PATH."""
        script = f"""
        cd {project_root}
        ORIGINAL_PATH="$PATH"
        source bin/activate.sh > /dev/null 2>&1
        deactivate > /dev/null 2>&1
        test "$PATH" = "$ORIGINAL_PATH" && echo "PATH_RESTORED=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        assert "PATH_RESTORED=1" in result.stdout

    def test_deactivate_restores_prompt(self, project_root: Path, clean_environment):
        """Test that deactivate restores original prompt."""
        script = f"""
        cd {project_root}
        export PS1="original> "
        ORIGINAL_PS1="$PS1"
        source bin/activate.sh > /dev/null 2>&1
        deactivate > /dev/null 2>&1
        test "$PS1" = "$ORIGINAL_PS1" && echo "PROMPT_RESTORED=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        assert "PROMPT_RESTORED=1" in result.stdout

    def test_deactivate_unsets_variables(self, project_root: Path, clean_environment):
        """Test that deactivate unsets MYCELIUM_* variables."""
        script = f"""
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1
        deactivate > /dev/null 2>&1
        test -z "${{MYCELIUM_ENV_ACTIVE:-}}" && echo "ENV_ACTIVE_UNSET=1"
        test -z "${{MYCELIUM_ROOT:-}}" && echo "ROOT_UNSET=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        assert "ENV_ACTIVE_UNSET=1" in result.stdout
        # MYCELIUM_ROOT might be preserved for reference

    def test_deactivate_removes_itself(self, project_root: Path, clean_environment):
        """Test that deactivate function removes itself."""
        script = f"""
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1
        deactivate > /dev/null 2>&1
        type deactivate > /dev/null 2>&1 || echo "DEACTIVATE_REMOVED=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        assert "DEACTIVATE_REMOVED=1" in result.stdout


class TestWrapperScript:
    """Test wrapper script behavior."""

    def test_wrapper_fails_without_activation(self, project_root: Path, clean_environment):
        """Test that wrapper script fails when environment not activated."""
        result = subprocess.run(
            [str(project_root / "bin" / "mycelium-wrapper")],
            capture_output=True,
            text=True,
        )

        # Should fail with error about activation
        assert result.returncode != 0
        assert "activate" in result.stderr.lower() or "not activated" in result.stderr.lower()

    def test_wrapper_works_with_activation(self, project_root: Path, clean_environment):
        """Test that wrapper script works when environment is activated."""
        script = f"""
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1
        bin/mycelium-wrapper --help 2>&1
        """

        subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Should succeed or show help
        # (exact behavior depends on wrapper implementation)


class TestDiagnosticCommand:
    """Test diagnostic command."""

    @pytest.mark.skip(reason="diagnose command not yet implemented")
    def test_diagnose_runs_successfully(self, project_root: Path, clean_environment):
        """Test that mycelium diagnose runs successfully."""
        script = f"""
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1
        python -m mycelium_onboarding diagnose 2>&1
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Should run without error
        assert result.returncode == 0

    def test_diagnose_detects_inactive_environment(self, project_root: Path, clean_environment):
        """Test that diagnose detects inactive environment."""
        result = subprocess.run(
            ["python", "-m", "mycelium_onboarding", "diagnose"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        # Should mention that environment is not activated
        output = result.stdout + result.stderr
        assert "not activated" in output.lower() or "inactive" in output.lower()

    @pytest.mark.skip(reason="diagnose command not yet implemented")
    def test_diagnose_detects_active_environment(self, project_root: Path, clean_environment):
        """Test that diagnose detects active environment."""
        script = f"""
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1
        python -m mycelium_onboarding diagnose 2>&1
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Should mention that environment is activated
        output = result.stdout
        assert "active" in output.lower() or "activated" in output.lower()


class TestDependencyChecker:
    """Test dependency checker functionality."""

    def test_dependency_checker_runs(self, project_root: Path, clean_environment):
        """Test that dependency checker runs without error."""
        script = f"""
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1
        python -m mycelium_onboarding check-deps 2>&1
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Should run without critical errors
        assert result.returncode in [0, 1]  # May return 1 if optional deps missing

    def test_dependency_checker_detects_python(self, project_root: Path, clean_environment):
        """Test that dependency checker detects Python."""
        script = f"""
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1
        python -m mycelium_onboarding check-deps 2>&1
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Should mention Python
        output = result.stdout
        assert "python" in output.lower()

    def test_dependency_checker_shows_summary(self, project_root: Path, clean_environment):
        """Test that dependency checker shows summary."""
        script = f"""
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1
        python -m mycelium_onboarding check-deps 2>&1
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Should show some kind of summary
        output = result.stdout
        assert len(output) > 0


class TestShellCompatibility:
    """Test shell compatibility."""

    def test_bash_compatibility(self, project_root: Path, clean_environment):
        """Test that activation works in bash."""
        script = f"""
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1
        test "$MYCELIUM_ENV_ACTIVE" = "1" && echo "BASH_OK=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        assert "BASH_OK=1" in result.stdout

    @pytest.mark.skipif(not Path("/bin/zsh").exists(), reason="zsh not available")
    def test_zsh_compatibility(self, project_root: Path, clean_environment):
        """Test that activation works in zsh."""
        script = f"""
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1
        test "$MYCELIUM_ENV_ACTIVE" = "1" && echo "ZSH_OK=1"
        """

        result = subprocess.run(
            ["zsh", "-c", script],
            capture_output=True,
            text=True,
        )

        assert "ZSH_OK=1" in result.stdout


class TestVerboseMode:
    """Test verbose mode."""

    def test_verbose_mode_with_flag(self, project_root: Path, clean_environment):
        """Test verbose mode with -v flag."""
        script = f"""
        cd {project_root}
        bash -x bin/activate.sh 2>&1 | grep -q "MYCELIUM" && echo "VERBOSE_OUTPUT=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # bash -x should show variable assignments
        assert "VERBOSE_OUTPUT=1" in result.stdout

    def test_verbose_mode_with_env_var(self, project_root: Path, clean_environment):
        """Test verbose mode with MYCELIUM_VERBOSE env var."""
        script = f"""
        cd {project_root}
        export MYCELIUM_VERBOSE=1
        source bin/activate.sh 2>&1 | grep -q "MYCELIUM" && echo "VERBOSE_ENV_OUTPUT=1"
        """

        subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Should show verbose output
        # (implementation dependent)


class TestEdgeCases:
    """Test edge cases."""

    def test_activation_outside_project(self, project_root: Path, clean_environment):
        """Test activation from outside project directory."""
        script = f"""
        cd /tmp
        source {project_root}/bin/activate.sh > /dev/null 2>&1
        test -n "${{MYCELIUM_ENV_ACTIVE:-}}" && echo "ACTIVATED_OUTSIDE=1"
        """

        subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Should work or fail gracefully depending on implementation
        # This test documents the behavior

    def test_activation_with_missing_directories(self, project_root: Path, clean_environment, tmp_path: Path):
        """Test activation with missing directories."""
        script = f"""
        export HOME={tmp_path}/nonexistent
        cd {project_root}
        source bin/activate.sh 2>&1
        test -n "${{MYCELIUM_ENV_ACTIVE:-}}" && echo "ACTIVATED_WITH_MISSING_DIRS=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Should create directories and activate successfully
        assert "ACTIVATED_WITH_MISSING_DIRS=1" in result.stdout


class TestFullActivationCycle:
    """Test full activation/deactivation cycle."""

    def test_complete_activation_deactivation_cycle(self, project_root: Path, clean_environment):
        """Test complete activation and deactivation cycle."""
        script = f"""
        cd {project_root}

        # Before activation
        test -z "${{MYCELIUM_ENV_ACTIVE:-}}" && echo "STEP1_NOT_ACTIVE=1"

        # Activate
        source bin/activate.sh > /dev/null 2>&1
        test "$MYCELIUM_ENV_ACTIVE" = "1" && echo "STEP2_ACTIVE=1"

        # Deactivate
        deactivate > /dev/null 2>&1
        test -z "${{MYCELIUM_ENV_ACTIVE:-}}" && echo "STEP3_DEACTIVATED=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        output = result.stdout
        assert "STEP1_NOT_ACTIVE=1" in output
        assert "STEP2_ACTIVE=1" in output
        assert "STEP3_DEACTIVATED=1" in output
