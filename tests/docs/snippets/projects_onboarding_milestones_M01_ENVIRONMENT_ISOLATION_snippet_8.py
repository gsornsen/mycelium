# Source: projects/onboarding/milestones/M01_ENVIRONMENT_ISOLATION.md
# Line: 799
# Valid syntax: True
# Has imports: True
# Has assignments: True

# tests/integration/test_environment_activation.py
import subprocess

import pytest


def test_manual_activation_full_flow(tmp_path):
    """Test complete manual activation flow."""
    # Setup mock project
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Copy activation script
    activate_script = project_dir / "bin" / "activate.sh"
    activate_script.parent.mkdir()
    # ... copy script ...

    # Run activation in subprocess
    result = subprocess.run(
        ["bash", "-c", f"source {activate_script} && env"],
        capture_output=True,
        text=True
    )

    # Verify environment variables set
    assert "MYCELIUM_ROOT" in result.stdout
    assert "MYCELIUM_CONFIG_DIR" in result.stdout
    assert "MYCELIUM_ENV_ACTIVE=1" in result.stdout


def test_direnv_activation(tmp_path):
    """Test direnv activation (if direnv installed)."""
    if not shutil.which("direnv"):
        pytest.skip("direnv not installed")

    # Setup .envrc
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    envrc = project_dir / ".envrc"
    # ... copy .envrc.template ...

    # Allow direnv
    subprocess.run(["direnv", "allow"], cwd=project_dir, check=True)

    # Verify environment
    result = subprocess.run(
        ["direnv", "exec", str(project_dir), "env"],
        capture_output=True,
        text=True
    )

    assert "MYCELIUM_ENV_ACTIVE=1" in result.stdout


def test_runtime_validation():
    """Test runtime validation catches missing environment."""
    from mycelium_onboarding.env_validator import validate_environment

    # Clear environment
    for var in os.environ.copy():
        if var.startswith("MYCELIUM_"):
            del os.environ[var]

    # Should raise error
    with pytest.raises(EnvironmentValidationError):
        validate_environment()
