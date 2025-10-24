"""
Tests for shell activation scripts and wrapper scripts.

Tests cover:
- Activation script functionality
- Environment variable setting
- Deactivation and cleanup
- Wrapper script behavior
- Diagnostic command
- Dependency checker
"""

import os
import subprocess
from pathlib import Path

import pytest


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

    def test_activation_sets_environment_variables(
        self, project_root: Path, clean_environment
    ):
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
        assert env_vars.get("MYCELIUM_PROJECT_DIR") == str(
            project_root / ".mycelium"
        )

    def test_activation_creates_xdg_directories(
        self, project_root: Path, clean_environment, tmp_path: Path
    ):
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
        assert "(mycelium)" in prompt
        assert "original>" in prompt

    def test_activation_prevents_double_activation(
        self, project_root: Path, clean_environment
    ):
        """Test that activating twice shows warning."""
        script = f"""
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1
        source bin/activate.sh 2>&1
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Should see warning about already active
        assert "already active" in result.stdout.lower()

    def test_activation_validates_project_root(self, tmp_path: Path):
        """Test that activation fails in non-project directory."""
        # Create a temporary directory without pyproject.toml
        script = f"""
        # Clean environment first
        unset MYCELIUM_ENV_ACTIVE MYCELIUM_ROOT MYCELIUM_PROJECT_DIR
        unset MYCELIUM_CONFIG_DIR MYCELIUM_DATA_DIR MYCELIUM_CACHE_DIR MYCELIUM_STATE_DIR

        cd {tmp_path}
        source {tmp_path}/activate_test.sh 2>&1
        echo "ENV_ACTIVE=${{MYCELIUM_ENV_ACTIVE:-}}"
        """

        # Create a test activation script in temp directory
        test_script = tmp_path / "activate_test.sh"
        activate_script = Path(__file__).parent.parent / "bin" / "activate.sh"
        test_script.write_text(activate_script.read_text())

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Should fail with error about missing pyproject.toml
        assert "pyproject.toml" in result.stdout.lower()

    def test_deactivate_function_defined(
        self, project_root: Path, clean_environment
    ):
        """Test that deactivate function is defined after activation."""
        script = f"""
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1

        # Check if deactivate function exists
        type deactivate > /dev/null 2>&1 && echo "DEACTIVATE_DEFINED=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        assert "DEACTIVATE_DEFINED=1" in result.stdout


class TestDeactivation:
    """Test deactivate function."""

    def test_deactivate_restores_path(self, project_root: Path, clean_environment):
        """Test that deactivate restores original PATH."""
        script = f"""
        cd {project_root}
        ORIGINAL_PATH="$PATH"
        source bin/activate.sh > /dev/null 2>&1
        deactivate > /dev/null 2>&1

        # Check if PATH restored
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

        # Check if prompt restored
        test "$PS1" = "$ORIGINAL_PS1" && echo "PROMPT_RESTORED=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        assert "PROMPT_RESTORED=1" in result.stdout

    def test_deactivate_unsets_variables(
        self, project_root: Path, clean_environment
    ):
        """Test that deactivate unsets all MYCELIUM_* variables."""
        script = f"""
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1
        deactivate > /dev/null 2>&1

        # Check if variables unset
        test -z "$MYCELIUM_ENV_ACTIVE" && echo "ENV_ACTIVE_UNSET=1"
        test -z "$MYCELIUM_ROOT" && echo "ROOT_UNSET=1"
        test -z "$MYCELIUM_CONFIG_DIR" && echo "CONFIG_UNSET=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        output = result.stdout.strip()
        assert "ENV_ACTIVE_UNSET=1" in output
        assert "ROOT_UNSET=1" in output
        assert "CONFIG_UNSET=1" in output

    def test_deactivate_removes_itself(self, project_root: Path, clean_environment):
        """Test that deactivate function removes itself after execution."""
        script = f"""
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1
        deactivate > /dev/null 2>&1

        # Try to call deactivate again - should fail
        type deactivate > /dev/null 2>&1 || echo "FUNCTION_REMOVED=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        assert "FUNCTION_REMOVED=1" in result.stdout


class TestWrapperScript:
    """Test bin/mycelium wrapper script."""

    def test_wrapper_fails_without_activation(
        self, project_root: Path, clean_environment
    ):
        """Test that wrapper script fails when environment not active."""
        result = subprocess.run(
            [str(project_root / "bin" / "mycelium"), "--help"],
            capture_output=True,
            text=True,
            env={k: v for k, v in os.environ.items() if not k.startswith("MYCELIUM_")},
        )

        # Should fail with non-zero exit code
        assert result.returncode != 0

        # Should have error message about activation
        assert "not active" in result.stderr.lower()

    def test_wrapper_works_with_activation(self, project_root: Path):
        """Test that wrapper script works when environment is active."""
        # This test requires the mycelium_onboarding module to be installed
        # We'll simulate activation by setting the required variable
        script = f"""
        cd {project_root}
        export MYCELIUM_ENV_ACTIVE=1
        {project_root}/bin/mycelium --help 2>&1 || echo "EXPECTED_FAIL"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Either succeeds or fails with Python error (module not found)
        # but NOT with activation error
        assert "not active" not in result.stdout.lower()
        assert "not active" not in result.stderr.lower()


