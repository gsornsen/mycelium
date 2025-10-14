"""Tests for CLI configuration commands.

This module tests all configuration management CLI commands using Click's
testing framework (CliRunner) to ensure robust command-line interface.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml
from click.testing import CliRunner

from mycelium_onboarding.cli import cli
from mycelium_onboarding.config.manager import ConfigManager
from mycelium_onboarding.config.schema import MyceliumConfig


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory."""
    config_dir = tmp_path / ".config" / "mycelium"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def temp_config_file(temp_config_dir):
    """Create temporary config file with default configuration."""
    config_path = temp_config_dir / "config.yaml"
    config = MyceliumConfig()
    yaml_content = config.to_yaml()
    config_path.write_text(yaml_content)
    return config_path


# ============================================================================
# Test 'config show' command
# ============================================================================


def test_config_show_default(runner, tmp_path):
    """Test 'config show' with default configuration."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["config", "show"])

        assert result.exit_code == 0
        assert "Configuration:" in result.output
        assert "mycelium" in result.output or "using defaults" in result.output


def test_config_show_yaml_format(runner, temp_config_file):
    """Test 'config show' with YAML format."""
    result = runner.invoke(
        cli,
        ["config", "show", "--path", str(temp_config_file), "--format", "yaml"],
    )

    assert result.exit_code == 0
    assert "version:" in result.output
    assert "services:" in result.output
    assert "deployment:" in result.output


def test_config_show_json_format(runner, temp_config_file):
    """Test 'config show' with JSON format."""
    result = runner.invoke(
        cli,
        ["config", "show", "--path", str(temp_config_file), "--format", "json"],
    )

    assert result.exit_code == 0
    # Verify it's valid JSON
    try:
        data = json.loads(result.output.split("\n\n")[1])  # Skip location line
        assert "version" in data
        assert "services" in data
    except (json.JSONDecodeError, IndexError):
        # Output might include location info, try parsing from output
        json_start = result.output.find("{")
        if json_start != -1:
            data = json.loads(result.output[json_start:])
            assert "version" in data


def test_config_show_table_format(runner, temp_config_file):
    """Test 'config show' with table format."""
    result = runner.invoke(
        cli,
        ["config", "show", "--path", str(temp_config_file), "--format", "table"],
    )

    assert result.exit_code == 0
    assert "Configuration" in result.output
    assert "General:" in result.output
    assert "Services:" in result.output
    assert "Redis:" in result.output
    assert "PostgreSQL:" in result.output


def test_config_show_nonexistent_path(runner, tmp_path):
    """Test 'config show' with nonexistent file path."""
    nonexistent = tmp_path / "nonexistent.yaml"
    result = runner.invoke(cli, ["config", "show", "--path", str(nonexistent)])

    assert result.exit_code != 0
    # Should fail because --path requires exists=True


def test_config_show_invalid_format(runner):
    """Test 'config show' with invalid format."""
    result = runner.invoke(cli, ["config", "show", "--format", "invalid"])

    assert result.exit_code != 0
    assert "Invalid value" in result.output or "invalid" in result.output.lower()


# ============================================================================
# Test 'config init' command
# ============================================================================


def test_config_init_default(runner, tmp_path, monkeypatch):
    """Test 'config init' creates default configuration."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Mock get_config_path to use temp directory
        config_path = tmp_path / "config.yaml"

        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            result = runner.invoke(cli, ["config", "init"])

        assert result.exit_code == 0
        assert "Created configuration" in result.output


def test_config_init_with_output(runner, tmp_path):
    """Test 'config init' with custom output path."""
    output_path = tmp_path / "custom-config.yaml"

    result = runner.invoke(cli, ["config", "init", "--output", str(output_path)])

    assert result.exit_code == 0
    assert output_path.exists()
    assert "Created configuration" in result.output

    # Verify file contents
    config = yaml.safe_load(output_path.read_text())
    assert "version" in config
    assert config["project_name"] == "mycelium"


