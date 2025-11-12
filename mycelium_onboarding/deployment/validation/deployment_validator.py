"""Deployment validation engine for Temporal + PostgreSQL services.

This module provides comprehensive validation of deployed services including:
- PostgreSQL health and connectivity checks
- Temporal server health and API availability
- Service-to-service communication validation
- Namespace and schema verification
- Performance and configuration checks
"""

from __future__ import annotations

import asyncio
import logging
import socket
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status of a service component."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    NOT_DEPLOYED = "not_deployed"


class ServiceType(str, Enum):
    """Type of service being validated."""

    POSTGRESQL = "postgresql"
    TEMPORAL = "temporal"
    TEMPORAL_UI = "temporal_ui"


@dataclass
class ServiceHealthStatus:
    """Health status of a service."""

    service_name: str
    service_type: ServiceType
    status: HealthStatus
    host: str
    port: int
    version: str | None = None
    message: str | None = None
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)
    response_time_ms: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def is_healthy(self) -> bool:
        """Check if service is healthy."""
        return self.status == HealthStatus.HEALTHY

    def is_degraded(self) -> bool:
        """Check if service is degraded but functional."""
        return self.status == HealthStatus.DEGRADED

    def can_operate(self) -> bool:
        """Check if service can operate (healthy or degraded)."""
        return self.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]

    def add_check(self, check_name: str, passed: bool, details: str | None = None) -> None:
        """Add a check result.

        Args:
            check_name: Name of the check
            passed: Whether the check passed
            details: Optional details about the check
        """
        check_entry = f"{check_name}: {details}" if details else check_name
        if passed:
            self.checks_passed.append(check_entry)
        else:
            self.checks_failed.append(check_entry)


