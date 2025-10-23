# Source: skills/S1-agent-discovery-fastmcp.md
# Line: 728
# Valid syntax: True
# Has imports: False
# Has assignments: True

def test_agent_match_model():
    """Test agent match model."""
    match = AgentMatch(
        id="test-agent",
        type="test",
        name="Test Agent",
        display_name="Test Agent",
        category=AgentCategory.CORE,
        description="Test description",
        confidence=0.95,
        match_reason="Test match"
    )

    assert match.id == "test-agent"
    assert match.confidence == 0.95
    assert 0.0 <= match.confidence <= 1.0


def test_discover_agents_response_serialization():
    """Test response serialization."""
    response = DiscoverAgentsResponse(
        success=True,
        query="test",
        agents=[],
        total_count=0,
        processing_time_ms=10.5
    )

    # Serialize to dict
    data = response.model_dump()
    assert data["success"] is True
    assert data["query"] == "test"

    # Serialize to JSON
    json_str = response.model_dump_json()
    assert "test" in json_str