"""Configuration migration system.

This module provides a comprehensive migration system for safely migrating
legacy configuration files to the new XDG-compliant structure.

The migration system consists of three main components:

1. MigrationDetector: Scans for legacy configuration files
2. MigrationPlanner: Creates migration plan with validation
3. MigrationExecutor: Executes migration with backup and rollback

Example:
    >>> from mycelium_onboarding.config.migration import (
    ...     MigrationDetector,
    ...     MigrationPlanner,
    ...     MigrationExecutor,
    ... )
    >>>
    >>> # Detect legacy configs
    >>> detector = MigrationDetector()
    >>> legacy_configs = detector.scan_for_legacy_configs()
    >>>
    >>> # Create migration plan
    >>> planner = MigrationPlanner()
    >>> plan = planner.create_plan(legacy_configs)
    >>>
    >>> # Execute migration
    >>> executor = MigrationExecutor(dry_run=False)
    >>> result = executor.execute(plan)
"""

from __future__ import annotations

from mycelium_onboarding.config.migration.backup import BackupManager
from mycelium_onboarding.config.migration.detector import (
    LegacyConfigLocation,
    MigrationDetector,
)
from mycelium_onboarding.config.migration.executor import (
    MigrationExecutor,
    MigrationResult,
)
from mycelium_onboarding.config.migration.planner import (
    MigrationAction,
    MigrationPlanner,
    MigrationStep,
)
from mycelium_onboarding.config.migration.rollback import RollbackManager

__all__ = [
    "MigrationDetector",
    "MigrationPlanner",
    "MigrationExecutor",
    "MigrationAction",
    "MigrationStep",
    "MigrationResult",
    "LegacyConfigLocation",
    "BackupManager",
    "RollbackManager",
]