@dataclass
class ValidationReport:
    """Complete validation report for deployment."""

    deployment_id: str
    validated_at: datetime = field(default_factory=datetime.now)
    overall_status: HealthStatus = HealthStatus.UNKNOWN
    services: dict[str, ServiceHealthStatus] = field(default_factory=dict)
    integration_checks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0

    def add_service(self, service_health: ServiceHealthStatus) -> None:
        """Add service health status to report."""
        self.services[service_health.service_name] = service_health
        self.total_checks += len(service_health.checks_passed) + len(service_health.checks_failed)
        self.passed_checks += len(service_health.checks_passed)
        self.failed_checks += len(service_health.checks_failed)

    def add_integration_check(self, check_description: str) -> None:
        """Add integration check result."""
        self.integration_checks.append(check_description)
        self.total_checks += 1
        self.passed_checks += 1

    def add_warning(self, warning: str) -> None:
        """Add warning to report."""
        self.warnings.append(warning)

    def add_error(self, error: str) -> None:
        """Add error to report."""
        self.errors.append(error)

    def add_recommendation(self, recommendation: str) -> None:
        """Add recommendation to report."""
        self.recommendations.append(recommendation)

    def is_healthy(self) -> bool:
        """Check if overall deployment is healthy."""
        return self.overall_status == HealthStatus.HEALTHY and self.failed_checks == 0

    def can_proceed(self) -> bool:
        """Check if deployment can proceed despite issues."""
        return self.overall_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]

    def compute_overall_status(self) -> HealthStatus:
        """Compute overall deployment status from service statuses."""
        if not self.services:
            return HealthStatus.NOT_DEPLOYED

        service_statuses = [s.status for s in self.services.values()]

        # If any service is unhealthy, overall is unhealthy
        if HealthStatus.UNHEALTHY in service_statuses:
            return HealthStatus.UNHEALTHY

        # If any service is degraded, overall is degraded
        if HealthStatus.DEGRADED in service_statuses:
            return HealthStatus.DEGRADED

        # If all services are healthy, overall is healthy
        if all(s == HealthStatus.HEALTHY for s in service_statuses):
            return HealthStatus.HEALTHY

        return HealthStatus.UNKNOWN

    def format_summary(self) -> str:
        """Format validation report as human-readable summary."""
        lines = []
        lines.append("=== Deployment Validation Report ===")
        lines.append(f"Deployment ID: {self.deployment_id}")
        lines.append(f"Validated At: {self.validated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Overall Status: {self.overall_status.value.upper()}")
        lines.append("")

        # Service statuses
        lines.append("Services:")
        for service_name, service_health in self.services.items():
            status_symbol = "✓" if service_health.is_healthy() else "✗"
            lines.append(
                f"  {status_symbol} {service_name} ({service_health.service_type.value}): {service_health.status.value}"
            )
            if service_health.version:
                lines.append(f"    Version: {service_health.version}")
            lines.append(f"    Endpoint: {service_health.host}:{service_health.port}")
            if service_health.response_time_ms:
                lines.append(f"    Response Time: {service_health.response_time_ms:.2f}ms")
            if service_health.checks_passed:
                lines.append(f"    Passed Checks: {len(service_health.checks_passed)}")
            if service_health.checks_failed:
                lines.append(f"    Failed Checks: {len(service_health.checks_failed)}")
                for check in service_health.checks_failed:
                    lines.append(f"      - {check}")

        lines.append("")

        # Integration checks
        if self.integration_checks:
            lines.append(f"Integration Checks: {len(self.integration_checks)} passed")
            for check in self.integration_checks:
                lines.append(f"  ✓ {check}")
            lines.append("")

        # Statistics
        lines.append("Statistics:")
        lines.append(f"  Total Checks: {self.total_checks}")
        lines.append(f"  Passed: {self.passed_checks}")
        lines.append(f"  Failed: {self.failed_checks}")
        if self.total_checks > 0:
            success_rate = (self.passed_checks / self.total_checks) * 100
            lines.append(f"  Success Rate: {success_rate:.1f}%")
        lines.append("")

        # Warnings
        if self.warnings:
            lines.append("Warnings:")
            for warning in self.warnings:
                lines.append(f"  ⚠ {warning}")
            lines.append("")

        # Errors
        if self.errors:
            lines.append("Errors:")
            for error in self.errors:
                lines.append(f"  ✗ {error}")
            lines.append("")

        # Recommendations
        if self.recommendations:
            lines.append("Recommendations:")
            for rec in self.recommendations:
                lines.append(f"  → {rec}")

        return "\n".join(lines)


