"""PostgreSQL deployment and compatibility management.

This module handles PostgreSQL version detection, compatibility checking,
and migration path planning for the Mycelium platform.
"""

from __future__ import annotations

from .compatibility import (
    CompatibilityMatrix,
    CompatibilityRequirement,
    PostgresCompatibilityChecker,
)
from .version_manager import PostgresVersionManager

__all__ = [
    "PostgresVersionManager",
    "PostgresCompatibilityChecker",
    "CompatibilityMatrix",
    "CompatibilityRequirement",
]