def test_config_init_project_local(runner, tmp_path, monkeypatch):
    """Test 'config init --project-local'."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        config_path = tmp_path / "config.yaml"

        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            result = runner.invoke(cli, ["config", "init", "--project-local"])

        assert result.exit_code == 0
        assert "Created configuration" in result.output


def test_config_init_already_exists(runner, temp_config_file):
    """Test 'config init' when file already exists."""
    result = runner.invoke(
        cli,
        ["config", "init", "--output", str(temp_config_file)],
    )

    assert result.exit_code != 0
    assert "already exists" in result.output


def test_config_init_force_overwrite(runner, temp_config_file):
    """Test 'config init --force' overwrites existing file."""
    result = runner.invoke(
        cli,
        ["config", "init", "--output", str(temp_config_file), "--force"],
        input="y\n",  # Confirm overwrite
    )

    assert result.exit_code == 0
    assert "Created configuration" in result.output


def test_config_init_force_cancel(runner, temp_config_file):
    """Test 'config init --force' can be cancelled."""
    result = runner.invoke(
        cli,
        ["config", "init", "--output", str(temp_config_file), "--force"],
        input="n\n",  # Cancel overwrite
    )

    assert result.exit_code == 0
    assert "Cancelled" in result.output


# ============================================================================
# Test 'config get' command
# ============================================================================


def test_config_get_top_level(runner, temp_config_file):
    """Test 'config get' for top-level key."""
    result = runner.invoke(
        cli,
        ["config", "get", "project_name", "--path", str(temp_config_file)],
    )

    assert result.exit_code == 0
    assert "project_name" in result.output
    assert "mycelium" in result.output


def test_config_get_nested(runner, temp_config_file):
    """Test 'config get' for nested key."""
    result = runner.invoke(
        cli,
        ["config", "get", "services.redis.port", "--path", str(temp_config_file)],
    )

    assert result.exit_code == 0
    assert "services.redis.port" in result.output
    assert "6379" in result.output


def test_config_get_deployment_method(runner, temp_config_file):
    """Test 'config get' for deployment method."""
    result = runner.invoke(
        cli,
        ["config", "get", "deployment.method", "--path", str(temp_config_file)],
    )

    assert result.exit_code == 0
    assert "deployment.method" in result.output
    assert "docker-compose" in result.output


def test_config_get_nonexistent_key(runner, temp_config_file):
    """Test 'config get' with nonexistent key."""
    result = runner.invoke(
        cli,
        ["config", "get", "nonexistent.key", "--path", str(temp_config_file)],
    )

    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_config_get_invalid_nested_key(runner, temp_config_file):
    """Test 'config get' with invalid nested key path."""
    result = runner.invoke(
        cli,
        ["config", "get", "services.invalid.key", "--path", str(temp_config_file)],
    )

    assert result.exit_code != 0
    assert "not found" in result.output.lower()


# ============================================================================
# Test 'config set' command
# ============================================================================


def test_config_set_integer(runner, tmp_path):
    """Test 'config set' with integer value."""
    config_path = tmp_path / "config.yaml"

    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize config first
        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            runner.invoke(cli, ["config", "init"])

        # Set value
        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            result = runner.invoke(
                cli,
                ["config", "set", "services.redis.port", "6380"],
            )

    assert result.exit_code == 0
    assert "Set services.redis.port = 6380" in result.output

    # Verify value was saved
    config = yaml.safe_load(config_path.read_text())
    assert config["services"]["redis"]["port"] == 6380


def test_config_set_boolean(runner, tmp_path):
    """Test 'config set' with boolean value."""
    config_path = tmp_path / "config.yaml"

    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize config first
        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            runner.invoke(cli, ["config", "init"])

        # Set boolean to false
        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            result = runner.invoke(
                cli,
                ["config", "set", "services.redis.enabled", "false"],
            )

    assert result.exit_code == 0
    assert "Set services.redis.enabled = False" in result.output

    # Verify value was saved
    config = yaml.safe_load(config_path.read_text())
    assert config["services"]["redis"]["enabled"] is False


def test_config_set_string(runner, tmp_path):
    """Test 'config set' with string value."""
    config_path = tmp_path / "config.yaml"

    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize config first
        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            runner.invoke(cli, ["config", "init"])

        # Set string value
        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            result = runner.invoke(
                cli,
                ["config", "set", "project_name", "my-project"],
            )

    assert result.exit_code == 0
    assert "Set project_name = my-project" in result.output

    # Verify value was saved
    config = yaml.safe_load(config_path.read_text())
    assert config["project_name"] == "my-project"


def test_config_set_invalid_value(runner, tmp_path):
    """Test 'config set' with invalid value causes validation error."""
    config_path = tmp_path / "config.yaml"

    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize config first
        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            runner.invoke(cli, ["config", "init"])

        # Try to set invalid port (exit code should be 1 or 2)
        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            result = runner.invoke(
                cli,
                ["config", "set", "services.redis.port", "99999"],
            )

    assert result.exit_code in (1, 2)  # Either error or validation error
    assert "validation" in result.output.lower() or "error" in result.output.lower()


def test_config_set_nonexistent_key(runner, tmp_path):
    """Test 'config set' with nonexistent key."""
    config_path = tmp_path / "config.yaml"

    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize config first
        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            runner.invoke(cli, ["config", "init"])

        # Try to set nonexistent key
        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            result = runner.invoke(
                cli,
                ["config", "set", "nonexistent.key", "value"],
            )

    # Should fail validation
    assert result.exit_code != 0


def test_config_set_project_local(runner, tmp_path):
    """Test 'config set' with --project-local flag."""
    config_path = tmp_path / "config.yaml"

    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize config first
        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            runner.invoke(cli, ["config", "init"])

        # Set with project-local flag
        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            result = runner.invoke(
                cli,
                ["config", "set", "project_name", "local-project", "--project-local"],
            )

    assert result.exit_code == 0
    assert "local-project" in result.output


# ============================================================================
# Test 'config validate' command
# ============================================================================


def test_config_validate_valid(runner, temp_config_file):
    """Test 'config validate' with valid configuration."""
    result = runner.invoke(
        cli,
        ["config", "validate", "--path", str(temp_config_file)],
    )

    assert result.exit_code == 0
    assert "Configuration valid" in result.output
    assert "Configuration Summary:" in result.output
    assert "Project:" in result.output


def test_config_validate_shows_summary(runner, temp_config_file):
    """Test 'config validate' displays configuration summary."""
    result = runner.invoke(
        cli,
        ["config", "validate", "--path", str(temp_config_file)],
    )

    assert result.exit_code == 0
    assert "Schema Version:" in result.output
    assert "Deployment:" in result.output
    assert "Enabled Services:" in result.output


def test_config_validate_invalid(runner, tmp_path):
    """Test 'config validate' with invalid configuration."""
    config_path = tmp_path / "invalid-config.yaml"

    # Create invalid config (missing required service)
    invalid_config = {
        "version": "1.0",
        "project_name": "test",
        "services": {
            "redis": {"enabled": False},
            "postgres": {"enabled": False},
            "temporal": {"enabled": False},
        },
    }

    config_path.write_text(yaml.dump(invalid_config))

    result = runner.invoke(cli, ["config", "validate", "--path", str(config_path)])

    assert result.exit_code == 2  # Validation error
    assert "invalid" in result.output.lower() or "error" in result.output.lower()


def test_config_validate_malformed_yaml(runner, tmp_path):
    """Test 'config validate' with malformed YAML."""
    config_path = tmp_path / "malformed.yaml"
    config_path.write_text("invalid: yaml: content:\n  - bad\n    - worse")

    result = runner.invoke(cli, ["config", "validate", "--path", str(config_path)])

    assert result.exit_code != 0


def test_config_validate_default(runner, tmp_path):
    """Test 'config validate' without path (uses default)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["config", "validate"])

        # Should validate default config
        assert result.exit_code == 0
        assert "Configuration valid" in result.output or "using defaults" in result.output.lower()


