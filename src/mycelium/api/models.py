"""Pydantic models for API request/response schemas.

Defines data transfer objects for the Mycelium API.
"""


from pydantic import BaseModel, ConfigDict, Field


class AgentResponse(BaseModel):  # type: ignore[misc]
    """Agent information response model."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Agent name", examples=["backend-engineer"])
    category: str = Field(..., description="Agent category", examples=["backend"])
    status: str = Field(..., description="Agent status", examples=["healthy", "unhealthy", "starting", "stopping"])
    pid: int | None = Field(None, description="Process ID", examples=[12345])
    port: int | None = Field(None, description="Port number", examples=[8080])
    description: str | None = Field(None, description="Agent description", examples=["Backend development specialist"])
    last_heartbeat: str | None = Field(None, description="Last heartbeat timestamp (ISO 8601)")
    started_at: str | None = Field(None, description="Start timestamp (ISO 8601)")


class AgentListResponse(BaseModel):  # type: ignore[misc]
    """List of agents response model."""

    agents: list[AgentResponse] = Field(..., description="List of agents")
    count: int = Field(..., description="Total agent count", examples=[5])
    category: str | None = Field(None, description="Category filter applied", examples=["backend"])


class CategoryResponse(BaseModel):  # type: ignore[misc]
    """Category information response model."""

    name: str = Field(..., description="Category name", examples=["backend"])
    agent_count: int = Field(..., description="Number of agents in this category", examples=[3])


class CategoryListResponse(BaseModel):  # type: ignore[misc]
    """List of categories response model."""

    categories: list[CategoryResponse] = Field(..., description="List of categories")
    count: int = Field(..., description="Total category count", examples=[5])


class HealthResponse(BaseModel):  # type: ignore[misc]
    """Health check response model."""

    status: str = Field(..., description="Health status", examples=["healthy", "unhealthy"])
    registry_connected: bool = Field(..., description="Whether registry is connected")
    agent_count: int = Field(0, description="Total registered agents", examples=[5])
    active_count: int = Field(0, description="Active agents", examples=[3])


class ErrorResponse(BaseModel):  # type: ignore[misc]
    """Error response model."""

    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Detailed error information")
    suggestion: str | None = Field(None, description="Suggested action to resolve error")
