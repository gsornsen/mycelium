"""PostgreSQL deployment and compatibility management.

This module handles PostgreSQL version detection, compatibility checking,
and migration path planning for the Mycelium platform.
"""

from __future__ import annotations

from .compatibility import PostgresCompatibilityChecker
from .migration import PostgresMigrationPlanner
from .version_manager import PostgresVersionManager

__all__ = [
    "PostgresVersionManager",
    "PostgresCompatibilityChecker",
    "PostgresMigrationPlanner",
]
