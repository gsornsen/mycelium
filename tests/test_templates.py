"""Tests for deployment template rendering.

This module contains comprehensive tests for all deployment templates:
- Docker Compose templates
- Kubernetes manifests
- systemd service files
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from mycelium_onboarding.config.schema import (
    DeploymentMethod,
    MyceliumConfig,
)
from mycelium_onboarding.deployment import TemplateRenderer


class TestTemplateRenderer:
    """Test TemplateRenderer initialization and basic functionality."""

    def test_renderer_initialization(self):
        """Test TemplateRenderer initializes with default template directory."""
        renderer = TemplateRenderer()
        assert renderer.template_dir.exists()
        assert renderer.template_dir.name == "templates"
        assert renderer.env is not None

    def test_renderer_custom_template_dir(self, tmp_path):
        """Test TemplateRenderer with custom template directory."""
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()

        renderer = TemplateRenderer(template_dir=custom_dir)
        assert renderer.template_dir == custom_dir

    def test_renderer_invalid_template_dir(self):
        """Test TemplateRenderer raises error for invalid directory."""
        with pytest.raises(FileNotFoundError):
            TemplateRenderer(template_dir=Path("/nonexistent/path"))

    def test_kebab_case_filter(self):
        """Test kebab-case filter conversion."""
        renderer = TemplateRenderer()
        assert renderer._kebab_case_filter("my_project") == "my-project"
        assert renderer._kebab_case_filter("Test_Name") == "test-name"


class TestDockerComposeTemplates:
    """Test Docker Compose template rendering."""

    @pytest.fixture
    def minimal_config(self):
        """Minimal configuration with only Redis enabled."""
        return MyceliumConfig(
            project_name="test-project",
            services={
                "redis": {"enabled": True},
                "postgres": {"enabled": False},
                "temporal": {"enabled": False},
            },
        )

    @pytest.fixture
    def full_config(self):
        """Full configuration with all services enabled."""
        return MyceliumConfig(
            project_name="full-project",
            services={
                "redis": {
                    "enabled": True,
                    "version": "7.0",
                    "port": 6380,
                    "persistence": True,
                    "max_memory": "512mb",
                },
                "postgres": {
                    "enabled": True,
                    "version": "15",
                    "port": 5433,
                    "database": "testdb",
                    "max_connections": 200,
                },
                "temporal": {
                    "enabled": True,
                    "version": "1.22.0",
                    "ui_port": 8081,
                    "frontend_port": 7234,
                    "namespace": "test-namespace",
                },
            },
            deployment={
                "method": "docker-compose",
                "auto_start": True,
            },
        )

    def test_docker_compose_renders_valid_yaml(self, minimal_config):
        """Test Docker Compose template renders valid YAML."""
        renderer = TemplateRenderer()
        output = renderer.render_docker_compose(minimal_config)

        # Should parse as valid YAML
        parsed = yaml.safe_load(output)
        assert isinstance(parsed, dict)
        assert "services" in parsed
        assert "version" in parsed

    def test_docker_compose_minimal_redis_only(self, minimal_config):
        """Test Docker Compose with only Redis enabled."""
        renderer = TemplateRenderer()
        output = renderer.render_docker_compose(minimal_config)
        parsed = yaml.safe_load(output)

        # Should have Redis service
        assert "redis" in parsed["services"]
        assert "postgres" not in parsed["services"]
        assert "temporal" not in parsed["services"]

        # Verify Redis configuration
        redis = parsed["services"]["redis"]
        assert redis["container_name"] == "test-project-redis"
        assert "6379:6379" in redis["ports"]

    def test_docker_compose_full_services(self, full_config):
        """Test Docker Compose with all services enabled."""
        renderer = TemplateRenderer()
        output = renderer.render_docker_compose(full_config)
        parsed = yaml.safe_load(output)

        # All services should be present
        assert "redis" in parsed["services"]
        assert "postgres" in parsed["services"]
        assert "temporal" in parsed["services"]

    def test_docker_compose_redis_version(self, full_config):
        """Test Redis version is correctly set."""
        renderer = TemplateRenderer()
        output = renderer.render_docker_compose(full_config)
        parsed = yaml.safe_load(output)

        assert "redis:7.0" in parsed["services"]["redis"]["image"]

    def test_docker_compose_redis_custom_port(self, full_config):
        """Test Redis custom port configuration."""
        renderer = TemplateRenderer()
        output = renderer.render_docker_compose(full_config)
        parsed = yaml.safe_load(output)

        assert "6380:6379" in parsed["services"]["redis"]["ports"]

    def test_docker_compose_redis_persistence(self, full_config):
        """Test Redis persistence volume is configured."""
        renderer = TemplateRenderer()
        output = renderer.render_docker_compose(full_config)
        parsed = yaml.safe_load(output)

        # Should have volume mount
        assert "volumes" in parsed["services"]["redis"]
        assert "redis-data:/data" in parsed["services"]["redis"]["volumes"]

        # Should have named volume
        assert "volumes" in parsed
        assert "redis-data" in parsed["volumes"]

    def test_docker_compose_redis_max_memory(self, full_config):
        """Test Redis max memory configuration."""
        renderer = TemplateRenderer()
        output = renderer.render_docker_compose(full_config)
        parsed = yaml.safe_load(output)

        # Should have command with maxmemory
        assert "command" in parsed["services"]["redis"]
        assert "512mb" in str(parsed["services"]["redis"]["command"])

    def test_docker_compose_postgres_environment(self, full_config):
        """Test PostgreSQL environment variables."""
        renderer = TemplateRenderer()
        output = renderer.render_docker_compose(full_config)
        parsed = yaml.safe_load(output)

        env = parsed["services"]["postgres"]["environment"]
        assert env["POSTGRES_DB"] == "testdb"
        assert "POSTGRES_USER" in env
        assert "POSTGRES_PASSWORD" in env

    def test_docker_compose_postgres_port(self, full_config):
        """Test PostgreSQL custom port."""
        renderer = TemplateRenderer()
        output = renderer.render_docker_compose(full_config)
        parsed = yaml.safe_load(output)

        assert "5433:5432" in parsed["services"]["postgres"]["ports"]

    def test_docker_compose_temporal_depends_on_postgres(self, full_config):
        """Test Temporal depends on PostgreSQL when enabled."""
        renderer = TemplateRenderer()
        output = renderer.render_docker_compose(full_config)
        parsed = yaml.safe_load(output)

        assert "depends_on" in parsed["services"]["temporal"]
        depends_on = parsed["services"]["temporal"]["depends_on"]
        assert "postgres" in depends_on

    def test_docker_compose_temporal_namespace(self, full_config):
        """Test Temporal namespace configuration."""
        renderer = TemplateRenderer()
        output = renderer.render_docker_compose(full_config)
        parsed = yaml.safe_load(output)

        env = parsed["services"]["temporal"]["environment"]
        assert "DEFAULT_NAMESPACE=test-namespace" in env

    def test_docker_compose_healthchecks_present(self, full_config):
        """Test all services have healthchecks."""
        renderer = TemplateRenderer()
        output = renderer.render_docker_compose(full_config)
        parsed = yaml.safe_load(output)

        assert "healthcheck" in parsed["services"]["redis"]
        assert "healthcheck" in parsed["services"]["postgres"]
        assert "healthcheck" in parsed["services"]["temporal"]

    def test_docker_compose_network_configuration(self, full_config):
        """Test network is properly configured."""
        renderer = TemplateRenderer()
        output = renderer.render_docker_compose(full_config)
        parsed = yaml.safe_load(output)

        # All services should use mycelium-network
        for service in ["redis", "postgres", "temporal"]:
            assert "mycelium-network" in parsed["services"][service]["networks"]

        # Network should be defined
        assert "networks" in parsed
        assert "mycelium-network" in parsed["networks"]

    def test_docker_compose_auto_start_restart_policy(self, full_config):
        """Test restart policy with auto_start enabled."""
        renderer = TemplateRenderer()
        output = renderer.render_docker_compose(full_config)
        parsed = yaml.safe_load(output)

        # With auto_start=True, restart should be "always"
        assert parsed["services"]["redis"]["restart"] == "always"

    def test_docker_compose_no_auto_start_restart_policy(self):
        """Test restart policy with auto_start disabled."""
        config = MyceliumConfig(
            project_name="test",
            services={"redis": {"enabled": True}},
            deployment={"auto_start": False},
        )

        renderer = TemplateRenderer()
        output = renderer.render_docker_compose(config)
        parsed = yaml.safe_load(output)

        # With auto_start=False, restart should be "on-failure"
        assert parsed["services"]["redis"]["restart"] == "on-failure"


class TestKubernetesTemplates:
    """Test Kubernetes manifest rendering."""

    @pytest.fixture
    def k8s_config(self):
        """Configuration for Kubernetes testing."""
        return MyceliumConfig(
            project_name="k8s-test",
            services={
                "redis": {
                    "enabled": True,
                    "version": "7.0",
                    "persistence": True,
                },
                "postgres": {
                    "enabled": True,
                    "version": "15",
                },
                "temporal": {
                    "enabled": True,
                },
            },
        )

    def test_kubernetes_renders_all_manifests(self, k8s_config):
        """Test Kubernetes rendering creates all expected manifests."""
        renderer = TemplateRenderer()
        manifests = renderer.render_kubernetes(k8s_config)

        assert isinstance(manifests, dict)
        assert "namespace.yaml" in manifests
        assert "redis.yaml" in manifests
        assert "postgres.yaml" in manifests
        assert "temporal.yaml" in manifests

    def test_kubernetes_namespace_valid_yaml(self, k8s_config):
        """Test namespace manifest is valid YAML."""
        renderer = TemplateRenderer()
        manifests = renderer.render_kubernetes(k8s_config)

        parsed = yaml.safe_load(manifests["namespace.yaml"])
        assert parsed["kind"] == "Namespace"
        assert parsed["metadata"]["name"] == "k8s-test"

    def test_kubernetes_redis_deployment(self, k8s_config):
        """Test Redis deployment manifest."""
        renderer = TemplateRenderer()
        manifests = renderer.render_kubernetes(k8s_config)

        # Parse all documents in the Redis manifest
        docs = list(yaml.safe_load_all(manifests["redis.yaml"]))

        # Should have Deployment, Service, and PVC
        kinds = [doc["kind"] for doc in docs if doc is not None]
        assert "Deployment" in kinds
        assert "Service" in kinds
        assert "PersistentVolumeClaim" in kinds

    def test_kubernetes_redis_labels(self, k8s_config):
        """Test Redis resources have proper labels."""
        renderer = TemplateRenderer()
        manifests = renderer.render_kubernetes(k8s_config)

        docs = list(yaml.safe_load_all(manifests["redis.yaml"]))
        deployment = next(doc for doc in docs if doc and doc["kind"] == "Deployment")

        labels = deployment["metadata"]["labels"]
        assert labels["app"] == "redis"
        assert labels["project"] == "k8s-test"

    def test_kubernetes_postgres_statefulset(self, k8s_config):
        """Test PostgreSQL uses StatefulSet."""
        renderer = TemplateRenderer()
        manifests = renderer.render_kubernetes(k8s_config)

        docs = list(yaml.safe_load_all(manifests["postgres.yaml"]))
        kinds = [doc["kind"] for doc in docs if doc is not None]

        assert "StatefulSet" in kinds
        assert "Secret" in kinds
        assert "ConfigMap" in kinds

    def test_kubernetes_postgres_secret(self, k8s_config):
        """Test PostgreSQL secret is created."""
        renderer = TemplateRenderer()
        manifests = renderer.render_kubernetes(k8s_config)

        docs = list(yaml.safe_load_all(manifests["postgres.yaml"]))
        secret = next(doc for doc in docs if doc and doc["kind"] == "Secret")

        assert secret["metadata"]["name"] == "postgres-secret"
        assert "POSTGRES_USER" in secret["stringData"]
        assert "POSTGRES_PASSWORD" in secret["stringData"]

    def test_kubernetes_temporal_deployment(self, k8s_config):
        """Test Temporal deployment manifest."""
        renderer = TemplateRenderer()
        manifests = renderer.render_kubernetes(k8s_config)

        docs = list(yaml.safe_load_all(manifests["temporal.yaml"]))
        kinds = [doc["kind"] for doc in docs if doc is not None]

        assert "Deployment" in kinds
        assert "ConfigMap" in kinds
        # Should have 2 services: frontend and UI
        services = [doc for doc in docs if doc and doc["kind"] == "Service"]
        assert len(services) == 2

    def test_kubernetes_temporal_depends_on_postgres(self, k8s_config):
        """Test Temporal has init container waiting for PostgreSQL."""
        renderer = TemplateRenderer()
        manifests = renderer.render_kubernetes(k8s_config)

        docs = list(yaml.safe_load_all(manifests["temporal.yaml"]))
        deployment = next(doc for doc in docs if doc and doc["kind"] == "Deployment")

        # Should have init container
        spec = deployment["spec"]["template"]["spec"]
        assert "initContainers" in spec

    def test_kubernetes_only_enabled_services(self):
        """Test only enabled services are rendered."""
        config = MyceliumConfig(
            project_name="partial",
            services={
                "redis": {"enabled": True},
                "postgres": {"enabled": False},
                "temporal": {"enabled": False},
            },
        )

        renderer = TemplateRenderer()
        manifests = renderer.render_kubernetes(config)

        assert "namespace.yaml" in manifests
        assert "redis.yaml" in manifests
        assert "postgres.yaml" not in manifests
        assert "temporal.yaml" not in manifests


class TestSystemdTemplates:
    """Test systemd service file rendering."""

    @pytest.fixture
    def systemd_config(self):
        """Configuration for systemd testing."""
        return MyceliumConfig(
            project_name="systemd-test",
            services={
                "redis": {
                    "enabled": True,
                    "port": 6380,
                    "persistence": True,
                },
                "postgres": {
                    "enabled": True,
                    "database": "mydb",
                    "port": 5433,
                },
                "temporal": {
                    "enabled": True,
                    "namespace": "prod",
                },
            },
            deployment={
                "auto_start": True,
            },
        )

    def test_systemd_renders_all_services(self, systemd_config):
        """Test systemd rendering creates all expected service files."""
        renderer = TemplateRenderer()
        services = renderer.render_systemd(systemd_config)

        assert isinstance(services, dict)
        assert "systemd-test-redis.service" in services
        assert "systemd-test-postgres.service" in services
        assert "systemd-test-temporal.service" in services

    def test_systemd_redis_service_structure(self, systemd_config):
        """Test Redis service file has proper structure."""
        renderer = TemplateRenderer()
        services = renderer.render_systemd(systemd_config)

        service = services["systemd-test-redis.service"]

        # Should have required sections
        assert "[Unit]" in service
        assert "[Service]" in service
        assert "[Install]" in service

    def test_systemd_redis_port_configuration(self, systemd_config):
        """Test Redis service uses correct port."""
        renderer = TemplateRenderer()
        services = renderer.render_systemd(systemd_config)

        service = services["systemd-test-redis.service"]
        assert "--port 6380" in service

    def test_systemd_redis_persistence_enabled(self, systemd_config):
        """Test Redis service has persistence when enabled."""
        renderer = TemplateRenderer()
        services = renderer.render_systemd(systemd_config)

        service = services["systemd-test-redis.service"]
        assert "--dir /var/lib/systemd-test/redis" in service
        assert "--save" in service

    def test_systemd_redis_no_persistence(self):
        """Test Redis service without persistence."""
        config = MyceliumConfig(
            project_name="test",
            services={"redis": {"enabled": True, "persistence": False}},
        )

        renderer = TemplateRenderer()
        services = renderer.render_systemd(config)

        service = services["test-redis.service"]
        assert '--save ""' in service

    def test_systemd_postgres_database_name(self, systemd_config):
        """Test PostgreSQL service uses correct database name."""
        renderer = TemplateRenderer()
        services = renderer.render_systemd(systemd_config)

        service = services["systemd-test-postgres.service"]
        assert "POSTGRES_DB=mydb" in service

    def test_systemd_temporal_namespace(self, systemd_config):
        """Test Temporal service uses correct namespace."""
        renderer = TemplateRenderer()
        services = renderer.render_systemd(systemd_config)

        service = services["systemd-test-temporal.service"]
        assert "DEFAULT_NAMESPACE=prod" in service

    def test_systemd_temporal_depends_on_postgres(self, systemd_config):
        """Test Temporal service depends on PostgreSQL."""
        renderer = TemplateRenderer()
        services = renderer.render_systemd(systemd_config)

        service = services["systemd-test-temporal.service"]
        assert "After=" in service
        assert "systemd-test-postgres.service" in service
        assert "Requires=systemd-test-postgres.service" in service

    def test_systemd_restart_policy_always(self, systemd_config):
        """Test restart policy with auto_start enabled."""
        renderer = TemplateRenderer()
        services = renderer.render_systemd(systemd_config)

        service = services["systemd-test-redis.service"]
        assert "Restart=always" in service

    def test_systemd_restart_policy_on_failure(self):
        """Test restart policy with auto_start disabled."""
        config = MyceliumConfig(
            project_name="test",
            services={"redis": {"enabled": True}},
            deployment={"auto_start": False},
        )

        renderer = TemplateRenderer()
        services = renderer.render_systemd(config)

        service = services["test-redis.service"]
        assert "Restart=on-failure" in service

    def test_systemd_security_hardening(self, systemd_config):
        """Test systemd services have security hardening options."""
        renderer = TemplateRenderer()
        services = renderer.render_systemd(systemd_config)

        # Check Redis service
        service = services["systemd-test-redis.service"]
        assert "NoNewPrivileges=true" in service
        assert "PrivateTmp=true" in service
        assert "ProtectSystem=strict" in service


class TestRendererMethods:
    """Test TemplateRenderer utility methods."""

    @pytest.fixture
    def test_config(self):
        """Basic test configuration."""
        return MyceliumConfig(
            project_name="test",
            services={"redis": {"enabled": True}},
        )

    def test_render_all_returns_all_formats(self, test_config):
        """Test render_all returns all deployment formats."""
        renderer = TemplateRenderer()
        result = renderer.render_all(test_config)

        assert "docker_compose" in result
        assert "kubernetes" in result
        assert "systemd" in result

        assert isinstance(result["docker_compose"], str)
        assert isinstance(result["kubernetes"], dict)
        assert isinstance(result["systemd"], dict)

    def test_render_for_method_docker_compose(self, test_config):
        """Test render_for_method with Docker Compose."""
        renderer = TemplateRenderer()
        result = renderer.render_for_method(
            test_config, DeploymentMethod.DOCKER_COMPOSE
        )

        assert isinstance(result, str)
        assert "version:" in result

    def test_render_for_method_kubernetes(self, test_config):
        """Test render_for_method with Kubernetes."""
        renderer = TemplateRenderer()
        result = renderer.render_for_method(test_config, DeploymentMethod.KUBERNETES)

        assert isinstance(result, dict)
        assert "namespace.yaml" in result

    def test_render_for_method_systemd(self, test_config):
        """Test render_for_method with systemd."""
        renderer = TemplateRenderer()
        result = renderer.render_for_method(test_config, DeploymentMethod.SYSTEMD)

        assert isinstance(result, dict)
        assert any("redis.service" in key for key in result)

    def test_render_for_method_manual(self, test_config):
        """Test render_for_method with manual deployment."""
        renderer = TemplateRenderer()
        result = renderer.render_for_method(test_config, DeploymentMethod.MANUAL)

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_render_for_method_uses_config_method(self):
        """Test render_for_method uses config's deployment method by default."""
        config = MyceliumConfig(
            project_name="test",
            services={"redis": {"enabled": True}},
            deployment={"method": "kubernetes"},
        )

        renderer = TemplateRenderer()
        result = renderer.render_for_method(config)

        # Should return kubernetes manifests
        assert isinstance(result, dict)
        assert "namespace.yaml" in result