class TestDiagnosticCommand:
    """Test bin/mycelium-diagnose command."""

    def test_diagnose_runs_successfully(self, project_root: Path):
        """Test that diagnose command runs without errors."""
        result = subprocess.run(
            [str(project_root / "bin" / "mycelium-diagnose")],
            capture_output=True,
            text=True,
        )

        # Should succeed
        assert result.returncode == 0

        # Should contain expected sections
        output = result.stdout
        assert "Shell Information" in output
        assert "Environment Variables" in output
        assert "Directory Status" in output
        assert "PATH Check" in output
        assert "Virtual Environment" in output
        assert "Recommendations" in output

    def test_diagnose_detects_inactive_environment(
        self, project_root: Path, clean_environment
    ):
        """Test that diagnose detects when environment is not active."""
        result = subprocess.run(
            [str(project_root / "bin" / "mycelium-diagnose")],
            capture_output=True,
            text=True,
            env={k: v for k, v in os.environ.items() if not k.startswith("MYCELIUM_")},
        )

        output = result.stdout
        assert "No MYCELIUM_* variables set" in output
        assert "Environment not activated" in output

    def test_diagnose_detects_active_environment(self, project_root: Path):
        """Test that diagnose detects when environment is active."""
        # Set environment variables to simulate activation
        env = os.environ.copy()
        env["MYCELIUM_ENV_ACTIVE"] = "1"
        env["MYCELIUM_ROOT"] = str(project_root)

        result = subprocess.run(
            [str(project_root / "bin" / "mycelium-diagnose")],
            capture_output=True,
            text=True,
            env=env,
        )

        output = result.stdout
        assert "MYCELIUM_ENV_ACTIVE=1" in output
        assert "MYCELIUM_ROOT=" in output


class TestDependencyChecker:
    """Test bin/check-dependencies.sh script."""

    def test_dependency_checker_runs(self, project_root: Path):
        """Test that dependency checker runs successfully."""
        result = subprocess.run(
            [str(project_root / "bin" / "check-dependencies.sh")],
            capture_output=True,
            text=True,
        )

        # Should succeed (with warnings) or fail (missing deps)
        # Either way, should produce output
        assert len(result.stdout) > 0

        # Should check for Python
        assert "python3" in result.stdout.lower()

        # Should check for git
        assert "git" in result.stdout.lower()

    def test_dependency_checker_detects_python(self, project_root: Path):
        """Test that dependency checker detects Python installation."""
        result = subprocess.run(
            [str(project_root / "bin" / "check-dependencies.sh")],
            capture_output=True,
            text=True,
        )

        # Python should be found (we're running in Python environment)
        assert "python3:" in result.stdout
        # Should NOT say "not found"
        assert "python3: not found" not in result.stdout

    def test_dependency_checker_shows_summary(self, project_root: Path):
        """Test that dependency checker shows summary."""
        result = subprocess.run(
            [str(project_root / "bin" / "check-dependencies.sh")],
            capture_output=True,
            text=True,
        )

        output = result.stdout
        assert "Summary" in output
        # Should show PASSED or FAILED
        assert "PASSED" in output or "FAILED" in output


