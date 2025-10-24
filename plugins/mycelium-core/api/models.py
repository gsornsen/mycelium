"""Pydantic models for Discovery API request/response validation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class DiscoverRequest(BaseModel):
    """Request model for agent discovery endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural language or structured query for agent discovery",
        examples=["python backend development", "secure API authentication"],
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of agents to return",
    )
    threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for matches (0.0-1.0)",
    )

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        """Validate query is not just whitespace."""
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()


class AgentMetadata(BaseModel):
    """Agent metadata model."""

    id: UUID = Field(description="Agent UUID")
    agent_id: str = Field(description="Unique agent identifier")
    agent_type: str = Field(description="Agent type/name")
    name: str = Field(description="Agent name")
    display_name: str = Field(description="Display name for UI")
    category: str = Field(description="Agent category")
    description: str = Field(description="Agent description")
    capabilities: list[str] = Field(
        default_factory=list, description="List of agent capabilities"
    )
    tools: list[str] = Field(default_factory=list, description="Available tools")
    keywords: list[str] = Field(default_factory=list, description="Search keywords")
    file_path: str = Field(description="Path to agent definition file")
    estimated_tokens: int | None = Field(
        default=None, description="Estimated token count"
    )
    avg_response_time_ms: float | None = Field(
        default=None, description="Average response time in milliseconds"
    )
    success_rate: float | None = Field(
        default=None, description="Success rate (0.0-1.0)"
    )
    usage_count: int = Field(default=0, description="Usage count")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    last_used_at: datetime | None = Field(
        default=None, description="Last usage timestamp"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "agent_id": "01-core-backend-developer",
                "agent_type": "backend-developer",
                "name": "backend-developer",
                "display_name": "Backend Developer",
                "category": "Development",
                "description": "Expert in backend development with Node.js, Python, and Go",
                "capabilities": [
                    "RESTful API design",
                    "Database optimization",
                    "Authentication implementation",
                ],
                "tools": ["database", "docker", "postgresql"],
                "keywords": ["backend", "api", "database", "python", "nodejs"],
                "file_path": "plugins/mycelium-core/agents/01-core-backend-developer.md",
                "estimated_tokens": 2500,
                "avg_response_time_ms": 150.5,
                "success_rate": 0.95,
                "usage_count": 42,
                "created_at": "2025-10-20T10:00:00Z",
                "updated_at": "2025-10-21T15:30:00Z",
                "last_used_at": "2025-10-21T14:00:00Z",
            }
        }


class AgentMatch(BaseModel):
    """Agent match with confidence score."""

    agent: AgentMetadata
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence score for this match (0.0-1.0)"
    )
    match_reason: str | None = Field(
        default=None, description="Explanation of why this agent was matched"
    )


class DiscoverResponse(BaseModel):
    """Response model for agent discovery endpoint."""

    query: str = Field(description="Original query")
    matches: list[AgentMatch] = Field(
        description="List of matching agents with confidence scores"
    )
    total_count: int = Field(description="Total number of matches found")
    processing_time_ms: float = Field(
        description="Processing time in milliseconds"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "query": "python backend development",
                "matches": [
                    {
                        "agent": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "agent_id": "01-core-backend-developer",
                            "agent_type": "backend-developer",
                            "name": "backend-developer",
                            "display_name": "Backend Developer",
                            "category": "Development",
                            "description": "Expert in backend development",
                            "capabilities": ["API design", "Database optimization"],
                            "tools": ["database", "docker"],
                            "keywords": ["backend", "api", "python"],
                            "file_path": "plugins/mycelium-core/agents/01-core-backend-developer.md",
                            "estimated_tokens": 2500,
                            "avg_response_time_ms": 150.5,
                            "success_rate": 0.95,
                            "usage_count": 42,
                            "created_at": "2025-10-20T10:00:00Z",
                            "updated_at": "2025-10-21T15:30:00Z",
                            "last_used_at": "2025-10-21T14:00:00Z",
                        },
                        "confidence": 0.92,
                        "match_reason": "Exact match on keywords: backend, python",
                    }
                ],
                "total_count": 1,
                "processing_time_ms": 45.3,
            }
        }


class AgentDetailResponse(BaseModel):
    """Response model for agent detail endpoint."""

    agent: AgentMetadata
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "agent": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "agent_id": "01-core-backend-developer",
                    "agent_type": "backend-developer",
                    "name": "backend-developer",
                    "display_name": "Backend Developer",
                    "category": "Development",
                    "description": "Expert in backend development",
                    "capabilities": ["API design"],
                    "tools": ["database"],
                    "keywords": ["backend"],
                    "file_path": "plugins/mycelium-core/agents/01-core-backend-developer.md",
                    "estimated_tokens": 2500,
                    "created_at": "2025-10-20T10:00:00Z",
                    "updated_at": "2025-10-21T15:30:00Z",
                },
                "metadata": {"version": "1.0.0"},
            }
        }


class AgentSearchResponse(BaseModel):
    """Response model for agent search endpoint."""

    query: str = Field(description="Search query")
    agents: list[AgentMetadata] = Field(description="List of matching agents")
    total_count: int = Field(description="Total number of results")
    processing_time_ms: float = Field(
        description="Processing time in milliseconds"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "query": "security",
                "agents": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "agent_id": "03-security-expert",
                        "agent_type": "security-expert",
                        "name": "security-expert",
                        "display_name": "Security Expert",
                        "category": "Security",
                        "description": "Security analysis and vulnerability assessment",
                        "capabilities": ["Security audit", "Vulnerability scanning"],
                        "tools": ["security-scanner"],
                        "keywords": ["security", "audit"],
                        "file_path": "plugins/mycelium-core/agents/03-security-expert.md",
                        "estimated_tokens": 2000,
                        "created_at": "2025-10-20T10:00:00Z",
                        "updated_at": "2025-10-21T15:30:00Z",
                    }
                ],
                "total_count": 1,
                "processing_time_ms": 35.2,
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(description="Error type")
    message: str = Field(description="Human-readable error message")
    details: dict[str, Any] | None = Field(
        default=None, description="Additional error details"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Query must be at least 1 character long",
                "details": {"field": "query", "constraint": "min_length"},
            }
        }


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(description="Health status (healthy/unhealthy)")
    pgvector_installed: bool = Field(description="Whether pgvector is installed")
    agent_count: int = Field(description="Total number of agents in registry")
    database_size: str = Field(description="Database size")
    timestamp: str = Field(description="Health check timestamp")
    version: str = Field(default="1.0.0", description="API version")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "status": "healthy",
                "pgvector_installed": True,
                "agent_count": 130,
                "database_size": "42 MB",
                "timestamp": "2025-10-21T15:30:00Z",
                "version": "1.0.0",
            }
        }
