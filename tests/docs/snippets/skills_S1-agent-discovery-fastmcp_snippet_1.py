# Source: skills/S1-agent-discovery-fastmcp.md
# Line: 18
# Valid syntax: True
# Has imports: True
# Has assignments: True

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class AgentCategory(str, Enum):
    """Agent categories for filtering."""
    CORE = "core"
    SPECIALIZED = "specialized"
    INFRASTRUCTURE = "infrastructure"
    ANALYSIS = "analysis"
    SECURITY = "security"
    TESTING = "testing"


class DiscoverAgentsRequest(BaseModel):
    """Request model for discover_agents tool."""

    query: str = Field(
        ...,
        description="Natural language description of desired capabilities",
        min_length=1,
        max_length=500,
        examples=["Python backend development", "database optimization"]
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of agents to return"
    )

    threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold (0.0-1.0)"
    )

    category_filter: AgentCategory | None = Field(
        default=None,
        description="Optional category filter"
    )

    @field_validator('query')
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        """Ensure query is not just whitespace."""
        if not v.strip():
            raise ValueError('Query cannot be empty or whitespace')
        return v.strip()


class GetAgentDetailsRequest(BaseModel):
    """Request model for get_agent_details tool."""

    agent_id: str = Field(
        ...,
        description="Agent ID or agent type",
        min_length=1,
        examples=["backend-developer", "python-pro", "01-core-backend-developer"]
    )

    @field_validator('agent_id')
    @classmethod
    def agent_id_valid(cls, v: str) -> str:
        """Validate agent_id format."""
        if not v.strip():
            raise ValueError('agent_id cannot be empty')
        return v.strip()
