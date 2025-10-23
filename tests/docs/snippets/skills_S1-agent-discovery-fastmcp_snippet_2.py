# Source: skills/S1-agent-discovery-fastmcp.md
# Line: 93
# Valid syntax: True
# Has imports: True
# Has assignments: True

from datetime import datetime


class AgentMatch(BaseModel):
    """Single agent match result."""

    id: str = Field(..., description="Agent identifier")
    type: str = Field(..., description="Agent type")
    name: str = Field(..., description="Agent display name")
    display_name: str = Field(..., description="Formatted display name")
    category: AgentCategory = Field(..., description="Agent category")
    description: str = Field(..., description="Agent description")

    capabilities: list[str] = Field(
        default_factory=list,
        description="Agent capabilities"
    )

    tools: list[str] = Field(
        default_factory=list,
        description="Tools the agent uses"
    )

    keywords: list[str] = Field(
        default_factory=list,
        description="Keywords for matching"
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Match confidence score"
    )

    match_reason: str = Field(
        ...,
        description="Explanation of why agent matched"
    )

    estimated_tokens: int = Field(
        default=0,
        ge=0,
        description="Estimated token count for agent"
    )

    avg_response_time_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Average response time in milliseconds"
    )


class DiscoverAgentsResponse(BaseModel):
    """Response model for discover_agents tool."""

    success: bool = Field(default=True, description="Request success status")
    query: str = Field(..., description="Original query")

    agents: list[AgentMatch] = Field(
        default_factory=list,
        description="Matching agents"
    )

    total_count: int = Field(
        ...,
        ge=0,
        description="Total number of matches"
    )

    processing_time_ms: float = Field(
        ...,
        ge=0.0,
        description="Processing time in milliseconds"
    )


class AgentDetailsMetadata(BaseModel):
    """Agent metadata."""

    dependencies: list[str] = Field(
        default_factory=list,
        description="Agent dependencies"
    )

    examples: list[str] = Field(
        default_factory=list,
        description="Example use cases"
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Additional tags"
    )


class AgentDetails(BaseModel):
    """Detailed agent information."""

    id: str
    type: str
    name: str
    display_name: str
    category: AgentCategory
    description: str
    capabilities: list[str]
    tools: list[str]
    keywords: list[str]

    file_path: str = Field(..., description="Path to agent definition file")
    estimated_tokens: int
    avg_response_time_ms: float

    success_rate: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Historical success rate"
    )

    usage_count: int = Field(
        default=0,
        ge=0,
        description="Number of times agent has been used"
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Agent creation timestamp"
    )

    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )

    last_used_at: datetime | None = Field(
        default=None,
        description="Last usage timestamp"
    )


class GetAgentDetailsResponse(BaseModel):
    """Response model for get_agent_details tool."""

    success: bool = Field(default=True)
    agent: AgentDetails = Field(..., description="Agent details")
    metadata: AgentDetailsMetadata = Field(
        default_factory=AgentDetailsMetadata,
        description="Additional metadata"
    )