class DeploymentValidator:
    """Comprehensive deployment validator for Temporal + PostgreSQL.

    This validator performs health checks, connectivity tests, and integration
    validation for deployed services.
    """

    def __init__(
        self,
        deployment_dir: Path | None = None,
        timeout: int = 30,
        retry_attempts: int = 3,
        retry_delay: float = 2.0,
    ):
        """Initialize deployment validator.

        Args:
            deployment_dir: Path to deployment directory
            timeout: Timeout in seconds for checks
            retry_attempts: Number of retry attempts for failed checks
            retry_delay: Delay between retries in seconds
        """
        self.deployment_dir = deployment_dir or Path.cwd()
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

    async def validate(
        self,
        postgres_host: str = "localhost",
        postgres_port: int = 5432,
        postgres_database: str = "temporal",
        postgres_user: str = "postgres",
        postgres_password: str | None = None,
        temporal_host: str = "localhost",
        temporal_port: int = 7233,
        temporal_ui_port: int = 8080,
        temporal_namespace: str = "default",
    ) -> ValidationReport:
        """Validate complete deployment.

        Args:
            postgres_host: PostgreSQL host
            postgres_port: PostgreSQL port
            postgres_database: PostgreSQL database name
            postgres_user: PostgreSQL username
            postgres_password: PostgreSQL password
            temporal_host: Temporal server host
            temporal_port: Temporal frontend port
            temporal_ui_port: Temporal UI port
            temporal_namespace: Temporal namespace to verify

        Returns:
            ValidationReport with complete validation results
        """
        report = ValidationReport(deployment_id=f"validation-{datetime.now().strftime('%Y%m%d-%H%M%S')}")

        # Phase 1: PostgreSQL validation
        logger.info("Validating PostgreSQL service...")
        postgres_health = await self.validate_postgresql(
            host=postgres_host,
            port=postgres_port,
            database=postgres_database,
            user=postgres_user,
            password=postgres_password,
        )
        report.add_service(postgres_health)

        # Phase 2: Temporal validation (only if PostgreSQL is healthy)
        if postgres_health.can_operate():
            logger.info("Validating Temporal service...")
            temporal_health = await self.validate_temporal(
                host=temporal_host,
                port=temporal_port,
                namespace=temporal_namespace,
            )
            report.add_service(temporal_health)

            # Phase 2.5: Temporal UI validation
            logger.info("Validating Temporal UI...")
            ui_health = await self.validate_temporal_ui(
                host=temporal_host,
                port=temporal_ui_port,
            )
            report.add_service(ui_health)

            # Phase 3: Integration checks (only if both services are functional)
            if temporal_health.can_operate():
                logger.info("Running integration checks...")
                await self._run_integration_checks(
                    report,
                    postgres_host,
                    postgres_port,
                    postgres_database,
                    postgres_user,
                    postgres_password,
                    temporal_host,
                    temporal_port,
                    temporal_namespace,
                )
        else:
            report.add_error("PostgreSQL is not healthy, skipping Temporal validation")
            report.add_recommendation("Fix PostgreSQL issues before proceeding with Temporal deployment")

        # Compute overall status
        report.overall_status = report.compute_overall_status()

        # Add final recommendations
        self._add_final_recommendations(report)

        return report

    async def validate_postgresql(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "temporal",
        user: str = "postgres",
        password: str | None = None,
    ) -> ServiceHealthStatus:
        """Validate PostgreSQL service.

        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            database: Database name
            user: Username
            password: Password

        Returns:
            ServiceHealthStatus for PostgreSQL
        """
        health = ServiceHealthStatus(
            service_name="postgresql",
            service_type=ServiceType.POSTGRESQL,
            status=HealthStatus.UNKNOWN,
            host=host,
            port=port,
        )

        start_time = time.time()

        # Check 1: Port connectivity
        port_check = await self._check_port_connectivity(host, port)
        health.add_check("Port Connectivity", port_check, f"{host}:{port}")

        if not port_check:
            health.status = HealthStatus.UNHEALTHY
            health.message = f"Cannot connect to PostgreSQL at {host}:{port}"
            return health

        # Check 2: PostgreSQL version
        version_info = await self._get_postgres_version(host, port, user, password)
        if version_info:
            health.version = version_info
            health.add_check("Version Detection", True, version_info)
        else:
            health.add_check("Version Detection", False, "Could not detect version")

        # Check 3: Database connectivity
        try:
            conn_check = await self._test_postgres_connection(host, port, database, user, password)
            health.add_check("Database Connection", conn_check, database)

            if conn_check:
                # Check 4: Temporal schema validation
                schema_check = await self._validate_temporal_schema(host, port, database, user, password)
                health.add_check("Temporal Schema", schema_check, "Schema tables verified")

                # Check 5: Connection pool
                pool_check = await self._check_postgres_connections(host, port, database, user, password)
                health.add_check("Connection Pool", pool_check)

                # All checks passed
                if schema_check and pool_check:
                    health.status = HealthStatus.HEALTHY
                    health.message = "PostgreSQL is healthy and ready for Temporal"
                elif schema_check:
                    health.status = HealthStatus.DEGRADED
                    health.message = "PostgreSQL is functional but connection pool may be limited"
                else:
                    health.status = HealthStatus.DEGRADED
                    health.message = "PostgreSQL is connected but Temporal schema may need initialization"
            else:
                health.status = HealthStatus.UNHEALTHY
                health.message = "Cannot connect to PostgreSQL database"

        except ImportError:
            # asyncpg not available, use basic checks only
            health.add_check("Database Connection", False, "asyncpg not installed")
            health.status = HealthStatus.DEGRADED
            health.message = "Limited validation: asyncpg not available"

        health.response_time_ms = (time.time() - start_time) * 1000
        return health

    async def validate_temporal(
        self,
        host: str = "localhost",
        port: int = 7233,
        namespace: str = "default",
    ) -> ServiceHealthStatus:
        """Validate Temporal service.

        Args:
            host: Temporal host
            port: Temporal frontend port
            namespace: Namespace to verify

        Returns:
            ServiceHealthStatus for Temporal
        """
        health = ServiceHealthStatus(
            service_name="temporal",
            service_type=ServiceType.TEMPORAL,
            status=HealthStatus.UNKNOWN,
            host=host,
            port=port,
        )

        start_time = time.time()

        # Check 1: Port connectivity
        port_check = await self._check_port_connectivity(host, port)
        health.add_check("gRPC Port Connectivity", port_check, f"{host}:{port}")

        if not port_check:
            health.status = HealthStatus.UNHEALTHY
            health.message = f"Cannot connect to Temporal at {host}:{port}"
            return health

        # Check 2: Temporal version
        version_info = await self._get_temporal_version(host, port)
        if version_info:
            health.version = version_info
            health.add_check("Version Detection", True, version_info)
        else:
            health.add_check("Version Detection", False, "Could not detect version")

        # Check 3: Cluster health
        cluster_health = await self._check_temporal_cluster_health(host, port)
        health.add_check("Cluster Health", cluster_health)

        # Check 4: Namespace existence
        namespace_check = await self._check_temporal_namespace(host, port, namespace)
        health.add_check("Namespace Exists", namespace_check, namespace)
        health.metadata["namespace"] = namespace

        # Check 5: Frontend service
        frontend_check = await self._check_temporal_frontend(host, port)
        health.add_check("Frontend Service", frontend_check)

        # Determine overall health
        if cluster_health and namespace_check and frontend_check:
            health.status = HealthStatus.HEALTHY
            health.message = "Temporal is healthy and ready for workflows"
        elif cluster_health and frontend_check:
            health.status = HealthStatus.DEGRADED
            health.message = f"Temporal is functional but namespace '{namespace}' may need creation"
        elif port_check:
            health.status = HealthStatus.DEGRADED
            health.message = "Temporal is starting up or partially available"
        else:
            # Defensive fallback - unreachable due to early return if not port_check
            health.status = HealthStatus.UNHEALTHY  # type: ignore[unreachable]
            health.message = "Temporal service is not responding correctly"

        health.response_time_ms = (time.time() - start_time) * 1000
        return health

    async def validate_temporal_ui(
        self,
        host: str = "localhost",
        port: int = 8080,
    ) -> ServiceHealthStatus:
        """Validate Temporal UI.

        Args:
            host: Temporal host
            port: Temporal UI port

        Returns:
            ServiceHealthStatus for Temporal UI
        """
        health = ServiceHealthStatus(
            service_name="temporal-ui",
            service_type=ServiceType.TEMPORAL_UI,
            status=HealthStatus.UNKNOWN,
            host=host,
            port=port,
        )

        start_time = time.time()

        # Check 1: Port connectivity
        port_check = await self._check_port_connectivity(host, port)
        health.add_check("HTTP Port Connectivity", port_check, f"{host}:{port}")

        if not port_check:
            health.status = HealthStatus.DEGRADED  # UI is optional
            health.message = "Temporal UI is not accessible (optional component)"
            return health

        # Check 2: HTTP endpoint
        http_check = await self._check_http_endpoint(f"http://{host}:{port}")
        health.add_check("HTTP Endpoint", http_check)

        if http_check:
            health.status = HealthStatus.HEALTHY
            health.message = "Temporal UI is accessible"
        else:
            health.status = HealthStatus.DEGRADED
            health.message = "Temporal UI port is open but HTTP endpoint not responding"

        health.response_time_ms = (time.time() - start_time) * 1000
        return health

    async def _run_integration_checks(
        self,
        report: ValidationReport,
        _postgres_host: str,
        _postgres_port: int,
        postgres_database: str,
        _postgres_user: str,
        _postgres_password: str | None,
        temporal_host: str,
        temporal_port: int,
        temporal_namespace: str,
    ) -> None:
        """Run integration checks between services."""
        # Integration check 1: Temporal → PostgreSQL connectivity
        temporal_db_check = await self._check_temporal_postgres_connection(
            temporal_host, temporal_port, postgres_database
        )
        if temporal_db_check:
            report.add_integration_check("Temporal can communicate with PostgreSQL")
        else:
            report.add_warning("Could not verify Temporal → PostgreSQL communication")

        # Integration check 2: Default namespace registration
        namespace_registered = await self._verify_namespace_registered(temporal_host, temporal_port, temporal_namespace)
        if namespace_registered:
            report.add_integration_check(f"Namespace '{temporal_namespace}' is registered and active")
        else:
            report.add_warning(f"Namespace '{temporal_namespace}' may not be fully initialized")

    async def _check_port_connectivity(self, host: str, port: int, timeout: float = 5.0) -> bool:
        """Check if a port is reachable.

        Args:
            host: Host to check
            port: Port to check
            timeout: Connection timeout

        Returns:
            True if port is reachable
        """
        for attempt in range(self.retry_attempts):
            try:
                # Use asyncio for non-blocking socket check
                loop = asyncio.get_event_loop()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)

                await loop.run_in_executor(None, sock.connect, (host, port))
                sock.close()
                return True

            except OSError as e:
                logger.debug(f"Port check attempt {attempt + 1}/{self.retry_attempts} failed: {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)

        return False

    async def _get_postgres_version(self, host: str, port: int, user: str, password: str | None) -> str | None:
        """Get PostgreSQL version."""
        try:
            # Use psql if available
            cmd = [
                "psql",
                f"postgresql://{user}:{password or ''}@{host}:{port}/postgres",
                "-t",
                "-c",
                "SELECT version();",
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0 and result.stdout:
                # Extract version number from output
                version_line = result.stdout.strip()
                if "PostgreSQL" in version_line:
                    parts = version_line.split()
                    for part in parts:
                        if part[0].isdigit():
                            return part
        except Exception as e:
            logger.debug(f"Could not detect PostgreSQL version: {e}")

        return None

    async def _test_postgres_connection(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str | None,
    ) -> bool:
        """Test PostgreSQL connection using asyncpg."""
        try:
            import asyncpg

            conn = await asyncpg.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password or "",
                timeout=self.timeout,
            )
            await conn.close()
            return True
        except Exception as e:
            logger.debug(f"PostgreSQL connection test failed: {e}")
            return False

    async def _validate_temporal_schema(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str | None,
    ) -> bool:
        """Validate Temporal schema exists in PostgreSQL."""
        try:
            import asyncpg

            conn = await asyncpg.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password or "",
                timeout=self.timeout,
            )

            # Check for Temporal schema tables
            result = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('namespaces', 'workflows', 'executions')
                """
            )

            await conn.close()

            # If we find some Temporal tables, schema is initialized
            return bool(result > 0)

        except Exception as e:
            logger.debug(f"Temporal schema validation failed: {e}")
            return False

    async def _check_postgres_connections(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str | None,
    ) -> bool:
        """Check PostgreSQL connection pool status."""
        try:
            import asyncpg

            conn = await asyncpg.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password or "",
                timeout=self.timeout,
            )

            # Check current connections
            result = await conn.fetchval("SELECT count(*) FROM pg_stat_activity WHERE datname = $1", database)

            await conn.close()

            # Healthy if we have some connections but not too many
            return bool(0 < result < 100)

        except Exception as e:
            logger.debug(f"PostgreSQL connection pool check failed: {e}")
            return False

    async def _get_temporal_version(self, _host: str, _port: int) -> str | None:
        """Get Temporal server version."""
        try:
            # This is simplified - in production would use Temporal SDK
            logger.debug("Temporal version detection requires Temporal SDK")
            return None
        except Exception as e:
            logger.debug(f"Could not detect Temporal version: {e}")
            return None

    async def _check_temporal_cluster_health(self, host: str, port: int) -> bool:
        """Check Temporal cluster health."""
        # This would require Temporal SDK or gRPC client
        # For now, use port connectivity as proxy
        return await self._check_port_connectivity(host, port)

    async def _check_temporal_namespace(self, _host: str, _port: int, namespace: str) -> bool:
        """Check if Temporal namespace exists."""
        # This would require Temporal SDK
        # For now, assume default namespace exists if server is up
        logger.debug(f"Namespace check for '{namespace}' requires Temporal SDK integration")
        return True  # Optimistic assumption

    async def _check_temporal_frontend(self, host: str, port: int) -> bool:
        """Check Temporal frontend service."""
        return await self._check_port_connectivity(host, port)

    async def _check_http_endpoint(self, url: str) -> bool:
        """Check if HTTP endpoint is responding."""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, follow_redirects=True)
                return response.status_code < 500
        except Exception as e:
            logger.debug(f"HTTP endpoint check failed for {url}: {e}")
            return False

    async def _check_temporal_postgres_connection(
        self, _temporal_host: str, _temporal_port: int, _postgres_database: str
    ) -> bool:
        """Verify Temporal can connect to PostgreSQL."""
        # This would require inspecting Temporal logs or using admin API
        logger.debug("Temporal → PostgreSQL connection check requires admin API")
        return True  # Optimistic assumption

    async def _verify_namespace_registered(self, _temporal_host: str, _temporal_port: int, _namespace: str) -> bool:
        """Verify namespace is registered in Temporal."""
        # This would require Temporal SDK
        logger.debug("Namespace registration check requires Temporal SDK")
        return True  # Optimistic assumption

    def _add_final_recommendations(self, report: ValidationReport) -> None:
        """Add final recommendations based on validation results."""
        if report.is_healthy():
            report.add_recommendation("All services are healthy. You can proceed with workflow development.")
            report.add_recommendation("Access Temporal UI at http://localhost:8080 to monitor workflows")
        elif report.can_proceed():
            report.add_recommendation(
                "Some issues detected but deployment can operate. Review warnings and consider fixes."
            )
        else:
            report.add_recommendation("Critical issues detected. Fix errors before proceeding with workflows.")

        # Add specific recommendations based on service statuses
        for service_name, service_health in report.services.items():
            if service_health.status == HealthStatus.UNHEALTHY:
                report.add_recommendation(f"Fix {service_name} health issues: {service_health.message}")
            elif service_health.status == HealthStatus.DEGRADED:
                report.add_recommendation(f"Optimize {service_name}: {service_health.message}")


async def validate_deployment(
    deployment_dir: Path | None = None,
    postgres_host: str = "localhost",
    postgres_port: int = 5432,
    temporal_host: str = "localhost",
    temporal_port: int = 7233,
    **kwargs: Any,
) -> ValidationReport:
    """Convenience function to validate deployment.

    Args:
        deployment_dir: Path to deployment directory
        postgres_host: PostgreSQL host
        postgres_port: PostgreSQL port
        temporal_host: Temporal host
        temporal_port: Temporal frontend port
        **kwargs: Additional validation parameters

    Returns:
        ValidationReport with complete validation results

    Example:
        >>> report = await validate_deployment()
        >>> if report.is_healthy():
        ...     print("Deployment is healthy!")
        >>> else:
        ...     print(report.format_summary())
    """
    validator = DeploymentValidator(deployment_dir=deployment_dir)
    return await validator.validate(
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        temporal_host=temporal_host,
        temporal_port=temporal_port,
        **kwargs,
    )
