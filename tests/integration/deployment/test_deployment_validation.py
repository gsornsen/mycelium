"""Integration tests for deployment validation.

These tests validate actual Temporal + PostgreSQL deployments, checking:
- Service health and connectivity
- Integration between services
- Data persistence
- Configuration correctness
"""

import asyncio
import os
import socket

import pytest

from mycelium_onboarding.deployment.validation import (
    DeploymentValidator,
    HealthStatus,
    ServiceType,
    validate_deployment,
)

# Test configuration from environment or defaults
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5433"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "changeme")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE", "temporal")

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost")
TEMPORAL_PORT = int(os.getenv("TEMPORAL_PORT", "7233"))
TEMPORAL_UI_PORT = int(os.getenv("TEMPORAL_UI_PORT", "8080"))
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")


def is_temporal_available() -> bool:
    """Check if Temporal server is accessible on configured host/port.

    Returns True if can connect to Temporal gRPC port, False otherwise.
    This allows tests to gracefully skip when Temporal is not available.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((TEMPORAL_HOST, TEMPORAL_PORT))
        sock.close()
        return result == 0
    except Exception:
        return False


# Skip marker for tests that require Temporal
requires_temporal = pytest.mark.skipif(
    not is_temporal_available(),
    reason=f"Temporal server not available at {TEMPORAL_HOST}:{TEMPORAL_PORT}. "
    "This is expected in CI until Tier 2 Temporal setup is implemented.",
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestDeploymentValidation:
    """Integration tests for deployment validation."""

    @requires_temporal
    async def test_validate_deployment_basic(self):
        """Test basic deployment validation."""
        validator = DeploymentValidator()
        report = await validator.validate(
            postgres_host=POSTGRES_HOST,
            postgres_port=POSTGRES_PORT,
            postgres_database=POSTGRES_DATABASE,
            postgres_user=POSTGRES_USER,
            postgres_password=POSTGRES_PASSWORD,
            temporal_host=TEMPORAL_HOST,
            temporal_port=TEMPORAL_PORT,
            temporal_ui_port=TEMPORAL_UI_PORT,
            temporal_namespace=TEMPORAL_NAMESPACE,
        )

        # Basic assertions
        assert report is not None
        assert report.deployment_id is not None
        assert len(report.services) >= 2  # At least PostgreSQL and Temporal
        assert report.total_checks > 0
        assert report.can_proceed()  # Deployment can proceed

    async def test_postgresql_health(self):
        """Test PostgreSQL service health check."""
        validator = DeploymentValidator()
        health = await validator.validate_postgresql(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DATABASE,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )

        assert health is not None
        assert health.service_name == "postgresql"
        assert health.service_type == ServiceType.POSTGRESQL
        assert health.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        assert health.can_operate()
        assert len(health.checks_passed) > 0
        assert health.version is not None

    async def test_postgresql_port_connectivity(self):
        """Test PostgreSQL port connectivity."""
        validator = DeploymentValidator()
        health = await validator.validate_postgresql(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DATABASE,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )

        # Port connectivity check should pass
        assert any("Port Connectivity" in check for check in health.checks_passed)

    async def test_postgresql_version_detection(self):
        """Test PostgreSQL version detection."""
        validator = DeploymentValidator()
        health = await validator.validate_postgresql(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DATABASE,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )

        # Version should be detected
        assert health.version is not None
        assert "15" in health.version  # We're using PostgreSQL 15.3

    async def test_postgresql_database_connection(self):
        """Test PostgreSQL database connection."""
        validator = DeploymentValidator()
        health = await validator.validate_postgresql(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DATABASE,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )

        # Database connection check should pass
        assert any("Database Connection" in check for check in health.checks_passed)

    async def test_postgresql_temporal_schema(self):
        """Test Temporal schema validation in PostgreSQL."""
        validator = DeploymentValidator()
        health = await validator.validate_postgresql(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DATABASE,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )

        # Temporal schema check should exist
        # May pass or fail depending on initialization state
        schema_checks = [c for c in health.checks_passed + health.checks_failed if "Temporal Schema" in c]
        assert len(schema_checks) > 0

    async def test_postgresql_connection_pool(self):
        """Test PostgreSQL connection pool check."""
        validator = DeploymentValidator()
        health = await validator.validate_postgresql(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DATABASE,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )

        # Connection pool check should exist
        pool_checks = [c for c in health.checks_passed + health.checks_failed if "Connection Pool" in c]
        assert len(pool_checks) > 0

    async def test_postgresql_response_time(self):
        """Test PostgreSQL response time measurement."""
        validator = DeploymentValidator()
        health = await validator.validate_postgresql(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DATABASE,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )

        # Response time should be measured
        assert health.response_time_ms is not None
        assert health.response_time_ms > 0
        assert health.response_time_ms < 10000  # Less than 10 seconds

    @requires_temporal
    async def test_temporal_health(self):
        """Test Temporal service health check."""
        validator = DeploymentValidator()
        health = await validator.validate_temporal(
            host=TEMPORAL_HOST,
            port=TEMPORAL_PORT,
            namespace=TEMPORAL_NAMESPACE,
        )

        assert health is not None
        assert health.service_name == "temporal"
        assert health.service_type == ServiceType.TEMPORAL
        assert health.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        assert health.can_operate()
        assert len(health.checks_passed) > 0

    @requires_temporal
    async def test_temporal_port_connectivity(self):
        """Test Temporal gRPC port connectivity."""
        validator = DeploymentValidator()
        health = await validator.validate_temporal(
            host=TEMPORAL_HOST,
            port=TEMPORAL_PORT,
            namespace=TEMPORAL_NAMESPACE,
        )

        # gRPC port connectivity check should pass
        assert any("gRPC Port Connectivity" in check for check in health.checks_passed)

    @requires_temporal
    async def test_temporal_cluster_health(self):
        """Test Temporal cluster health check."""
        validator = DeploymentValidator()
        health = await validator.validate_temporal(
            host=TEMPORAL_HOST,
            port=TEMPORAL_PORT,
            namespace=TEMPORAL_NAMESPACE,
        )

        # Cluster health check should exist
        assert any("Cluster Health" in check for check in health.checks_passed)

    @requires_temporal
    async def test_temporal_namespace_check(self):
        """Test Temporal namespace existence check."""
        validator = DeploymentValidator()
        health = await validator.validate_temporal(
            host=TEMPORAL_HOST,
            port=TEMPORAL_PORT,
            namespace=TEMPORAL_NAMESPACE,
        )

        # Namespace check should exist
        namespace_checks = [c for c in health.checks_passed + health.checks_failed if "Namespace Exists" in c]
        assert len(namespace_checks) > 0

    @requires_temporal
    async def test_temporal_frontend_service(self):
        """Test Temporal frontend service check."""
        validator = DeploymentValidator()
        health = await validator.validate_temporal(
            host=TEMPORAL_HOST,
            port=TEMPORAL_PORT,
            namespace=TEMPORAL_NAMESPACE,
        )

        # Frontend service check should pass
        assert any("Frontend Service" in check for check in health.checks_passed)

    @requires_temporal
    async def test_temporal_response_time(self):
        """Test Temporal response time measurement."""
        validator = DeploymentValidator()
        health = await validator.validate_temporal(
            host=TEMPORAL_HOST,
            port=TEMPORAL_PORT,
            namespace=TEMPORAL_NAMESPACE,
        )

        # Response time should be measured
        assert health.response_time_ms is not None
        assert health.response_time_ms > 0
        assert health.response_time_ms < 5000  # Less than 5 seconds

    @requires_temporal
    async def test_temporal_ui_health(self):
        """Test Temporal UI health check."""
        validator = DeploymentValidator()
        health = await validator.validate_temporal_ui(
            host=TEMPORAL_HOST,
            port=TEMPORAL_UI_PORT,
        )

        assert health is not None
        assert health.service_name == "temporal-ui"
        assert health.service_type == ServiceType.TEMPORAL_UI
        # UI may be degraded but still functional
        assert health.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]

    @requires_temporal
    async def test_temporal_ui_port_connectivity(self):
        """Test Temporal UI HTTP port connectivity."""
        validator = DeploymentValidator()
        health = await validator.validate_temporal_ui(
            host=TEMPORAL_HOST,
            port=TEMPORAL_UI_PORT,
        )

        # Port connectivity check should exist
        port_checks = [c for c in health.checks_passed + health.checks_failed if "HTTP Port Connectivity" in c]
        assert len(port_checks) > 0

    @requires_temporal
    async def test_integration_checks_in_full_validation(self):
        """Test that integration checks run in full validation."""
        validator = DeploymentValidator()
        report = await validator.validate(
            postgres_host=POSTGRES_HOST,
            postgres_port=POSTGRES_PORT,
            postgres_database=POSTGRES_DATABASE,
            postgres_user=POSTGRES_USER,
            postgres_password=POSTGRES_PASSWORD,
            temporal_host=TEMPORAL_HOST,
            temporal_port=TEMPORAL_PORT,
            temporal_ui_port=TEMPORAL_UI_PORT,
            temporal_namespace=TEMPORAL_NAMESPACE,
        )

        # Integration checks should be present
        assert len(report.integration_checks) > 0

    async def test_overall_status_computation(self):
        """Test overall deployment status computation."""
        validator = DeploymentValidator()
        report = await validator.validate(
            postgres_host=POSTGRES_HOST,
            postgres_port=POSTGRES_PORT,
            postgres_database=POSTGRES_DATABASE,
            postgres_user=POSTGRES_USER,
            postgres_password=POSTGRES_PASSWORD,
            temporal_host=TEMPORAL_HOST,
            temporal_port=TEMPORAL_PORT,
            temporal_ui_port=TEMPORAL_UI_PORT,
            temporal_namespace=TEMPORAL_NAMESPACE,
        )

        # Overall status should be computed
        assert report.overall_status in [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY,
        ]
        # Should not be "not deployed" since we're testing a deployment
        assert report.overall_status != HealthStatus.NOT_DEPLOYED

    async def test_validation_report_formatting(self):
        """Test validation report formatting."""
        validator = DeploymentValidator()
        report = await validator.validate(
            postgres_host=POSTGRES_HOST,
            postgres_port=POSTGRES_PORT,
            postgres_database=POSTGRES_DATABASE,
            postgres_user=POSTGRES_USER,
            postgres_password=POSTGRES_PASSWORD,
            temporal_host=TEMPORAL_HOST,
            temporal_port=TEMPORAL_PORT,
            temporal_ui_port=TEMPORAL_UI_PORT,
            temporal_namespace=TEMPORAL_NAMESPACE,
        )

        # Report should format correctly
        summary = report.format_summary()
        assert summary is not None
        assert len(summary) > 0
        assert "Deployment Validation Report" in summary
        assert "Overall Status" in summary
        assert "Services:" in summary

    async def test_recommendations_generated(self):
        """Test that recommendations are generated."""
        validator = DeploymentValidator()
        report = await validator.validate(
            postgres_host=POSTGRES_HOST,
            postgres_port=POSTGRES_PORT,
            postgres_database=POSTGRES_DATABASE,
            postgres_user=POSTGRES_USER,
            postgres_password=POSTGRES_PASSWORD,
            temporal_host=TEMPORAL_HOST,
            temporal_port=TEMPORAL_PORT,
            temporal_ui_port=TEMPORAL_UI_PORT,
            temporal_namespace=TEMPORAL_NAMESPACE,
        )

        # Recommendations should be present
        assert len(report.recommendations) > 0

    async def test_statistics_accurate(self):
        """Test that validation statistics are accurate."""
        validator = DeploymentValidator()
        report = await validator.validate(
            postgres_host=POSTGRES_HOST,
            postgres_port=POSTGRES_PORT,
            postgres_database=POSTGRES_DATABASE,
            postgres_user=POSTGRES_USER,
            postgres_password=POSTGRES_PASSWORD,
            temporal_host=TEMPORAL_HOST,
            temporal_port=TEMPORAL_PORT,
            temporal_ui_port=TEMPORAL_UI_PORT,
            temporal_namespace=TEMPORAL_NAMESPACE,
        )

        # Statistics should be consistent
        assert report.total_checks == report.passed_checks + report.failed_checks
        assert report.total_checks > 0
        assert report.passed_checks >= 0
        assert report.failed_checks >= 0

    @requires_temporal
    async def test_validate_deployment_convenience_function(self):
        """Test convenience function for deployment validation."""
        report = await validate_deployment(
            postgres_host=POSTGRES_HOST,
            postgres_port=POSTGRES_PORT,
            postgres_database=POSTGRES_DATABASE,
            postgres_user=POSTGRES_USER,
            postgres_password=POSTGRES_PASSWORD,
            temporal_host=TEMPORAL_HOST,
            temporal_port=TEMPORAL_PORT,
            temporal_ui_port=TEMPORAL_UI_PORT,
            temporal_namespace=TEMPORAL_NAMESPACE,
        )

        assert report is not None
        assert report.can_proceed()

    @requires_temporal
    async def test_service_restart_recovery(self):
        """Test that validator can detect and handle service restart scenarios."""
        validator = DeploymentValidator(retry_attempts=2, retry_delay=1.0)

        # First validation
        report1 = await validator.validate(
            postgres_host=POSTGRES_HOST,
            postgres_port=POSTGRES_PORT,
            postgres_database=POSTGRES_DATABASE,
            postgres_user=POSTGRES_USER,
            postgres_password=POSTGRES_PASSWORD,
            temporal_host=TEMPORAL_HOST,
            temporal_port=TEMPORAL_PORT,
            temporal_ui_port=TEMPORAL_UI_PORT,
            temporal_namespace=TEMPORAL_NAMESPACE,
        )

        # Services should still be operational
        assert report1.can_proceed()

        # Second validation (immediate retry)
        report2 = await validator.validate(
            postgres_host=POSTGRES_HOST,
            postgres_port=POSTGRES_PORT,
            postgres_database=POSTGRES_DATABASE,
            postgres_user=POSTGRES_USER,
            postgres_password=POSTGRES_PASSWORD,
            temporal_host=TEMPORAL_HOST,
            temporal_port=TEMPORAL_PORT,
            temporal_ui_port=TEMPORAL_UI_PORT,
            temporal_namespace=TEMPORAL_NAMESPACE,
        )

        # Results should be consistent
        assert report2.can_proceed()


@pytest.mark.integration
class TestDeploymentValidationSync:
    """Synchronous wrapper tests for deployment validation."""

    @requires_temporal
    def test_deployment_validation_sync(self):
        """Test synchronous execution of deployment validation."""

        async def run_validation():
            return await validate_deployment(
                postgres_host=POSTGRES_HOST,
                postgres_port=POSTGRES_PORT,
                postgres_database=POSTGRES_DATABASE,
                postgres_user=POSTGRES_USER,
                postgres_password=POSTGRES_PASSWORD,
                temporal_host=TEMPORAL_HOST,
                temporal_port=TEMPORAL_PORT,
                temporal_ui_port=TEMPORAL_UI_PORT,
                temporal_namespace=TEMPORAL_NAMESPACE,
            )

        report = asyncio.run(run_validation())
        assert report is not None
        assert report.can_proceed()