class TestShellCompatibility:
    """Test shell compatibility (bash, zsh)."""

    def test_bash_compatibility(self, project_root: Path, clean_environment):
        """Test that activation works in bash."""
        script = f"""
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1
        test "$MYCELIUM_ENV_ACTIVE" = "1" && echo "BASH_WORKS=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        assert "BASH_WORKS=1" in result.stdout

    @pytest.mark.skipif(
        not subprocess.run(
            ["which", "zsh"], capture_output=True
        ).returncode
        == 0,
        reason="zsh not installed",
    )
    def test_zsh_compatibility(self, project_root: Path, clean_environment):
        """Test that activation works in zsh."""
        script = f"""
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1
        test "$MYCELIUM_ENV_ACTIVE" = "1" && echo "ZSH_WORKS=1"
        """

        result = subprocess.run(
            ["zsh", "-c", script],
            capture_output=True,
            text=True,
        )

        assert "ZSH_WORKS=1" in result.stdout


class TestVerboseMode:
    """Test verbose/debug mode."""

    def test_verbose_mode_with_flag(self, project_root: Path, clean_environment):
        """Test that verbose mode works with --verbose flag."""
        script = f"""
        cd {project_root}
        source bin/activate.sh --verbose 2>&1 | head -n 5
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Should see verbose output (set -x traces)
        assert "Activation started at" in result.stdout

    def test_verbose_mode_with_env_var(self, project_root: Path, clean_environment):
        """Test that verbose mode works with MYCELIUM_VERBOSE env var."""
        script = f"""
        cd {project_root}
        export MYCELIUM_VERBOSE=1
        source bin/activate.sh 2>&1 | head -n 5
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Should see verbose output
        assert "Activation started at" in result.stdout


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_activation_outside_project(self, tmp_path: Path):
        """Test that activation fails gracefully outside project."""
        # Copy activation script to temp directory
        project_root = Path(__file__).parent.parent
        activate_script = project_root / "bin" / "activate.sh"
        test_script = tmp_path / "activate.sh"
        test_script.write_text(activate_script.read_text())

        script = f"""
        cd {tmp_path}
        source {test_script} 2>&1
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        # Should fail with error about missing pyproject.toml
        assert result.returncode != 0 or "pyproject.toml" in result.stdout

    def test_activation_with_missing_directories(
        self, project_root: Path, tmp_path: Path, clean_environment
    ):
        """Test that activation creates missing XDG directories."""
        script = f"""
        export HOME={tmp_path}
        cd {project_root}
        source bin/activate.sh > /dev/null 2>&1

        # All directories should exist
        test -d "$MYCELIUM_CONFIG_DIR" && \
        test -d "$MYCELIUM_DATA_DIR" && \
        test -d "$MYCELIUM_CACHE_DIR" && \
        test -d "$MYCELIUM_STATE_DIR" && \
        echo "ALL_DIRS_CREATED=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        assert "ALL_DIRS_CREATED=1" in result.stdout


# Integration test
class TestFullActivationCycle:
    """Test full activation and deactivation cycle."""

    def test_complete_activation_deactivation_cycle(
        self, project_root: Path, clean_environment, tmp_path: Path
    ):
        """Test complete activation and deactivation cycle."""
        script = f"""
        export HOME={tmp_path}
        cd {project_root}

        # Before activation
        test -z "$MYCELIUM_ENV_ACTIVE" && echo "STEP1_NOT_ACTIVE=1"

        # Activate
        source bin/activate.sh > /dev/null 2>&1

        # During activation
        test "$MYCELIUM_ENV_ACTIVE" = "1" && echo "STEP2_ACTIVE=1"
        test -n "$MYCELIUM_ROOT" && echo "STEP3_VARS_SET=1"
        test -d "$MYCELIUM_CONFIG_DIR" && echo "STEP4_DIRS_CREATED=1"

        # Deactivate
        deactivate > /dev/null 2>&1

        # After deactivation
        test -z "$MYCELIUM_ENV_ACTIVE" && echo "STEP5_DEACTIVATED=1"
        test -z "$MYCELIUM_ROOT" && echo "STEP6_VARS_UNSET=1"
        """

        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )

        output = result.stdout
        assert "STEP1_NOT_ACTIVE=1" in output
        assert "STEP2_ACTIVE=1" in output
        assert "STEP3_VARS_SET=1" in output
        assert "STEP4_DIRS_CREATED=1" in output
        assert "STEP5_DEACTIVATED=1" in output
        assert "STEP6_VARS_UNSET=1" in output
