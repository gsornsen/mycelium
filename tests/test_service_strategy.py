"""Tests for service deployment strategy module.

This module tests the smart service detection and reuse logic,
including strategy selection, deployment planning, and compatibility checking.
"""

from __future__ import annotations

import pytest

from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.deployment.strategy import (
    CompatibilityLevel,
    DeploymentPlanSummary,
    DetectedService,
    ServiceDeploymentPlan,
    ServiceDeploymentPlanner,
    ServiceStatus,
    ServiceStrategy,
    ServiceType,
    VersionRequirement,
)


class TestVersionRequirement:
    """Test version requirement checking."""

    def test_version_requirement_creation(self):
        """Test creating version requirements."""
        req = VersionRequirement(min_version="6.0", preferred_version="7.0")
        assert req.min_version == "6.0"
        assert req.preferred_version == "7.0"

    def test_is_compatible_returns_compatible(self):
        """Test version compatibility check returns compatible."""
        req = VersionRequirement(min_version="6.0")
        result = req.is_compatible("7.2.0")
        assert result == CompatibilityLevel.COMPATIBLE


class TestServiceDeploymentPlan:
    """Test service deployment plan model."""

    def test_plan_creation(self):
        """Test creating a service deployment plan."""
        plan = ServiceDeploymentPlan(
            service_name="redis",
            strategy=ServiceStrategy.REUSE,
            host="localhost",
            port=6379,
            version="7.2.0",
            connection_string="redis://localhost:6379/0",
            reason="Compatible version detected",
        )

        assert plan.service_name == "redis"
        assert plan.strategy == ServiceStrategy.REUSE
        assert plan.port == 6379
        assert plan.is_reusing_existing
        assert not plan.is_creating_new

    def test_plan_with_create_strategy(self):
        """Test plan with CREATE strategy."""
        plan = ServiceDeploymentPlan(
            service_name="postgres",
            strategy=ServiceStrategy.CREATE,
            host="localhost",
            port=5432,
            version="15",
            connection_string="postgresql://localhost:5432/mycelium",
            reason="No existing service detected",
            container_name="mycelium-postgres",
        )

        assert plan.strategy == ServiceStrategy.CREATE
        assert not plan.is_reusing_existing
        assert plan.is_creating_new
        assert plan.container_name == "mycelium-postgres"

    def test_plan_with_alongside_strategy(self):
        """Test plan with ALONGSIDE strategy."""
        plan = ServiceDeploymentPlan(
            service_name="redis",
            strategy=ServiceStrategy.ALONGSIDE,
            host="localhost",
            port=6380,
            version="7.2.0",
            connection_string="redis://localhost:6380/0",
            reason="Incompatible version, running alongside",
            compatibility_level=CompatibilityLevel.MAJOR_MISMATCH,
            metadata={"existing_service_port": 6379},
        )

        assert plan.strategy == ServiceStrategy.ALONGSIDE
        assert plan.is_creating_new
        assert plan.port == 6380
        assert plan.metadata["existing_service_port"] == 6379

    def test_plan_to_dict(self):
        """Test converting plan to dictionary."""
        plan = ServiceDeploymentPlan(
            service_name="redis",
            strategy=ServiceStrategy.REUSE,
            host="localhost",
            port=6379,
            version="7.2.0",
            connection_string="redis://localhost:6379/0",
            reason="Compatible version",
        )

        plan_dict = plan.to_dict()
        assert plan_dict["service_name"] == "redis"
        assert plan_dict["strategy"] == "reuse"
        assert plan_dict["port"] == 6379


