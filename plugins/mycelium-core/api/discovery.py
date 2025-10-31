"""Discovery API implementation using FastAPI.

This module provides RESTful endpoints for agent discovery, search,
and metadata retrieval.
"""

import json
import os
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from registry import (
    AgentNotFoundError,
    AgentRegistry,
    AgentRegistryError,
)

from .middleware import (
    PerformanceMonitoringMiddleware,
    RateLimitMiddleware,
    RequestValidationMiddleware,
)
from .models import (
    AgentDetailResponse,
    AgentMatch,
    AgentMetadata,
    AgentSearchResponse,
    DiscoverRequest,
    DiscoverResponse,
    ErrorResponse,
    HealthResponse,
)

# Global registry instance
_registry: AgentRegistry | None = None


def get_registry() -> AgentRegistry:
    """Get the global registry instance.

    Returns:
        AgentRegistry instance

    Raises:
        RuntimeError: If registry is not initialized
    """
    if _registry is None:
        raise RuntimeError("Registry not initialized")
    return _registry


def set_registry(registry: AgentRegistry | None) -> None:
    """Set the global registry instance.

    This function is primarily for testing purposes to inject a test registry.

    Args:
        registry: AgentRegistry instance or None to clear
    """
    global _registry
    _registry = registry


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager.

    Handles startup and shutdown of database connections.
    """
    global _registry

    # Startup: Initialize registry
    connection_string = os.getenv("DATABASE_URL", "postgresql://localhost:5432/mycelium_registry")

    _registry = AgentRegistry(connection_string=connection_string)
    await _registry.initialize()

    # Perform health check
    health = await _registry.health_check()
    if health["status"] != "healthy":
        raise RuntimeError(f"Registry is unhealthy: {health}")

    yield

    # Shutdown: Close registry
    if _registry is not None:
        await _registry.close()


def create_app(
    rate_limit: int = 100,
    enable_cors: bool = True,
    cors_origins: list[str] | None = None,
) -> FastAPI:
    """Create and configure FastAPI application.

    Args:
        rate_limit: Requests per minute rate limit
        enable_cors: Whether to enable CORS
        cors_origins: List of allowed CORS origins

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Mycelium Discovery API",
        description="RESTful API for agent discovery and metadata retrieval",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/v1/openapi.json",
    )

    # Add CORS middleware
    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins or ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Add custom middleware (order matters - outermost first)
    app.add_middleware(PerformanceMonitoringMiddleware)
    app.add_middleware(RequestValidationMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=rate_limit)

    # Exception handlers
    @app.exception_handler(AgentNotFoundError)
    async def agent_not_found_handler(_request: Any, exc: AgentNotFoundError) -> JSONResponse:
        """Handle agent not found errors."""
        return JSONResponse(
            status_code=404,
            content={
                "error": "AgentNotFound",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(AgentRegistryError)
    async def registry_error_handler(_request: Any, exc: AgentRegistryError) -> JSONResponse:
        """Handle registry errors."""
        return JSONResponse(
            status_code=500,
            content={
                "error": "RegistryError",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Any, exc: ValueError) -> JSONResponse:
        """Handle validation errors."""
        return JSONResponse(
            status_code=400,
            content={
                "error": "ValidationError",
                "message": str(exc),
                "details": None,
            },
        )

    # Health check endpoint
    @app.get(
        "/api/v1/health",
        response_model=HealthResponse,
        tags=["Health"],
        summary="Health check",
        description="Check API and database health status",
    )
    async def health_check() -> HealthResponse:
        """Perform health check on the API and database."""
        registry = get_registry()
        health = await registry.health_check()

        return HealthResponse(
            status=health["status"],
            pgvector_installed=health["pgvector_installed"],
            agent_count=health["agent_count"],
            database_size=health["database_size"],
            timestamp=health["timestamp"],
        )

    # Agent discovery endpoint
    @app.post(
        "/api/v1/agents/discover",
        response_model=DiscoverResponse,
        tags=["Discovery"],
        summary="Discover agents",
        description="Discover agents using natural language or keyword query",
        responses={
            200: {"description": "Successful discovery"},
            400: {"model": ErrorResponse, "description": "Invalid request"},
            500: {"model": ErrorResponse, "description": "Server error"},
        },
    )
    async def discover_agents(request: DiscoverRequest) -> DiscoverResponse:
        """Discover agents based on natural language query.

        This endpoint performs full-text search on agent descriptions,
        capabilities, keywords, and names to find relevant agents.

        Args:
            request: Discovery request with query and parameters

        Returns:
            List of matching agents with confidence scores
        """
        start_time = time.time()
        registry = get_registry()

        # Perform search using registry
        results = await registry.search_agents(
            query=request.query,
            limit=request.limit,
        )

        # Convert to response format with confidence scores
        # For now, use simple text matching for confidence
        # This will be enhanced in Task 1.3 with NLP matching
        matches: list[AgentMatch] = []
        for agent_data in results:
            # Calculate simple confidence based on keyword matches
            query_lower = request.query.lower()
            confidence = 0.0

            # Exact type match = high confidence
            if query_lower in agent_data["agent_type"].lower():
                confidence = 0.95
            # Name match
            elif query_lower in agent_data["name"].lower():
                confidence = 0.90
            # Keyword match
            elif any(query_lower in kw.lower() for kw in agent_data["keywords"]):
                confidence = 0.85
            # Description match
            elif query_lower in agent_data["description"].lower():
                confidence = 0.70
            else:
                confidence = 0.60

            # Filter by threshold
            if confidence >= request.threshold:
                # Parse metadata from JSON string
                metadata_str = agent_data.get("metadata", "{}")
                if isinstance(metadata_str, str):
                    json.loads(metadata_str)
                else:
                    pass

                agent_meta = AgentMetadata(
                    id=agent_data["id"],
                    agent_id=agent_data["agent_id"],
                    agent_type=agent_data["agent_type"],
                    name=agent_data["name"],
                    display_name=agent_data["display_name"],
                    category=agent_data["category"],
                    description=agent_data["description"],
                    capabilities=agent_data["capabilities"],
                    tools=agent_data["tools"],
                    keywords=agent_data["keywords"],
                    file_path=agent_data["file_path"],
                    estimated_tokens=agent_data.get("estimated_tokens"),
                    avg_response_time_ms=agent_data.get("avg_response_time_ms"),
                    success_rate=agent_data.get("success_rate"),
                    usage_count=agent_data.get("usage_count", 0),
                    created_at=agent_data["created_at"],
                    updated_at=agent_data["updated_at"],
                    last_used_at=agent_data.get("last_used_at"),
                )

                match = AgentMatch(
                    agent=agent_meta,
                    confidence=confidence,
                    match_reason=_get_match_reason(agent_data, query_lower),
                )
                matches.append(match)

        # Sort by confidence descending
        matches.sort(key=lambda m: m.confidence, reverse=True)

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        return DiscoverResponse(
            query=request.query,
            matches=matches,
            total_count=len(matches),
            processing_time_ms=processing_time,
        )

    # Agent search endpoint

    @app.get(
        "/api/v1/agents/search",
        response_model=AgentSearchResponse,
        tags=["Discovery"],
        summary="Search agents",
        description="Search agents with filters and full-text search",
        responses={
            200: {"description": "Search results"},
            400: {"model": ErrorResponse, "description": "Invalid request"},
            500: {"model": ErrorResponse, "description": "Server error"},
        },
    )
    async def search_agents(
        q: str | None = Query(
            None,
            description="Search query for full-text search",
            min_length=1,
            max_length=500,
        ),
        category: str | None = Query(
            None,
            description="Filter by category",
        ),
        limit: int = Query(
            10,
            ge=1,
            le=100,
            description="Maximum number of results",
        ),
        offset: int = Query(
            0,
            ge=0,
            description="Offset for pagination",
        ),
    ) -> AgentSearchResponse:
        """Search agents with optional filters.

        Args:
            q: Search query (optional)
            category: Category filter (optional)
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            List of matching agents
        """
        start_time = time.time()
        registry = get_registry()

        # If query provided, use search
        if q:
            results = await registry.search_agents(query=q, limit=limit)
            # Apply category filter if provided
            if category:
                results = [r for r in results if r["category"] == category]
        else:
            # Otherwise list with category filter
            results = await registry.list_agents(
                category=category,
                limit=limit,
                offset=offset,
            )

        # Convert to response format
        agents: list[AgentMetadata] = []
        for agent_data in results:
            agent_meta = AgentMetadata(
                id=agent_data["id"],
                agent_id=agent_data["agent_id"],
                agent_type=agent_data["agent_type"],
                name=agent_data["name"],
                display_name=agent_data["display_name"],
                category=agent_data["category"],
                description=agent_data["description"],
                capabilities=agent_data["capabilities"],
                tools=agent_data["tools"],
                keywords=agent_data["keywords"],
                file_path=agent_data["file_path"],
                estimated_tokens=agent_data.get("estimated_tokens"),
                avg_response_time_ms=agent_data.get("avg_response_time_ms"),
                success_rate=agent_data.get("success_rate"),
                usage_count=agent_data.get("usage_count", 0),
                created_at=agent_data["created_at"],
                updated_at=agent_data["updated_at"],
                last_used_at=agent_data.get("last_used_at"),
            )
            agents.append(agent_meta)

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        return AgentSearchResponse(
            query=q or "",
            agents=agents,
            total_count=len(agents),
            processing_time_ms=processing_time,
        )

    # Agent detail endpoint

    @app.get(
        "/api/v1/agents/{agent_id}",
        response_model=AgentDetailResponse,
        tags=["Discovery"],
        summary="Get agent details",
        description="Retrieve detailed information about a specific agent",
        responses={
            200: {"description": "Agent found"},
            404: {"model": ErrorResponse, "description": "Agent not found"},
            500: {"model": ErrorResponse, "description": "Server error"},
        },
    )
    async def get_agent_details(
        agent_id: str = Path(
            ...,
            description=("Agent ID (e.g., 'backend-developer' or '01-core-backend-developer')"),
            examples=["backend-developer", "01-core-backend-developer"],
        ),
    ) -> AgentDetailResponse:
        """Get detailed information about a specific agent.

        Args:
            agent_id: Agent ID or agent type

        Returns:
            Agent metadata and details

        Raises:
            HTTPException: If agent is not found
        """
        registry = get_registry()

        # Try to get by agent_id first
        try:
            agent_data = await registry.get_agent_by_id(agent_id)
        except AgentNotFoundError:
            # Try by agent_type
            try:
                agent_data = await registry.get_agent_by_type(agent_id)
            except AgentNotFoundError as e:
                raise HTTPException(
                    status_code=404,
                    detail=f"Agent with ID or type '{agent_id}' not found",
                ) from e

        # Parse metadata
        metadata_str = agent_data.get("metadata", "{}")
        metadata_dict = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str

        agent_meta = AgentMetadata(
            id=agent_data["id"],
            agent_id=agent_data["agent_id"],
            agent_type=agent_data["agent_type"],
            name=agent_data["name"],
            display_name=agent_data["display_name"],
            category=agent_data["category"],
            description=agent_data["description"],
            capabilities=agent_data["capabilities"],
            tools=agent_data["tools"],
            keywords=agent_data["keywords"],
            file_path=agent_data["file_path"],
            estimated_tokens=agent_data.get("estimated_tokens"),
            avg_response_time_ms=agent_data.get("avg_response_time_ms"),
            success_rate=agent_data.get("success_rate"),
            usage_count=agent_data.get("usage_count", 0),
            created_at=agent_data["created_at"],
            updated_at=agent_data["updated_at"],
            last_used_at=agent_data.get("last_used_at"),
        )

        return AgentDetailResponse(
            agent=agent_meta,
            metadata=metadata_dict,
        )

    return app


def _get_match_reason(agent_data: dict[str, Any], query: str) -> str:
    """Generate match reason explanation.

    Args:
        agent_data: Agent data dictionary
        query: Search query

    Returns:
        Human-readable match reason
    """
    reasons = []

    if query in agent_data["agent_type"].lower():
        reasons.append(f"exact match on agent type: {agent_data['agent_type']}")

    if query in agent_data["name"].lower():
        reasons.append(f"exact match on name: {agent_data['name']}")

    matched_keywords = [kw for kw in agent_data["keywords"] if query in kw.lower()]
    if matched_keywords:
        reasons.append(f"keyword match: {', '.join(matched_keywords[:3])}")

    if query in agent_data["description"].lower():
        reasons.append("description contains query")

    if not reasons:
        reasons.append("general relevance match")

    return "; ".join(reasons)


# Create default app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "discovery:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
