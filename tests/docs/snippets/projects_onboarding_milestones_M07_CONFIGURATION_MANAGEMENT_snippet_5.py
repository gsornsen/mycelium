# Source: projects/onboarding/milestones/M07_CONFIGURATION_MANAGEMENT.md
# Line: 482
# Valid syntax: True
# Has imports: False
# Has assignments: True

# tests/test_config_validate.py
"""Tests for config validate command."""

def test_validate_success(tmp_valid_config):
    """Validate should pass for valid configuration."""
    runner = CliRunner()
    result = runner.invoke(validate)

    assert result.exit_code == 0
    assert '✓ Configuration is valid' in result.output

def test_validate_detects_warnings(tmp_config_with_warnings):
    """Validate should show warnings."""
    runner = CliRunner()
    result = runner.invoke(validate)

    assert result.exit_code == 0
    assert '⚠' in result.output

def test_validate_strict_fails_on_warnings(tmp_config_with_warnings):
    """Validate --strict should fail on warnings."""
    runner = CliRunner()
    result = runner.invoke(validate, ['--strict'])

    assert result.exit_code != 0

def test_validate_invalid_config(tmp_invalid_config):
    """Validate should fail for invalid configuration."""
    runner = CliRunner()
    result = runner.invoke(validate)

    assert result.exit_code != 0
    assert 'Validation failed' in result.output