class TestDeploymentPlanSummary:
    """Test deployment plan summary model."""

    def test_summary_creation(self):
        """Test creating deployment plan summary."""
        summary = DeploymentPlanSummary(
            plan_id="deploy-test-001",
            project_name="test-project",
        )

        assert summary.plan_id == "deploy-test-001"
        assert summary.project_name == "test-project"
        assert len(summary.services_to_reuse) == 0
        assert len(summary.services_to_create) == 0

    def test_add_service_plan_reuse(self):
        """Test adding a REUSE service plan."""
        summary = DeploymentPlanSummary(
            plan_id="test",
            project_name="test",
        )

        plan = ServiceDeploymentPlan(
            service_name="redis",
            strategy=ServiceStrategy.REUSE,
            host="localhost",
            port=6379,
            version="7.2.0",
            connection_string="redis://localhost:6379/0",
            reason="Compatible version",
        )

        summary.add_service_plan(plan)

        assert "redis" in summary.services_to_reuse
        assert "redis" not in summary.services_to_create
        assert summary.get_service_plan("redis") == plan

    def test_add_service_plan_create(self):
        """Test adding a CREATE service plan."""
        summary = DeploymentPlanSummary(
            plan_id="test",
            project_name="test",
        )

        plan = ServiceDeploymentPlan(
            service_name="postgres",
            strategy=ServiceStrategy.CREATE,
            host="localhost",
            port=5432,
            version="15",
            connection_string="postgresql://localhost:5432/mycelium",
            reason="No existing service",
        )

        summary.add_service_plan(plan)

        assert "postgres" in summary.services_to_create
        assert "postgres" not in summary.services_to_reuse

    def test_has_services_to_deploy(self):
        """Test checking if deployment has services to deploy."""
        summary = DeploymentPlanSummary(
            plan_id="test",
            project_name="test",
        )

        assert not summary.has_services_to_deploy

        # Add CREATE plan
        plan = ServiceDeploymentPlan(
            service_name="redis",
            strategy=ServiceStrategy.CREATE,
            host="localhost",
            port=6379,
            version="7.2.0",
            connection_string="redis://localhost:6379/0",
            reason="No existing service",
        )
        summary.add_service_plan(plan)

        assert summary.has_services_to_deploy

    def test_generate_docker_compose_context(self):
        """Test generating context for docker-compose template."""
        summary = DeploymentPlanSummary(
            plan_id="test",
            project_name="test",
        )

        # Add REUSE plan
        reuse_plan = ServiceDeploymentPlan(
            service_name="redis",
            strategy=ServiceStrategy.REUSE,
            host="localhost",
            port=6379,
            version="7.2.0",
            connection_string="redis://localhost:6379/0",
            reason="Existing service",
        )
        summary.add_service_plan(reuse_plan)

        # Add CREATE plan
        create_plan = ServiceDeploymentPlan(
            service_name="postgres",
            strategy=ServiceStrategy.CREATE,
            host="localhost",
            port=5432,
            version="15",
            connection_string="postgresql://localhost:5432/mycelium",
            reason="No existing service",
            container_name="test-postgres",
        )
        summary.add_service_plan(create_plan)

        context = summary.generate_docker_compose_context()

        # Verify reused service
        assert "redis" in context["services_reused"]
        assert context["services_reused"]["redis"]["port"] == 6379

        # Verify created service
        assert "postgres" in context["services_to_deploy"]
        assert context["services_to_deploy"]["postgres"]["port"] == 5432
        assert context["services_to_deploy"]["postgres"]["container_name"] == "test-postgres"

        # Verify connection info
        assert "redis" in context["connection_info"]
        assert "postgres" in context["connection_info"]


