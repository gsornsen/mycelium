"""Service deployment strategy models.

This module defines the strategy patterns for intelligent service deployment,
including reuse decisions, compatibility checking, and deployment planning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ServiceStrategy(str, Enum):
    """Strategy for deploying a service.

    Determines how a service should be handled during deployment:
    - REUSE: Use existing service (compatible version, running)
    - CREATE: Create new service (no existing service found)
    - ALONGSIDE: Create new service on different port (incompatible version)
    - SKIP: Skip this service (not needed for deployment)
    """

    REUSE = "reuse"
    CREATE = "create"
    ALONGSIDE = "alongside"
    SKIP = "skip"


class CompatibilityLevel(str, Enum):
    """Compatibility level between detected and required versions."""

    COMPATIBLE = "compatible"
    MINOR_MISMATCH = "minor_mismatch"
    MAJOR_MISMATCH = "major_mismatch"
    UNKNOWN = "unknown"


@dataclass
class VersionRequirement:
    """Version requirement for a service."""

    min_version: str | None = None
    max_version: str | None = None
    preferred_version: str | None = None

    def is_compatible(self, version: str) -> CompatibilityLevel:  # noqa: ARG002
        """Check if version meets requirements.

        Args:
            version: Version string to check

        Returns:
            Compatibility level
        """
        # Simple version comparison logic
        # TODO: Implement proper semantic versioning comparison
        if self.min_version or self.max_version:
            # For now, accept any version if detected
            return CompatibilityLevel.COMPATIBLE
        return CompatibilityLevel.COMPATIBLE


@dataclass
class ServiceDeploymentPlan:
    """Plan for deploying a specific service.

    Attributes:
        service_name: Name of the service (e.g., "redis", "postgres")
        strategy: Deployment strategy to use
        host: Host where service will be accessed
        port: Port where service will be accessed
        version: Version of service to deploy/use
        connection_string: Connection string for accessing the service
        reason: Human-readable reason for the strategy choice
        detected_service_id: ID of detected service if reusing
        container_name: Docker container name if creating
        requires_configuration: Whether additional configuration is needed
        metadata: Additional metadata about the deployment
    """

    service_name: str
    strategy: ServiceStrategy
    host: str
    port: int
    version: str
    connection_string: str
    reason: str
    detected_service_id: str | None = None
    container_name: str | None = None
    requires_configuration: bool = False
    compatibility_level: CompatibilityLevel = CompatibilityLevel.COMPATIBLE
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def is_reusing_existing(self) -> bool:
        """Check if this plan reuses an existing service."""
        return self.strategy == ServiceStrategy.REUSE

    @property
    def is_creating_new(self) -> bool:
        """Check if this plan creates a new service."""
        return self.strategy in [ServiceStrategy.CREATE, ServiceStrategy.ALONGSIDE]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "service_name": self.service_name,
            "strategy": self.strategy.value,
            "host": self.host,
            "port": self.port,
            "version": self.version,
            "connection_string": self.connection_string,
            "reason": self.reason,
            "detected_service_id": self.detected_service_id,
            "container_name": self.container_name,
            "requires_configuration": self.requires_configuration,
            "compatibility_level": self.compatibility_level.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


class DeploymentPlanSummary(BaseModel):
    """Summary of complete deployment plan.

    Tracks which services will be reused, created, or run alongside
    existing instances.
    """

    model_config = {"arbitrary_types_allowed": True}

    plan_id: str = Field(description="Unique plan identifier")
    project_name: str = Field(description="Project name")
    created_at: datetime = Field(default_factory=datetime.now, description="Plan creation time")

    services_to_reuse: list[str] = Field(
        default_factory=list, description="Services that will reuse existing instances"
    )
    services_to_create: list[str] = Field(default_factory=list, description="Services to create fresh")
    services_alongside: list[str] = Field(
        default_factory=list, description="Services to run alongside existing instances"
    )
    services_skipped: list[str] = Field(default_factory=list, description="Services skipped")

    service_plans: dict[str, ServiceDeploymentPlan] = Field(
        default_factory=dict, description="Detailed plan for each service"
    )

    warnings: list[str] = Field(default_factory=list, description="Warnings about the deployment")
    recommendations: list[str] = Field(default_factory=list, description="Recommendations for the user")

    def add_service_plan(self, plan: ServiceDeploymentPlan) -> None:
        """Add a service plan to the summary.

        Args:
            plan: Service deployment plan to add
        """
        self.service_plans[plan.service_name] = plan

        # Update summary lists
        if plan.strategy == ServiceStrategy.REUSE:
            self.services_to_reuse.append(plan.service_name)
        elif plan.strategy == ServiceStrategy.CREATE:
            self.services_to_create.append(plan.service_name)
        elif plan.strategy == ServiceStrategy.ALONGSIDE:
            self.services_alongside.append(plan.service_name)
        elif plan.strategy == ServiceStrategy.SKIP:
            self.services_skipped.append(plan.service_name)

    def get_service_plan(self, service_name: str) -> ServiceDeploymentPlan | None:
        """Get deployment plan for a specific service.

        Args:
            service_name: Name of the service

        Returns:
            Service deployment plan or None if not found
        """
        return self.service_plans.get(service_name)

    @property
    def has_services_to_deploy(self) -> bool:
        """Check if there are any services to deploy."""
        return bool(self.services_to_create or self.services_alongside)

    @property
    def total_services(self) -> int:
        """Get total number of services in plan."""
        return len(self.service_plans)

    def generate_docker_compose_context(self) -> dict[str, Any]:
        """Generate context for docker-compose template rendering.

        Returns:
            Dictionary with template context including strategy info
        """
        context: dict[str, Any] = {
            "services_to_deploy": {},
            "services_reused": {},
            "connection_info": {},
        }

        for service_name, plan in self.service_plans.items():
            if plan.is_creating_new:
                context["services_to_deploy"][service_name] = {
                    "port": plan.port,
                    "version": plan.version,
                    "container_name": plan.container_name,
                    "host": plan.host,
                }
            elif plan.is_reusing_existing:
                context["services_reused"][service_name] = {
                    "host": plan.host,
                    "port": plan.port,
                    "version": plan.version,
                }

            context["connection_info"][service_name] = {
                "connection_string": plan.connection_string,
                "host": plan.host,
                "port": plan.port,
            }

        return context

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "plan_id": self.plan_id,
            "project_name": self.project_name,
            "created_at": self.created_at.isoformat(),
            "services_to_reuse": self.services_to_reuse,
            "services_to_create": self.services_to_create,
            "services_alongside": self.services_alongside,
            "services_skipped": self.services_skipped,
            "service_plans": {name: plan.to_dict() for name, plan in self.service_plans.items()},
            "warnings": self.warnings,
            "recommendations": self.recommendations,
        }
