# Source: wizard-integration.md
# Line: 700
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Test with realistic mock data
mock_detection = Mock(spec=DetectionSummary)
mock_detection.has_docker = True
mock_detection.docker = Mock(version="24.0.0")

# Test error paths
def test_validation_failure():
    state = WizardState()
    state.project_name = ""  # Invalid
    validator = WizardValidator(state)
    assert not validator.validate_state()
