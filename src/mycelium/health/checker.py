"""Health check implementation for agents and services.

Provides liveness and readiness probes with metrics exposure.
"""

from typing import Optional, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from mycelium.errors import HealthCheckError


class HealthStatus(str, Enum):
    """Health check status."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    status: HealthStatus
    message: Optional[str] = None
    timestamp: Optional[datetime] = None
    latency_ms: Optional[float] = None
    details: Optional[dict[str, str | int | float]] = None

    def __post_init__(self) -> None:
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class HealthChecker:
    """Health check coordinator for agents and services."""

    def __init__(self) -> None:
        """Initialize health checker."""
        self.checks: dict[str, Callable[[], Awaitable[HealthCheckResult]]] = {}
        self.results: dict[str, HealthCheckResult] = {}

    def register_check(
        self,
        name: str,
        check_fn: Callable[[], Awaitable[HealthCheckResult]],
    ) -> None:
        """Register a health check.

        Args:
            name: Check name
            check_fn: Async function returning HealthCheckResult
        """
        self.checks[name] = check_fn

    async def run_check(self, name: str) -> HealthCheckResult:
        """Run a specific health check.

        Args:
            name: Check name

        Returns:
            Health check result
        """
        if name not in self.checks:
            raise HealthCheckError(
                f"Health check '{name}' not found",
                suggestion="List available checks with health_checker.list_checks()",
                debug_info={"check": name}
            )

        check_fn = self.checks[name]
        start_time = datetime.now(timezone.utc)

        try:
            result = await check_fn()
            result.latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self.results[name] = result
            return result
        except Exception as e:
            result = HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}",
                latency_ms=(datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
            )
            self.results[name] = result
            return result

    async def run_all_checks(self) -> dict[str, HealthCheckResult]:
        """Run all registered health checks.

        Returns:
            Dictionary of check results
        """
        results = {}
        for name in self.checks:
            results[name] = await self.run_check(name)
        return results

    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status.

        Returns:
            Aggregated health status
        """
        if not self.results:
            return HealthStatus.UNKNOWN

        statuses = [r.status for r in self.results.values()]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNKNOWN

    def list_checks(self) -> list[str]:
        """List registered health checks.

        Returns:
            List of check names
        """
        return list(self.checks.keys())

    def get_check_result(self, name: str) -> Optional[HealthCheckResult]:
        """Get cached check result.

        Args:
            name: Check name

        Returns:
            Cached result or None
        """
        return self.results.get(name)

    def is_result_stale(
        self,
        name: str,
        max_age_seconds: int = 30
    ) -> bool:
        """Check if cached result is stale.

        Args:
            name: Check name
            max_age_seconds: Maximum age in seconds

        Returns:
            True if stale or missing
        """
        result = self.results.get(name)
        if not result or not result.timestamp:
            return True

        age = datetime.now(timezone.utc) - result.timestamp
        return age > timedelta(seconds=max_age_seconds)


# Common health check implementations

async def redis_health_check() -> HealthCheckResult:
    """Check Redis connectivity.

    Uses Redis MCP to verify connectivity.

    Returns:
        Health check result
    """
    try:
        # In production, this would use MCP to ping Redis:
        # result = mcp__RedisMCPServer__ping()
        # For Phase 0.5, we use the registry's health check
        from mycelium.registry.client import RegistryClient

        registry = RegistryClient()
        is_healthy = registry.health_check()

        if is_healthy:
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Redis is reachable",
            )
        else:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message="Redis is not responding",
            )
    except Exception as e:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message=f"Redis unreachable: {str(e)}",
        )


async def registry_health_check() -> HealthCheckResult:
    """Check agent registry health.

    Returns:
        Health check result
    """
    from mycelium.registry.client import RegistryClient

    try:
        registry = RegistryClient()
        is_healthy = registry.health_check()

        if is_healthy:
            stats = registry.get_stats()
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Registry is operational",
                details={k: float(v) for k, v in stats.items()},
            )
        else:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message="Registry is not responding",
            )
    except Exception as e:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message=f"Registry check failed: {str(e)}",
        )


async def supervisor_health_check() -> HealthCheckResult:
    """Check process supervisor health.

    Returns:
        Health check result
    """
    from mycelium.supervisor.manager import ProcessManager

    try:
        supervisor = ProcessManager()
        # Check if supervisor is operational
        # For Phase 0.5, verify we can access the process manager
        process_count = len(supervisor.processes)

        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message="Supervisor is operational",
            details={"managed_processes": float(process_count)},
        )
    except Exception as e:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message=f"Supervisor check failed: {str(e)}",
        )