class TestServiceDeploymentPlanner:
    """Test service deployment planner."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MyceliumConfig(project_name="test-project")

    @pytest.fixture
    def redis_detected(self):
        """Create detected Redis service."""
        return DetectedService(
            name="redis",
            service_type=ServiceType.REDIS,
            status=ServiceStatus.RUNNING,
            version="7.2.0",
            host="localhost",
            port=6379,
        )

    @pytest.fixture
    def postgres_detected(self):
        """Create detected PostgreSQL service."""
        return DetectedService(
            name="postgres",
            service_type=ServiceType.POSTGRESQL,
            status=ServiceStatus.RUNNING,
            version="15.0",
            host="localhost",
            port=5432,
        )

    def test_planner_creation(self, config):
        """Test creating deployment planner."""
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[],
        )

        assert planner.config == config
        assert planner.prefer_reuse is True

    def test_plan_redis_reuse(self, config, redis_detected):
        """Test planning Redis with REUSE strategy."""
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[redis_detected],
            prefer_reuse=True,
        )

        plan = planner._plan_redis()

        assert plan.service_name == "redis"
        assert plan.strategy == ServiceStrategy.REUSE
        assert plan.port == 6379
        assert plan.host == "localhost"
        assert "Compatible" in plan.reason

    def test_plan_redis_create(self, config):
        """Test planning Redis with CREATE strategy."""
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[],
        )

        plan = planner._plan_redis()

        assert plan.service_name == "redis"
        assert plan.strategy == ServiceStrategy.CREATE
        assert plan.port == config.services.redis.port
        assert plan.container_name == "test-project-redis"
        assert "No compatible" in plan.reason

    def test_plan_postgres_reuse(self, config, postgres_detected):
        """Test planning PostgreSQL with REUSE strategy."""
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[postgres_detected],
            prefer_reuse=True,
        )

        plan = planner._plan_postgres()

        assert plan.service_name == "postgres"
        assert plan.strategy == ServiceStrategy.REUSE
        assert plan.port == 5432
        assert plan.requires_configuration is True

    def test_plan_postgres_create(self, config):
        """Test planning PostgreSQL with CREATE strategy."""
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[],
        )

        plan = planner._plan_postgres()

        assert plan.service_name == "postgres"
        assert plan.strategy == ServiceStrategy.CREATE
        assert plan.container_name == "test-project-postgres"

    def test_create_full_deployment_plan(self, config, redis_detected, postgres_detected):
        """Test creating complete deployment plan."""
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[redis_detected, postgres_detected],
        )

        plan = planner.create_deployment_plan()

        assert plan.project_name == "test-project"
        assert "redis" in plan.services_to_reuse
        assert "postgres" in plan.services_to_reuse
        assert "temporal" in plan.services_to_create  # Temporal always created

    def test_create_plan_with_no_detected_services(self, config):
        """Test creating plan when no services are detected."""
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[],
        )

        plan = planner.create_deployment_plan()

        assert len(plan.services_to_reuse) == 0
        assert "redis" in plan.services_to_create
        assert "postgres" in plan.services_to_create
        assert "temporal" in plan.services_to_create

    def test_alongside_port_calculation(self, config):
        """Test port calculation for ALONGSIDE strategy."""
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[],
        )

        redis_port = planner._calculate_alongside_port(ServiceType.REDIS, 6379)
        assert redis_port == 6380  # Redis offset is 1

        postgres_port = planner._calculate_alongside_port(ServiceType.POSTGRESQL, 5432)
        assert postgres_port == 5433  # PostgreSQL offset is 1

    def test_recommendations_added_to_plan(self, config, redis_detected):
        """Test that recommendations are added to plan."""
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[redis_detected],
        )

        plan = planner.create_deployment_plan()

        # Should have recommendations about reused services
        assert len(plan.recommendations) > 0
        assert any("redis" in rec.lower() for rec in plan.recommendations)

    def test_build_connection_strings(self, config):
        """Test connection string building."""
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[],
        )

        redis_conn = planner._build_redis_connection("localhost", 6379)
        assert redis_conn == "redis://localhost:6379/0"

        postgres_conn = planner._build_postgres_connection("localhost", 5432, "mycelium")
        assert "postgresql://" in postgres_conn
        assert "localhost:5432" in postgres_conn
        assert "mycelium" in postgres_conn


class TestServiceStrategy:
    """Test ServiceStrategy enum."""

    def test_strategy_values(self):
        """Test strategy enum values."""
        assert ServiceStrategy.REUSE.value == "reuse"
        assert ServiceStrategy.CREATE.value == "create"
        assert ServiceStrategy.ALONGSIDE.value == "alongside"
        assert ServiceStrategy.SKIP.value == "skip"

    def test_strategy_comparison(self):
        """Test strategy comparison."""
        assert ServiceStrategy.REUSE == ServiceStrategy.REUSE
        assert ServiceStrategy.REUSE != ServiceStrategy.CREATE


class TestCompatibilityLevel:
    """Test CompatibilityLevel enum."""

    def test_compatibility_values(self):
        """Test compatibility level values."""
        assert CompatibilityLevel.COMPATIBLE.value == "compatible"
        assert CompatibilityLevel.MINOR_MISMATCH.value == "minor_mismatch"
        assert CompatibilityLevel.MAJOR_MISMATCH.value == "major_mismatch"
        assert CompatibilityLevel.UNKNOWN.value == "unknown"