# ============================================================================
# Test help output
# ============================================================================


def test_config_help(runner):
    """Test 'config --help' displays help."""
    result = runner.invoke(cli, ["config", "--help"])

    assert result.exit_code == 0
    assert "Configuration management commands" in result.output
    assert "show" in result.output
    assert "init" in result.output
    assert "get" in result.output
    assert "set" in result.output
    assert "validate" in result.output


def test_config_show_help(runner):
    """Test 'config show --help' displays command help."""
    result = runner.invoke(cli, ["config", "show", "--help"])

    assert result.exit_code == 0
    assert "Display current configuration" in result.output
    assert "--format" in result.output
    assert "--path" in result.output


def test_config_get_help(runner):
    """Test 'config get --help' displays command help."""
    result = runner.invoke(cli, ["config", "get", "--help"])

    assert result.exit_code == 0
    assert "Get configuration value" in result.output
    assert "dot notation" in result.output


def test_config_set_help(runner):
    """Test 'config set --help' displays command help."""
    result = runner.invoke(cli, ["config", "set", "--help"])

    assert result.exit_code == 0
    assert "Set configuration value" in result.output
    assert "--project-local" in result.output


# ============================================================================
# Test error handling
# ============================================================================


def test_config_show_with_load_error(runner, tmp_path, monkeypatch):
    """Test 'config show' handles ConfigLoadError gracefully."""
    config_path = tmp_path / "config.yaml"

    with patch("mycelium_onboarding.cli.ConfigManager") as mock_manager:
        mock_manager.return_value.load.side_effect = Exception("Load failed")

        result = runner.invoke(cli, ["config", "show"])

        assert result.exit_code != 0
        assert "Error" in result.output


def test_config_set_with_save_error(runner, tmp_path):
    """Test 'config set' handles ConfigSaveError gracefully."""
    config_path = tmp_path / "config.yaml"

    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize config
        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            runner.invoke(cli, ["config", "init"])

        # Make directory read-only to cause save error
        config_path.parent.chmod(0o444)

        try:
            with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
                result = runner.invoke(
                    cli,
                    ["config", "set", "project_name", "test"],
                )

            assert result.exit_code != 0
        finally:
            # Restore permissions
            config_path.parent.chmod(0o755)


