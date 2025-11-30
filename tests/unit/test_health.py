"""Unit tests for health checks."""

import pytest

from mycelium.health.checker import (
    HealthChecker,
    HealthCheckResult,
    HealthStatus,
)


@pytest.fixture
def health_checker():
    """Create health checker instance."""
    return HealthChecker()


@pytest.mark.asyncio
async def test_register_and_run_check(health_checker):
    """Test registering and running a health check."""

    async def dummy_check():
        return HealthCheckResult(status=HealthStatus.HEALTHY, message="All good")

    health_checker.register_check("dummy", dummy_check)
    result = await health_checker.run_check("dummy")

    assert result.status == HealthStatus.HEALTHY
    assert result.message == "All good"
    assert result.latency_ms is not None


@pytest.mark.asyncio
async def test_run_all_checks(health_checker):
    """Test running all checks."""

    async def check1():
        return HealthCheckResult(status=HealthStatus.HEALTHY)

    async def check2():
        return HealthCheckResult(status=HealthStatus.HEALTHY)

    health_checker.register_check("check1", check1)
    health_checker.register_check("check2", check2)

    results = await health_checker.run_all_checks()

    assert len(results) == 2
    assert "check1" in results
    assert "check2" in results


@pytest.mark.asyncio
async def test_overall_status_all_healthy(health_checker):
    """Test overall status when all checks are healthy."""

    async def healthy_check():
        return HealthCheckResult(status=HealthStatus.HEALTHY)

    health_checker.register_check("check1", healthy_check)
    health_checker.register_check("check2", healthy_check)

    await health_checker.run_all_checks()
    status = health_checker.get_overall_status()

    assert status == HealthStatus.HEALTHY


@pytest.mark.asyncio
async def test_overall_status_with_unhealthy(health_checker):
    """Test overall status when one check is unhealthy."""

    async def healthy_check():
        return HealthCheckResult(status=HealthStatus.HEALTHY)

    async def unhealthy_check():
        return HealthCheckResult(status=HealthStatus.UNHEALTHY)

    health_checker.register_check("healthy", healthy_check)
    health_checker.register_check("unhealthy", unhealthy_check)

    await health_checker.run_all_checks()
    status = health_checker.get_overall_status()

    assert status == HealthStatus.UNHEALTHY


def test_list_checks(health_checker):
    """Test listing registered checks."""

    async def dummy_check():
        return HealthCheckResult(status=HealthStatus.HEALTHY)

    health_checker.register_check("check1", dummy_check)
    health_checker.register_check("check2", dummy_check)

    checks = health_checker.list_checks()

    assert len(checks) == 2
    assert "check1" in checks
    assert "check2" in checks
