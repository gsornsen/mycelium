# Source: skills/S1-agent-discovery-fastmcp.md
# Line: 681
# Valid syntax: True
# Has imports: True
# Has assignments: True

import pytest
from pydantic import ValidationError


def test_discover_agents_request_validation():
    """Test request model validation."""

    # Valid request
    request = DiscoverAgentsRequest(
        query="Python development",
        limit=5
    )
    assert request.query == "Python development"
    assert request.limit == 5
    assert request.threshold == 0.6  # default

    # Invalid: empty query
    with pytest.raises(ValidationError):
        DiscoverAgentsRequest(query="")

    # Invalid: limit out of range
    with pytest.raises(ValidationError):
        DiscoverAgentsRequest(query="test", limit=0)

    with pytest.raises(ValidationError):
        DiscoverAgentsRequest(query="test", limit=100)

    # Invalid: threshold out of range
    with pytest.raises(ValidationError):
        DiscoverAgentsRequest(query="test", threshold=1.5)


def test_get_agent_details_request_validation():
    """Test agent details request validation."""

    # Valid request
    request = GetAgentDetailsRequest(agent_id="backend-developer")
    assert request.agent_id == "backend-developer"

    # Invalid: empty agent_id
    with pytest.raises(ValidationError):
        GetAgentDetailsRequest(agent_id="")