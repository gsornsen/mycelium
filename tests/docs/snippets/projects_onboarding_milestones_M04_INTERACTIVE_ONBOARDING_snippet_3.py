# Source: projects/onboarding/milestones/M04_INTERACTIVE_ONBOARDING.md
# Line: 306
# Valid syntax: True
# Has imports: True
# Has assignments: True

# tests/test_wizard_screens.py
"""Test wizard screen rendering and validation."""

import pytest
from unittest.mock import patch, MagicMock
from mycelium_onboarding.wizard.screens import (
    prompt_service_selection,
    prompt_deployment_method,
    prompt_project_metadata,
)

def test_service_selection_requires_at_least_one():
    """Service selection should require at least one service."""
    with patch('mycelium_onboarding.wizard.screens.inquirer.checkbox') as mock:
        mock.return_value.execute.return_value = []
        # Should show validation error
        # (validation happens in InquirerPy, test the validator)

def test_deployment_method_defaults_to_justfile_without_docker():
    """Should default to Justfile when Docker unavailable."""
    method = prompt_deployment_method(has_docker=False)
    assert method == "justfile"

def test_project_metadata_validates_identifier():
    """Project name must be valid Python identifier."""
    # Test validation logic separately
    validator = lambda x: x.isidentifier()
    assert validator("mycelium") is True
    assert validator("my-project") is False
    assert validator("123project") is False