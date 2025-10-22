"""Agent Registry module for Mycelium.

This module provides a centralized registry for managing agent metadata
with PostgreSQL backend and pgvector support for semantic search.
"""

from .registry import (
    AgentAlreadyExistsError,
    AgentNotFoundError,
    AgentRegistry,
    AgentRegistryError,
    load_agents_from_index,
)

__all__ = [
    "AgentRegistry",
    "AgentRegistryError",
    "AgentNotFoundError",
    "AgentAlreadyExistsError",
    "load_agents_from_index",
]

__version__ = "1.0.0"