# ============================================================================
# Test helper functions
# ============================================================================


def test_parse_value_boolean():
    """Test _parse_value correctly parses boolean values."""
    from mycelium_onboarding.cli import _parse_value

    assert _parse_value("true") is True
    assert _parse_value("True") is True
    assert _parse_value("yes") is True
    assert _parse_value("1") is True

    assert _parse_value("false") is False
    assert _parse_value("False") is False
    assert _parse_value("no") is False
    assert _parse_value("0") is False


def test_parse_value_integer():
    """Test _parse_value correctly parses integer values."""
    from mycelium_onboarding.cli import _parse_value

    assert _parse_value("42") == 42
    assert _parse_value("-10") == -10
    assert _parse_value("0") is False  # Special case: "0" is boolean False


def test_parse_value_float():
    """Test _parse_value correctly parses float values."""
    from mycelium_onboarding.cli import _parse_value

    assert _parse_value("3.14") == 3.14
    assert _parse_value("-2.5") == -2.5


def test_parse_value_string():
    """Test _parse_value returns string for non-numeric values."""
    from mycelium_onboarding.cli import _parse_value

    assert _parse_value("hello") == "hello"
    assert _parse_value("docker-compose") == "docker-compose"
    assert _parse_value("256mb") == "256mb"


def test_get_nested_value():
    """Test _get_nested_value retrieves nested dictionary values."""
    from mycelium_onboarding.cli import _get_nested_value

    data = {
        "level1": {
            "level2": {
                "level3": "value"
            }
        }
    }

    assert _get_nested_value(data, "level1.level2.level3") == "value"
    assert _get_nested_value(data, "level1.level2") == {"level3": "value"}


def test_get_nested_value_missing_key():
    """Test _get_nested_value raises KeyError for missing keys."""
    from mycelium_onboarding.cli import _get_nested_value

    data = {"key1": {"key2": "value"}}

    with pytest.raises(KeyError):
        _get_nested_value(data, "key1.missing")


def test_set_nested_value():
    """Test _set_nested_value sets nested dictionary values."""
    from mycelium_onboarding.cli import _set_nested_value

    data = {"level1": {"level2": {}}}

    _set_nested_value(data, "level1.level2.level3", "new_value")

    assert data["level1"]["level2"]["level3"] == "new_value"


def test_set_nested_value_creates_path():
    """Test _set_nested_value creates missing intermediate keys."""
    from mycelium_onboarding.cli import _set_nested_value

    data = {}

    _set_nested_value(data, "a.b.c", "value")

    assert data == {"a": {"b": {"c": "value"}}}


# ============================================================================
# Integration tests
# ============================================================================


def test_config_workflow_init_get_set_validate(runner, tmp_path):
    """Test complete configuration workflow."""
    config_path = tmp_path / "config.yaml"

    with runner.isolated_filesystem(temp_dir=tmp_path):
        # 1. Initialize configuration
        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            result = runner.invoke(cli, ["config", "init"])
        assert result.exit_code == 0

        # 2. Get initial value (directly from file)
        result = runner.invoke(cli, ["config", "get", "services.redis.port", "--path", str(config_path)])
        assert result.exit_code == 0
        assert "6379" in result.output

        # 3. Set new value
        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            result = runner.invoke(
                cli,
                ["config", "set", "services.redis.port", "6380"],
            )
        assert result.exit_code == 0

        # 4. Verify new value (directly from file)
        result = runner.invoke(cli, ["config", "get", "services.redis.port", "--path", str(config_path)])
        assert result.exit_code == 0
        assert "6380" in result.output

        # 5. Validate configuration
        result = runner.invoke(cli, ["config", "validate", "--path", str(config_path)])
        assert result.exit_code == 0


def test_config_multiple_sets(runner, tmp_path):
    """Test setting multiple configuration values."""
    config_path = tmp_path / "config.yaml"

    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Initialize
        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            runner.invoke(cli, ["config", "init"])

        # Set multiple values
        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            runner.invoke(cli, ["config", "set", "project_name", "test-project"])

        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            runner.invoke(cli, ["config", "set", "services.redis.port", "6380"])

        with patch("mycelium_onboarding.cli.get_config_path", return_value=config_path):
            runner.invoke(cli, ["config", "set", "services.postgres.database", "testdb"])

        # Verify all values
        config = yaml.safe_load(config_path.read_text())
        assert config["project_name"] == "test-project"
        assert config["services"]["redis"]["port"] == 6380
        assert config["services"]["postgres"]["database"] == "testdb"
