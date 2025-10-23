# Source: guides/coordination-best-practices.md
# Line: 799
# Valid syntax: True
# Has imports: True
# Has assignments: True

# ✅ GOOD: Mock agents for testing
from unittest.mock import Mock, patch

def test_workflow_coordination_logic():
    # Mock agent discovery
    mock_discover = Mock(return_value={
        "agents": [
            {"id": "mock-agent-1", "confidence": 0.95},
            {"id": "mock-agent-2", "confidence": 0.90}
        ]
    })

    # Mock workflow execution
    mock_coordinate = Mock(return_value={
        "workflow_id": "test-wf-123",
        "status": "completed",
        "results": [...]
    })

    with patch('discover_agents', mock_discover):
        with patch('coordinate_workflow', mock_coordinate):
            # Test your logic
            result = my_workflow_function()
            assert result["status"] == "completed"
            mock_discover.assert_called_once()
            mock_coordinate.assert_called_once()