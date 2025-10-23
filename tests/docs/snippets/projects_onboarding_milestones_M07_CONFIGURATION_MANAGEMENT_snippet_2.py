# Source: projects/onboarding/milestones/M07_CONFIGURATION_MANAGEMENT.md
# Line: 226
# Valid syntax: True
# Has imports: True
# Has assignments: True

# tests/test_config_show.py
"""Tests for config show command."""

import pytest
from click.testing import CliRunner
from mycelium_onboarding.cli.config import show

def test_show_table_format(tmp_config):
    """Show command should display table format."""
    runner = CliRunner()
    result = runner.invoke(show, ['--format', 'table'])

    assert result.exit_code == 0
    assert 'Project Configuration' in result.output

def test_show_yaml_format(tmp_config):
    """Show command should display YAML format."""
    runner = CliRunner()
    result = runner.invoke(show, ['--format', 'yaml'])

    assert result.exit_code == 0
    assert 'project_name:' in result.output

def test_show_masks_sensitive_data(tmp_config_with_password):
    """Sensitive data should be masked."""
    runner = CliRunner()
    result = runner.invoke(show, ['--format', 'yaml'])

    assert '***REDACTED***' in result.output
    assert 'actual_password' not in result.output

def test_show_path_only():
    """Show --path should only display config path."""
    runner = CliRunner()
    result = runner.invoke(show, ['--path'])

    assert result.exit_code == 0
    assert 'mycelium.yaml' in result.output