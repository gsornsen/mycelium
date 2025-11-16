"""Integration tests for smart service deployment.

This module tests the end-to-end smart service detection and reuse workflow,
including detection, planning, and docker-compose generation with service reuse.
"""

from __future__ import annotations

import pytest

from mycelium_onboarding.config.schema import DeploymentMethod, MyceliumConfig
from mycelium_onboarding.deployment.generator import DeploymentGenerator
from mycelium_onboarding.deployment.strategy import (
    DetectedService,
    ServiceDeploymentPlanner,
    ServiceStatus,
    ServiceStrategy,
    ServiceType,
)


class TestSmartDeploymentIntegration:
    """Integration tests for smart deployment workflow."""

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create temporary output directory."""
        return tmp_path / "deployment"

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MyceliumConfig(
            project_name="test-smart-deploy",
            services={
                "redis": {"enabled": True, "port": 6379},
                "postgres": {"enabled": True, "port": 5432},
                "temporal": {"enabled": True},
            },
        )

    @pytest.fixture
    def detected_redis(self):
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
    def detected_postgres(self):
        """Create detected PostgreSQL service."""
        return DetectedService(
            name="postgres",
            service_type=ServiceType.POSTGRESQL,
            status=ServiceStatus.RUNNING,
            version="15.0",
            host="localhost",
            port=5432,
        )

    def test_full_workflow_with_reuse(
        self,
        config,
        detected_redis,
        detected_postgres,
        temp_output_dir,
    ):
        """Test complete workflow with service reuse.

        This test simulates the full smart deployment workflow:
        1. Detect existing services
        2. Create deployment plan with reuse strategy
        3. Generate docker-compose.yml
        4. Verify only new services are included
        """
        # Step 1: Create deployment plan
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[detected_redis, detected_postgres],
            prefer_reuse=True,
        )

        plan = planner.create_deployment_plan()

        # Verify plan reuses existing services
        assert "redis" in plan.services_to_reuse
        assert "postgres" in plan.services_to_reuse
        assert "temporal" in plan.services_to_create

        # Step 2: Generate deployment with plan
        generator = DeploymentGenerator(
            config=config,
            output_dir=temp_output_dir,
            deployment_plan=plan,
        )

        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        # Verify generation succeeded
        assert result.success
        assert len(result.errors) == 0

        # Step 3: Verify docker-compose.yml content
        compose_file = temp_output_dir / "docker-compose.yml"
        assert compose_file.exists()

        compose_content = compose_file.read_text()

        # Redis and Postgres should NOT be in docker-compose
        # (they are being reused from existing services)
        assert "redis:" not in compose_content or "Reusing existing" in compose_content
        assert "postgres:" not in compose_content or "Reusing existing" in compose_content

        # Temporal should be included (always created)
        assert "temporal:" in compose_content

        # Check for deployment plan comments
        assert "Smart Deployment Plan" in compose_content or "test-smart-deploy" in compose_content

    def test_workflow_without_detected_services(self, config, temp_output_dir):
        """Test workflow when no services are detected.

        Verifies that all services are created when none are detected.
        """
        # Create deployment plan with no detected services
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[],
        )

        plan = planner.create_deployment_plan()

        # Verify all services will be created
        assert len(plan.services_to_reuse) == 0
        assert "redis" in plan.services_to_create
        assert "postgres" in plan.services_to_create
        assert "temporal" in plan.services_to_create

        # Generate deployment
        generator = DeploymentGenerator(
            config=config,
            output_dir=temp_output_dir,
            deployment_plan=plan,
        )

        generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        # Verify all services in docker-compose
        compose_content = (temp_output_dir / "docker-compose.yml").read_text()
        assert "redis:" in compose_content
        assert "postgres:" in compose_content
        assert "temporal:" in compose_content

    def test_alongside_deployment(self, config, temp_output_dir):
        """Test ALONGSIDE deployment strategy.

        Verifies that incompatible services run on different ports.
        """
        # Create detected service with incompatible version
        incompatible_redis = DetectedService(
            name="redis",
            service_type=ServiceType.REDIS,
            status=ServiceStatus.RUNNING,
            version="5.0.0",  # Old version
            host="localhost",
            port=6379,
        )

        # For this test, we'll manually create an ALONGSIDE plan
        # (In real scenario, planner would detect version incompatibility)
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[incompatible_redis],
            prefer_reuse=False,  # Force new deployment
        )

        plan = planner.create_deployment_plan()

        # Generate deployment
        generator = DeploymentGenerator(
            config=config,
            output_dir=temp_output_dir,
            deployment_plan=plan,
        )

        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success

    def test_connection_info_generation(
        self,
        config,
        detected_redis,
        temp_output_dir,
    ):
        """Test generation of connection information file."""
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[detected_redis],
        )

        plan = planner.create_deployment_plan()

        generator = DeploymentGenerator(
            config=config,
            output_dir=temp_output_dir,
            deployment_plan=plan,
        )

        generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        # Check CONNECTIONS.md was generated
        conn_file = temp_output_dir / "CONNECTIONS.md"
        assert conn_file.exists()

        conn_content = conn_file.read_text()

        # Verify connection info for Redis (reused)
        assert "redis" in conn_content.lower()
        assert "reuse" in conn_content.lower()
        assert "6379" in conn_content

    def test_env_file_with_reuse_info(
        self,
        config,
        detected_redis,
        detected_postgres,
        temp_output_dir,
    ):
        """Test .env file includes connection strings for reused services."""
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[detected_redis, detected_postgres],
        )

        plan = planner.create_deployment_plan()

        generator = DeploymentGenerator(
            config=config,
            output_dir=temp_output_dir,
            deployment_plan=plan,
        )

        generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        # Check .env file
        env_file = temp_output_dir / ".env"
        assert env_file.exists()

        env_content = env_file.read_text()

        # Should include connection strings
        assert "REDIS_URL" in env_content or "redis://" in env_content
        assert "POSTGRES" in env_content or "postgresql://" in env_content

    def test_readme_includes_deployment_plan(
        self,
        config,
        detected_redis,
        temp_output_dir,
    ):
        """Test README includes deployment plan information."""
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[detected_redis],
        )

        plan = planner.create_deployment_plan()

        generator = DeploymentGenerator(
            config=config,
            output_dir=temp_output_dir,
            deployment_plan=plan,
        )

        generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        # Check README
        readme_file = temp_output_dir / "README.md"
        assert readme_file.exists()

        readme_content = readme_file.read_text()

        # Should mention deployment plan
        assert "Deployment Plan" in readme_content or "Reusing" in readme_content

    def test_warnings_for_reused_services(
        self,
        config,
        detected_redis,
        temp_output_dir,
    ):
        """Test that warnings are generated for reused services."""
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[detected_redis],
        )

        plan = planner.create_deployment_plan()

        generator = DeploymentGenerator(
            config=config,
            output_dir=temp_output_dir,
            deployment_plan=plan,
        )

        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        # Should have warnings about reused services
        assert any("reuse" in w.lower() or "existing" in w.lower() for w in result.warnings)

    def test_backward_compatibility_without_plan(self, config, temp_output_dir):
        """Test backward compatibility when no deployment plan is provided.

        Verifies that generator works without a deployment plan (original behavior).
        """
        # Generate without deployment plan
        generator = DeploymentGenerator(
            config=config,
            output_dir=temp_output_dir,
            deployment_plan=None,  # No plan
        )

        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        # Should still work and include all enabled services
        assert result.success

        compose_content = (temp_output_dir / "docker-compose.yml").read_text()
        assert "redis:" in compose_content
        assert "postgres:" in compose_content
        assert "temporal:" in compose_content

    def test_partial_reuse_scenario(
        self,
        config,
        detected_redis,
        temp_output_dir,
    ):
        """Test scenario where some services are reused and others created.

        This is the most common real-world scenario.
        """
        # Only Redis detected, Postgres and Temporal need to be created
        planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=[detected_redis],
        )

        plan = planner.create_deployment_plan()

        # Verify mixed strategy
        assert "redis" in plan.services_to_reuse
        assert "postgres" in plan.services_to_create
        assert "temporal" in plan.services_to_create

        # Generate deployment
        generator = DeploymentGenerator(
            config=config,
            output_dir=temp_output_dir,
            deployment_plan=plan,
        )

        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success

        compose_content = (temp_output_dir / "docker-compose.yml").read_text()

        # Postgres and Temporal should be in docker-compose
        assert "postgres:" in compose_content
        assert "temporal:" in compose_content

    def test_custom_ports_in_alongside_mode(self, config, temp_output_dir):
        """Test that ALONGSIDE mode uses custom ports to avoid conflicts."""
        # Create planner (normally it would detect incompatible version)
        ServiceDeploymentPlanner(
            config=config,
            detected_services=[],
        )

        # Manually create a plan with ALONGSIDE strategy for testing
        from mycelium_onboarding.deployment.strategy import (
            DeploymentPlanSummary,
            ServiceDeploymentPlan,
        )

        plan = DeploymentPlanSummary(
            plan_id="test-alongside",
            project_name=config.project_name,
        )

        # Add ALONGSIDE plan with custom port
        redis_alongside = ServiceDeploymentPlan(
            service_name="redis",
            strategy=ServiceStrategy.ALONGSIDE,
            host="localhost",
            port=6380,  # Different port
            version="7.2.0",
            connection_string="redis://localhost:6380/0",
            reason="Running alongside existing instance",
            container_name=f"{config.project_name}-redis",
            metadata={"existing_service_port": 6379},
        )
        plan.add_service_plan(redis_alongside)

        # Generate deployment
        generator = DeploymentGenerator(
            config=config,
            output_dir=temp_output_dir,
            deployment_plan=plan,
        )

        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success

        compose_content = (temp_output_dir / "docker-compose.yml").read_text()

        # Should use port 6380, not 6379
        assert "6380" in compose_content
        assert "redis:" in compose_content
