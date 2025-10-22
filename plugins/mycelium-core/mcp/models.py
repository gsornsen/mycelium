"""Pydantic models for MCP tool validation.

This module provides type-safe request/response models for agent discovery tools,
enabling automatic JSON schema generation and validation.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DiscoverAgentsRequest(BaseModel):
    """Request model for agent discovery."""

    query: str = Field(
        min_length=1,
        max_length=500,
        description="Natural language description of desired capabilities",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of agents to return",
    )
    threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold",
    )


class AgentMatch(BaseModel):
    """Agent match information with confidence score."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="agent_id")
    type: str = Field(alias="agent_type")
    name: str
    display_name: str
    category: str
    description: str
    capabilities: list[str]
    tools: list[str]
    keywords: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    match_reason: str
    estimated_tokens: int | None = None
    avg_response_time_ms: float | None = None


class DiscoverAgentsResponse(BaseModel):
    """Response model for agent discovery."""

    success: bool
    query: str
    agents: list[AgentMatch]
    total_count: int
    processing_time_ms: float


class GetAgentDetailsRequest(BaseModel):
    """Request model for agent details retrieval."""

    agent_id: str = Field(
        min_length=1,
        description="Agent ID or agent type",
    )


class AgentDetails(BaseModel):
    """Detailed agent information."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="agent_id")
    type: str = Field(alias="agent_type")
    name: str
    display_name: str
    category: str
    description: str
    capabilities: list[str]
    tools: list[str]
    keywords: list[str]
    file_path: str | None = None
    estimated_tokens: int | None = None
    avg_response_time_ms: float | None = None
    success_rate: float | None = None
    usage_count: int = 0
    created_at: datetime | str | None = None
    updated_at: datetime | str | None = None
    last_used_at: datetime | str | None = None


class GetAgentDetailsResponse(BaseModel):
    """Response model for agent details."""

    success: bool
    agent: AgentDetails
    metadata: dict[str, object]


class HealthCheckResponse(BaseModel):
    """Response model for health check."""

    success: bool
    status: str
    agent_count: int | None = None
    database_size: int | None = None
    pgvector_installed: bool | None = None
    timestamp: str | None = None
    error: str | None = None
