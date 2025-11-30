"""FastAPI application with routes and middleware.

Main application factory for the Mycelium REST API.
Includes rate limiting and security configurations.
"""

from collections import defaultdict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from mycelium.api.models import (
    AgentListResponse,
    AgentResponse,
    CategoryListResponse,
    CategoryResponse,
    ErrorResponse,
    HealthResponse,
)
from mycelium.errors import MyceliumError
from mycelium.registry.client import RegistryClient

# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address, default_limits=["100/second"])


def create_app(redis_url: str = "redis://localhost:6379") -> FastAPI:
    """Create FastAPI application instance.

    Args:
        redis_url: Redis connection URL for registry

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Mycelium API",
        description="RESTful API for Mycelium multi-agent orchestration platform",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Add rate limiting state
    app.state.limiter = limiter

    # Add rate limit exceeded handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS configuration - restrict to localhost origins only
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost",
            "http://localhost:8080",
            "http://127.0.0.1",
            "http://127.0.0.1:8080",
        ],
        allow_credentials=True,
        allow_methods=["GET"],  # Only GET methods for status API
        allow_headers=["*"],
    )

    # Initialize registry client
    registry = RegistryClient(redis_url=redis_url)

    # Custom exception handler for MyceliumError
    @app.exception_handler(MyceliumError)
    async def mycelium_error_handler(request: Request, exc: MyceliumError) -> JSONResponse:
        """Handle MyceliumError exceptions."""
        return JSONResponse(
            status_code=500,
            content={
                "error": str(exc),
                "suggestion": getattr(exc, "suggestion", None),
                "detail": getattr(exc, "debug_info", None),
            },
        )

    # Health check endpoint (no rate limiting for health checks)
    @app.get(
        "/api/v1/health",
        response_model=HealthResponse,
        tags=["Health"],
        summary="Health check endpoint",
        description="Check if the API and registry are healthy",
    )
    async def health() -> HealthResponse:
        """Health check endpoint.

        Returns:
            Health status including registry connection and agent counts
        """
        try:
            is_healthy = registry.health_check()

            if is_healthy:
                stats = registry.get_stats()
                return HealthResponse(
                    status="healthy",
                    registry_connected=True,
                    agent_count=stats.get("agent_count", 0),
                    active_count=stats.get("active_count", 0),
                )
            return HealthResponse(
                status="unhealthy",
                registry_connected=False,
            )
        except Exception:
            return HealthResponse(
                status="unhealthy",
                registry_connected=False,
            )

    # List agents endpoint (with rate limiting)
    @app.get(
        "/api/v1/agents",
        response_model=AgentListResponse,
        tags=["Agents"],
        summary="List all agents",
        description="Get a list of all registered agents, optionally filtered by category",
    )
    @limiter.limit("100/second")
    async def list_agents(request: Request, category: str | None = None) -> AgentListResponse:
        """List all registered agents.

        Args:
            _request: FastAPI request object (required for rate limiting)
            category: Optional category filter

        Returns:
            List of agents with metadata

        Raises:
            HTTPException: If registry is unavailable
        """
        try:
            agents = registry.list_agents(category=category)
            agent_responses = [
                AgentResponse(
                    name=agent.name,
                    category=agent.category,
                    status=agent.status,
                    pid=agent.pid,
                    port=agent.port,
                    description=agent.description,
                    last_heartbeat=agent.last_heartbeat,
                    started_at=agent.started_at,
                )
                for agent in agents
            ]

            return AgentListResponse(
                agents=agent_responses,
                count=len(agent_responses),
                category=category,
            )
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Registry unavailable: {str(e)}",
            ) from None

    # Get agent details endpoint (with rate limiting)
    @app.get(
        "/api/v1/agents/{name}",
        response_model=AgentResponse,
        tags=["Agents"],
        summary="Get agent details",
        description="Get detailed information about a specific agent by name",
        responses={
            404: {
                "model": ErrorResponse,
                "description": "Agent not found",
            }
        },
    )
    @limiter.limit("100/second")
    async def get_agent(request: Request, name: str) -> AgentResponse:
        """Get agent details by name.

        Args:
            _request: FastAPI request object (required for rate limiting)
            name: Agent name

        Returns:
            Agent details

        Raises:
            HTTPException: If agent not found or registry unavailable
        """
        try:
            agent = registry.get_agent(name)

            if not agent:
                raise HTTPException(
                    status_code=404,
                    detail=f"Agent '{name}' not found",
                )

            return AgentResponse(
                name=agent.name,
                category=agent.category,
                status=agent.status,
                pid=agent.pid,
                port=agent.port,
                description=agent.description,
                last_heartbeat=agent.last_heartbeat,
                started_at=agent.started_at,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Registry unavailable: {str(e)}",
            ) from None

    # List categories endpoint (with rate limiting)
    @app.get(
        "/api/v1/categories",
        response_model=CategoryListResponse,
        tags=["Categories"],
        summary="List all categories",
        description="Get a list of all agent categories with counts",
    )
    @limiter.limit("100/second")
    async def list_categories(request: Request) -> CategoryListResponse:
        """List all agent categories.

        Args:
            _request: FastAPI request object (required for rate limiting)

        Returns:
            List of categories with agent counts

        Raises:
            HTTPException: If registry is unavailable
        """
        try:
            agents = registry.list_agents()

            # Count agents per category
            category_counts: dict[str, int] = defaultdict(int)
            for agent in agents:
                category_counts[agent.category] += 1

            categories = [
                CategoryResponse(name=category, agent_count=count)
                for category, count in sorted(category_counts.items())
            ]

            return CategoryListResponse(
                categories=categories,
                count=len(categories),
            )
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Registry unavailable: {str(e)}",
            ) from None

    return app
