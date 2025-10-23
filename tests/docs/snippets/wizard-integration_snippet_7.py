# Source: wizard-integration.md
# Line: 467
# Valid syntax: True
# Has imports: True
# Has assignments: True

from unittest.mock import MagicMock, patch

from mycelium_onboarding.wizard.flow import WizardState
from mycelium_onboarding.wizard.screens import WizardScreens


def test_services_screen_with_mocks():
    """Test services screen with mocked InquirerPy."""
    state = WizardState()
    screens = WizardScreens(state)

    # Mock InquirerPy
    with patch("mycelium_onboarding.wizard.screens.inquirer") as mock_inquirer:
        # Mock checkbox for service selection
        mock_inquirer.checkbox.return_value = MagicMock(
            execute=lambda: ["redis", "postgres"]
        )

        # Mock text input for database name
        mock_inquirer.text.return_value = MagicMock(
            execute=lambda: "test_db"
        )

        # Execute
        services = screens.show_services()

        # Assert
        assert services == {"redis": True, "postgres": True, "temporal": False}
        assert state.postgres_database == "test_db"

def test_wizard_flow_with_mock_detection():
    """Test complete wizard flow with mocked detection."""
    from unittest.mock import Mock

    from mycelium_onboarding.detection.orchestrator import DetectionSummary
    from mycelium_onboarding.wizard.flow import WizardFlow

    # Create mock detection
    mock_detection = Mock(spec=DetectionSummary)
    mock_detection.has_docker = True
    mock_detection.has_redis = True
    mock_detection.has_postgres = False

    # Create state
    state = WizardState()
    state.detection_results = mock_detection

    flow = WizardFlow(state)

    # Test flow can proceed with detection
    assert state.can_proceed_to(WizardStep.SERVICES)
