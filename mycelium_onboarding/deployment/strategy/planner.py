"""Service deployment planning.

This module implements intelligent deployment planning based on service
detection results. It determines the optimal strategy (REUSE, CREATE, ALONGSIDE)
for each service based on compatibility, availability, and user preferences.
"""

from __future__ import annotations

import logging

from mycelium_onboarding.config.schema import MyceliumConfig

from .detector import DetectedService, ServiceStatus, ServiceType
from .service_strategy import (
    CompatibilityLevel,
    DeploymentPlanSummary,
    ServiceDeploymentPlan,
    ServiceStrategy,
    VersionRequirement,
)

logger = logging.getLogger(__name__)


class ServiceDeploymentPlanner:
    """Creates intelligent deployment plans based on detection results.

    This class analyzes detected services and creates deployment plans that
    optimize for service reuse while respecting compatibility requirements
    and avoiding conflicts.
    """

    # Version requirements for services
    VERSION_REQUIREMENTS = {
        ServiceType.REDIS: VersionRequirement(min_version="6.0"),
        ServiceType.POSTGRESQL: VersionRequirement(min_version="13.0"),
        ServiceType.RABBITMQ: VersionRequirement(min_version="3.8"),
    }

    # Port offsets for ALONGSIDE strategy
    PORT_OFFSETS = {
        ServiceType.REDIS: 1,  # 6379 -> 6380
        ServiceType.POSTGRESQL: 1,  # 5432 -> 5433
        ServiceType.RABBITMQ: 100,  # 5672 -> 5772
    }

    def __init__(self, config: MyceliumConfig, detected_services: list[DetectedService], prefer_reuse: bool = True):
        """Initialize deployment planner.

        Args:
            config: Mycelium configuration
            detected_services: List of detected services
            prefer_reuse: Whether to prefer reusing existing services
        """
        self.config = config
        self.detected_services = detected_services
        self.prefer_reuse = prefer_reuse
        self._detected_by_type: dict[ServiceType, list[DetectedService]] = {}
        self._index_services()

    def _index_services(self):
        """Index detected services by type for quick lookup."""
        logger.debug(f"Indexing {len(self.detected_services)} detected services:")
        for service in self.detected_services:
            logger.debug(f"  - {service.name}: type={service.service_type}, status={service.status}")
            if service.service_type not in self._detected_by_type:
                self._detected_by_type[service.service_type] = []
            self._detected_by_type[service.service_type].append(service)

        logger.debug(f"Index result: {len(self._detected_by_type)} service types")
        for service_type, services in self._detected_by_type.items():
            logger.debug(f"  - {service_type}: {len(services)} service(s)")

    def create_deployment_plan(self) -> DeploymentPlanSummary:
        """Create complete deployment plan for all services.

        Returns:
            Deployment plan summary with strategy for each service
        """
        plan = DeploymentPlanSummary(
            plan_id=f"deploy-{self.config.project_name}",
            project_name=self.config.project_name,
        )

        # Plan for each enabled service
        if self.config.services.redis.enabled:
            redis_plan = self._plan_redis()
            plan.add_service_plan(redis_plan)

        if self.config.services.postgres.enabled:
            postgres_plan = self._plan_postgres()
            plan.add_service_plan(postgres_plan)

        if self.config.services.temporal.enabled:
            temporal_plan = self._plan_temporal()
            plan.add_service_plan(temporal_plan)

        # Add general recommendations
        self._add_recommendations(plan)

        return plan

    def _plan_redis(self) -> ServiceDeploymentPlan:
        """Plan Redis deployment strategy.

        Returns:
            Service deployment plan for Redis
        """
        detected_redis = self._get_best_service(ServiceType.REDIS)
        config = self.config.services.redis

        # DEBUG: Log what we found
        logger.debug("Planning Redis deployment:")
        logger.debug(f"  - Config enabled: {config.enabled}")
        logger.debug(f"  - Detected service: {detected_redis.name if detected_redis else 'None'}")
        logger.debug(f"  - Detected status: {detected_redis.status if detected_redis else 'N/A'}")

        if detected_redis and detected_redis.status == ServiceStatus.RUNNING:
            # Redis is running, check compatibility
            compatibility = self._check_compatibility(ServiceType.REDIS, detected_redis.version)

            if self.prefer_reuse and compatibility == CompatibilityLevel.COMPATIBLE:
                # REUSE existing Redis
                return ServiceDeploymentPlan(
                    service_name="redis",
                    strategy=ServiceStrategy.REUSE,
                    host=detected_redis.host,
                    port=detected_redis.port,
                    version=detected_redis.version,
                    connection_string=self._build_redis_connection(detected_redis.host, detected_redis.port),
                    reason=f"Compatible Redis {detected_redis.version} already running on {detected_redis.host}:{detected_redis.port}",
                    detected_service_id=detected_redis.fingerprint.fingerprint_hash
                    if detected_redis.fingerprint
                    else None,
                    compatibility_level=compatibility,
                )
            if compatibility == CompatibilityLevel.MAJOR_MISMATCH:
                # Version incompatible, run ALONGSIDE
                new_port = self._calculate_alongside_port(ServiceType.REDIS, detected_redis.port)
                return ServiceDeploymentPlan(
                    service_name="redis",
                    strategy=ServiceStrategy.ALONGSIDE,
                    host="localhost",
                    port=new_port,
                    version=config.version or "7.2",
                    connection_string=self._build_redis_connection("localhost", new_port),
                    reason=f"Existing Redis {detected_redis.version} incompatible, running alongside on port {new_port}",
                    container_name=f"{self.config.project_name}-redis",
                    compatibility_level=compatibility,
                    metadata={"existing_service_port": detected_redis.port},
                )

        # No running Redis or not reusing, CREATE new
        return ServiceDeploymentPlan(
            service_name="redis",
            strategy=ServiceStrategy.CREATE,
            host="localhost",
            port=config.port,
            version=config.version or "7.2",
            connection_string=self._build_redis_connection("localhost", config.port),
            reason="No compatible Redis instance detected, creating new service",
            container_name=f"{self.config.project_name}-redis",
        )

    def _plan_postgres(self) -> ServiceDeploymentPlan:
        """Plan PostgreSQL deployment strategy.

        Returns:
            Service deployment plan for PostgreSQL
        """
        detected_pg = self._get_best_service(ServiceType.POSTGRESQL)
        config = self.config.services.postgres

        if detected_pg and detected_pg.status == ServiceStatus.RUNNING:
            # PostgreSQL is running, check compatibility
            compatibility = self._check_compatibility(ServiceType.POSTGRESQL, detected_pg.version)

            if self.prefer_reuse and compatibility == CompatibilityLevel.COMPATIBLE:
                # REUSE existing PostgreSQL
                return ServiceDeploymentPlan(
                    service_name="postgres",
                    strategy=ServiceStrategy.REUSE,
                    host=detected_pg.host,
                    port=detected_pg.port,
                    version=detected_pg.version,
                    connection_string=self._build_postgres_connection(
                        detected_pg.host, detected_pg.port, config.database
                    ),
                    reason=f"Compatible PostgreSQL {detected_pg.version} already running on {detected_pg.host}:{detected_pg.port}",
                    detected_service_id=detected_pg.fingerprint.fingerprint_hash if detected_pg.fingerprint else None,
                    compatibility_level=compatibility,
                    requires_configuration=True,
                    metadata={"requires_database_creation": True},
                )
            if compatibility == CompatibilityLevel.MAJOR_MISMATCH:
                # Version incompatible, run ALONGSIDE
                new_port = self._calculate_alongside_port(ServiceType.POSTGRESQL, detected_pg.port)
                return ServiceDeploymentPlan(
                    service_name="postgres",
                    strategy=ServiceStrategy.ALONGSIDE,
                    host="localhost",
                    port=new_port,
                    version=config.version or "15",
                    connection_string=self._build_postgres_connection("localhost", new_port, config.database),
                    reason=f"Existing PostgreSQL {detected_pg.version} incompatible, running alongside on port {new_port}",
                    container_name=f"{self.config.project_name}-postgres",
                    compatibility_level=compatibility,
                    metadata={"existing_service_port": detected_pg.port},
                )

        # Check if detected but not running (e.g., stopped service with port still in use)
        if detected_pg and detected_pg.status != ServiceStatus.RUNNING:
            # Service detected but not running - check if port is in use
            port_in_use = self._is_port_in_use(config.port)

            if port_in_use:
                # Port is in use by something else - use ALONGSIDE strategy
                logger.warning(
                    f"Port {config.port} is in use even though PostgreSQL is {detected_pg.status}. "
                    f"Using ALONGSIDE strategy."
                )
                new_port = self._calculate_alongside_port(ServiceType.POSTGRESQL, config.port)
                return ServiceDeploymentPlan(
                    service_name="postgres",
                    strategy=ServiceStrategy.ALONGSIDE,
                    host="localhost",
                    port=new_port,
                    version=config.version or "15",
                    connection_string=self._build_postgres_connection("localhost", new_port, config.database),
                    reason=f"Port {config.port} in use by undetected service, running alongside on port {new_port}",
                    container_name=f"{self.config.project_name}-postgres",
                    metadata={"original_port": config.port, "port_conflict_detected": True},
                )

        # Check if CREATE port is available (no detected service, or detected service is not installed)
        if not detected_pg or detected_pg.status == ServiceStatus.NOT_INSTALLED:
            port_in_use = self._is_port_in_use(config.port)
            if port_in_use:
                # Port conflict - use alternative port
                new_port = config.port + 1
                logger.warning(f"Port {config.port} in use, using port {new_port} instead")
                return ServiceDeploymentPlan(
                    service_name="postgres",
                    strategy=ServiceStrategy.CREATE,
                    host="localhost",
                    port=new_port,
                    version=config.version or "15",
                    connection_string=self._build_postgres_connection("localhost", new_port, config.database),
                    reason=f"Creating new service on port {new_port} (port {config.port} in use)",
                    container_name=f"{self.config.project_name}-postgres",
                    metadata={"port_conflict_avoided": True},
                )

        # No running PostgreSQL or not reusing, CREATE new on configured port
        return ServiceDeploymentPlan(
            service_name="postgres",
            strategy=ServiceStrategy.CREATE,
            host="localhost",
            port=config.port,
            version=config.version or "15",
            connection_string=self._build_postgres_connection("localhost", config.port, config.database),
            reason="No compatible PostgreSQL instance detected, creating new service",
            container_name=f"{self.config.project_name}-postgres",
        )

    def _plan_temporal(self) -> ServiceDeploymentPlan:
        """Plan Temporal deployment strategy.

        Temporal is complex and typically always created fresh to avoid conflicts.

        Returns:
            Service deployment plan for Temporal
        """
        config = self.config.services.temporal

        # For Temporal, we typically always create a new instance
        # It's too complex to reliably reuse existing instances
        return ServiceDeploymentPlan(
            service_name="temporal",
            strategy=ServiceStrategy.CREATE,
            host="localhost",
            port=config.frontend_port,
            version=config.version or "1.22.0",
            connection_string=f"localhost:{config.frontend_port}",
            reason="Temporal requires dedicated instance with specific configuration",
            container_name=f"{self.config.project_name}-temporal",
            metadata={
                "ui_port": config.ui_port,
                "namespace": config.namespace,
            },
        )

    def _get_best_service(self, service_type: ServiceType) -> DetectedService | None:
        """Get the best detected service of a given type.

        Prefers running services with recent versions.

        Args:
            service_type: Type of service to find

        Returns:
            Best matching service or None
        """
        services = self._detected_by_type.get(service_type, [])
        if not services:
            return None

        # Prioritize running services
        running_services = [s for s in services if s.status == ServiceStatus.RUNNING]
        if running_services:
            return running_services[0]

        # Fall back to any detected service
        return services[0]

    def _is_port_in_use(self, port: int, host: str = "localhost") -> bool:
        """Check if a port is currently in use.

        Args:
            port: Port number to check
            host: Host to check (default: localhost)

        Returns:
            True if port is in use, False otherwise
        """
        import socket

        try:
            # Try to connect to the port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                # If connect_ex returns 0, something is listening
                # If it returns error code, port is likely free
                in_use = result == 0
                logger.debug(f"Port {port} check: {'IN USE' if in_use else 'AVAILABLE'} (result={result})")
                return in_use
        except Exception as e:
            logger.debug(f"Error checking port {port}: {e}")
            # If we can't check, assume it's free (conservative)
            return False

    def _check_compatibility(self, service_type: ServiceType, version: str) -> CompatibilityLevel:
        """Check version compatibility for a service.

        Args:
            service_type: Type of service
            version: Detected version string

        Returns:
            Compatibility level
        """
        requirement = self.VERSION_REQUIREMENTS.get(service_type)
        if not requirement:
            return CompatibilityLevel.UNKNOWN

        return requirement.is_compatible(version)

    def _calculate_alongside_port(self, service_type: ServiceType, existing_port: int) -> int:
        """Calculate port for ALONGSIDE strategy.

        Args:
            service_type: Type of service
            existing_port: Port of existing service

        Returns:
            New port to use
        """
        offset = self.PORT_OFFSETS.get(service_type, 100)
        return existing_port + offset

    def _build_redis_connection(self, host: str, port: int) -> str:
        """Build Redis connection string.

        Args:
            host: Redis host
            port: Redis port

        Returns:
            Redis connection URL
        """
        return f"redis://{host}:{port}/0"

    def _build_postgres_connection(self, host: str, port: int, database: str) -> str:
        """Build PostgreSQL connection string.

        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            database: Database name

        Returns:
            PostgreSQL connection URL
        """
        # Use environment variables for credentials
        return f"postgresql://postgres:{{POSTGRES_PASSWORD}}@{host}:{port}/{database}"

    def _add_recommendations(self, plan: DeploymentPlanSummary):
        """Add recommendations to deployment plan.

        Args:
            plan: Deployment plan to add recommendations to
        """
        # Recommend updating credentials for reused services
        if plan.services_to_reuse:
            plan.recommendations.append(
                f"Using existing services: {', '.join(plan.services_to_reuse)}. "
                "Ensure you have appropriate credentials configured."
            )

        # Warn about alongside deployments
        if plan.services_alongside:
            plan.warnings.append(
                f"Running services alongside existing instances: {', '.join(plan.services_alongside)}. "
                "This may consume additional resources."
            )

        # Recommend configuration for reused PostgreSQL
        for service_name, service_plan in plan.service_plans.items():
            if service_name == "postgres" and service_plan.requires_configuration:
                plan.recommendations.append(
                    f"PostgreSQL database '{self.config.services.postgres.database}' "
                    "may need to be created on the existing instance."
                )
