# Source: projects/onboarding/milestones/M04_INTERACTIVE_ONBOARDING.md
# Line: 713
# Valid syntax: True
# Has imports: True
# Has assignments: True

# tests/integration/test_wizard_flow.py
"""Integration tests for complete wizard flow."""

from unittest.mock import AsyncMock, patch

import pytest
from mycelium_onboarding.wizard.integration import run_wizard_with_detection


@pytest.mark.asyncio
async def test_complete_wizard_flow():
    """Test complete wizard flow from detection to config."""

    # Mock detection results
    mock_detection = AsyncMock(return_value=mock_detection_results())

    # Mock user inputs
    mock_inputs = {
        'service_selection': {'redis', 'temporal'},
        'deployment_method': 'docker-compose',
        'project_name': 'test-project',
        'confirm': True,
    }

    with patch('mycelium_onboarding.wizard.integration.detect_all_services', mock_detection):
        with patch_wizard_prompts(mock_inputs):
            config = await run_wizard_with_detection()

    assert config is not None
    assert config.project_name == 'test-project'
    assert config.services.redis.enabled is True
    assert config.services.temporal.enabled is True
    assert config.deployment.method == 'docker-compose'

@pytest.mark.asyncio
async def test_wizard_handles_no_docker():
    """Wizard should default to Justfile when Docker unavailable."""
    mock_detection = AsyncMock(return_value=mock_detection_results(docker_available=False))

    with patch('mycelium_onboarding.wizard.integration.detect_all_services', mock_detection):
        # ... run wizard ...
        config = await run_wizard_with_detection()

    assert config.deployment.method == 'justfile'

def test_wizard_resume_functionality():
    """Resume should load previous config and offer choices."""
    # Create previous config
    # Mock resume prompt
    # Verify correct behavior
    pass
