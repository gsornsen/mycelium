"""Smart deployment strategy module.

This module provides intelligent service detection, reuse logic,
and deployment decision making for the Mycelium platform.
"""

from __future__ import annotations

from .detector import (
    DetectedService,
    ServiceDetector,
    ServiceFingerprint,
    ServiceStatus,
    ServiceType,
)
from .planner import ServiceDeploymentPlanner
from .service_strategy import (
    CompatibilityLevel,
    DeploymentPlanSummary,
    ServiceDeploymentPlan,
    ServiceStrategy,
    VersionRequirement,
)

__all__ = [
    # Detector classes
    "ServiceDetector",
    "DetectedService",
    "ServiceFingerprint",
    "ServiceType",
    "ServiceStatus",
    # Strategy classes
    "ServiceStrategy",
    "ServiceDeploymentPlan",
    "DeploymentPlanSummary",
    "CompatibilityLevel",
    "VersionRequirement",
    # Planner
    "ServiceDeploymentPlanner",
]
