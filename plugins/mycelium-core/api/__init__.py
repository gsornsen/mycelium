"""Discovery API module for Mycelium agent registry.

This module provides RESTful API endpoints for agent discovery,
search, and metadata retrieval.
"""

from .discovery import app, create_app
from .models import (
    AgentDetailResponse,
    AgentSearchResponse,
    DiscoverRequest,
    DiscoverResponse,
    ErrorResponse,
)

__all__ = [
    "app",
    "create_app",
    "DiscoverRequest",
    "DiscoverResponse",
    "AgentDetailResponse",
    "AgentSearchResponse",
    "ErrorResponse",
]

__version__ = "1.0.0"
