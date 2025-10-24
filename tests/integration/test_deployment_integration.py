"""End-to-end integration tests for deployment generation.

This module contains comprehensive integration tests that verify the complete
deployment generation workflow from configuration to validated output files.
Tests cover all deployment methods (Docker Compose, Kubernetes, systemd) and
include CLI integration, secrets management, and real-world scenarios.

Test Coverage:
    - Docker Compose deployment generation
    - Kubernetes manifest generation
    - systemd service file generation
    - CLI integration workflows
    - Secrets generation and integration
    - Multi-service deployments
    - Template validation
    - Error handling scenarios
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from mycelium_onboarding.cli import cli
from mycelium_onboarding.config.schema import DeploymentMethod, MyceliumConfig
from mycelium_onboarding.deployment.generator import DeploymentGenerator
from mycelium_onboarding.deployment.secrets import SecretsManager

# ============================================================================
# Docker Compose Integration Tests
# ============================================================================


class TestDeploymentE2EDockerCompose:
    """Test complete Docker Compose deployment generation flow."""

    def test_full_docker_compose_flow(self, tmp_path: Path) -> None:
        """Test complete flow: config → generate → validate."""
        # Create config
        config = MyceliumConfig(
            project_name="test-integration",
            services={
                "redis": {"enabled": True, "port": 6379},
                "postgres": {"enabled": True, "database": "test_db"},
            },
            deployment={"method": "docker-compose"},
        )

        # Generate deployment
        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success
        assert (tmp_path / "docker-compose.yml").exists()
        assert (tmp_path / ".env").exists()
        assert (tmp_path / "README.md").exists()

        # Validate docker-compose.yml is valid YAML
        with open(tmp_path / "docker-compose.yml") as f:
            compose_config = yaml.safe_load(f)

        assert "services" in compose_config
        assert "redis" in compose_config["services"]
        assert "postgres" in compose_config["services"]

        # Verify service configurations (uses 'latest' by default)
        assert compose_config["services"]["redis"]["image"] == "redis:latest"
        assert "6379:6379" in compose_config["services"]["redis"]["ports"]

        postgres_service = compose_config["services"]["postgres"]
        assert postgres_service["image"] == "postgres:latest"
        assert "5432:5432" in postgres_service["ports"]

    def test_docker_compose_with_secrets(self, tmp_path: Path) -> None:
        """Test Docker Compose generation with secrets integration."""
        config = MyceliumConfig(
            project_name="secrets-test",
            services={
                "redis": {"enabled": True},
                "postgres": {"enabled": True},
            },
        )

        # Generate secrets
        secrets_mgr = SecretsManager(config.project_name, secrets_dir=tmp_path / "secrets")
        secrets_obj = secrets_mgr.generate_secrets(postgres=True, redis=True)
        secrets_mgr.save_secrets(secrets_obj)

        # Generate deployment
        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success
        assert (tmp_path / "docker-compose.yml").exists()
        assert (tmp_path / ".env").exists()

        # Verify .env file contains expected structure
        env_content = (tmp_path / ".env").read_text()
        assert "POSTGRES_USER" in env_content
        assert "POSTGRES_PASSWORD" in env_content
        assert "REDIS_MAX_MEMORY" in env_content

    def test_docker_compose_single_service(self, tmp_path: Path) -> None:
        """Test Docker Compose with only one service enabled."""
        config = MyceliumConfig(
            project_name="redis-only",
            services={
                "redis": {"enabled": True},
                "postgres": {"enabled": False},
                "temporal": {"enabled": False},
            },
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success

        with open(tmp_path / "docker-compose.yml") as f:
            compose_config = yaml.safe_load(f)

        assert "redis" in compose_config["services"]
        assert "postgres" not in compose_config["services"]
        assert "temporal" not in compose_config["services"]

    def test_docker_compose_all_services(self, tmp_path: Path) -> None:
        """Test Docker Compose with all services enabled."""
        config = MyceliumConfig(
            project_name="all-services",
            services={
                "redis": {"enabled": True},
                "postgres": {"enabled": True},
                "temporal": {"enabled": True},
            },
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success

        with open(tmp_path / "docker-compose.yml") as f:
            compose_config = yaml.safe_load(f)

        assert "redis" in compose_config["services"]
        assert "postgres" in compose_config["services"]
        assert "temporal" in compose_config["services"]

    def test_docker_compose_custom_ports(self, tmp_path: Path) -> None:
        """Test Docker Compose with custom port configurations."""
        config = MyceliumConfig(
            project_name="custom-ports",
            services={
                "redis": {"enabled": True, "port": 6380},
                "postgres": {"enabled": True, "port": 5433},
            },
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success

        with open(tmp_path / "docker-compose.yml") as f:
            compose_config = yaml.safe_load(f)

        # Verify custom ports
        assert "6380:6379" in compose_config["services"]["redis"]["ports"]
        assert "5433:5432" in compose_config["services"]["postgres"]["ports"]

    def test_docker_compose_readme_generation(self, tmp_path: Path) -> None:
        """Test README.md is generated with correct instructions."""
        config = MyceliumConfig(
            project_name="readme-test",
            services={"redis": {"enabled": True}},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success
        assert (tmp_path / "README.md").exists()

        readme_content = (tmp_path / "README.md").read_text()
        assert "readme-test" in readme_content
        assert "docker-compose up -d" in readme_content
        assert "docker-compose ps" in readme_content
        assert "Redis" in readme_content

    def test_docker_compose_warnings(self, tmp_path: Path) -> None:
        """Test that warnings are generated for default credentials."""
        config = MyceliumConfig(
            project_name="warnings-test",
            services={"postgres": {"enabled": True}},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success
        assert len(result.warnings) > 0
        assert any("credentials" in w.lower() for w in result.warnings)


# ============================================================================
# Kubernetes Integration Tests
# ============================================================================


class TestDeploymentE2EKubernetes:
    """Test complete Kubernetes deployment generation flow."""

    def test_full_kubernetes_flow(self, tmp_path: Path) -> None:
        """Test complete Kubernetes generation and validation."""
        config = MyceliumConfig(
            project_name="k8s-test",
            services={"redis": {"enabled": True}},
            deployment={"method": "kubernetes"},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.KUBERNETES)

        assert result.success
        k8s_dir = tmp_path / "kubernetes"
        assert k8s_dir.exists()
        assert (k8s_dir / "00-namespace.yaml").exists()
        assert (k8s_dir / "10-redis.yaml").exists()
        assert (k8s_dir / "kustomization.yaml").exists()
        assert (k8s_dir / "README.md").exists()

    def test_kubernetes_namespace_creation(self, tmp_path: Path) -> None:
        """Test Kubernetes namespace manifest is valid."""
        config = MyceliumConfig(
            project_name="namespace-test",
            services={"redis": {"enabled": True}},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.KUBERNETES)

        assert result.success

        namespace_file = tmp_path / "kubernetes" / "00-namespace.yaml"
        with open(namespace_file) as f:
            namespace_manifest = yaml.safe_load(f)

        assert namespace_manifest["kind"] == "Namespace"
        assert namespace_manifest["metadata"]["name"] == "namespace-test"

    def test_kubernetes_redis_manifest(self, tmp_path: Path) -> None:
        """Test Redis Kubernetes manifest structure."""
        config = MyceliumConfig(
            project_name="redis-k8s",
            services={"redis": {"enabled": True, "port": 6379}},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.KUBERNETES)

        assert result.success

        redis_file = tmp_path / "kubernetes" / "10-redis.yaml"
        with open(redis_file) as f:
            # YAML file contains multiple documents
            docs = list(yaml.safe_load_all(f))

        # Should contain Deployment and Service
        kinds = [doc["kind"] for doc in docs if doc]
        assert "Deployment" in kinds
        assert "Service" in kinds

    def test_kubernetes_postgres_manifest(self, tmp_path: Path) -> None:
        """Test PostgreSQL Kubernetes manifest structure."""
        config = MyceliumConfig(
            project_name="postgres-k8s",
            services={"postgres": {"enabled": True}},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.KUBERNETES)

        assert result.success

        postgres_file = tmp_path / "kubernetes" / "20-postgres.yaml"
        with open(postgres_file) as f:
            docs = list(yaml.safe_load_all(f))

        kinds = [doc["kind"] for doc in docs if doc]
        assert "Deployment" in kinds or "StatefulSet" in kinds
        assert "Service" in kinds

    def test_kubernetes_kustomization(self, tmp_path: Path) -> None:
        """Test kustomization.yaml is valid and references all manifests."""
        config = MyceliumConfig(
            project_name="kustomize-test",
            services={
                "redis": {"enabled": True},
                "postgres": {"enabled": True},
            },
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.KUBERNETES)

        assert result.success

        kustomize_file = tmp_path / "kubernetes" / "kustomization.yaml"
        with open(kustomize_file) as f:
            kustomize_config = yaml.safe_load(f)

        assert kustomize_config["kind"] == "Kustomization"
        assert kustomize_config["namespace"] == "kustomize-test"
        assert "resources" in kustomize_config

        # Verify resources list contains expected files
        resources = kustomize_config["resources"]
        assert any("namespace" in r for r in resources)
        assert any("redis" in r for r in resources)
        assert any("postgres" in r for r in resources)

    def test_kubernetes_multi_service(self, tmp_path: Path) -> None:
        """Test Kubernetes with multiple services."""
        config = MyceliumConfig(
            project_name="multi-k8s",
            services={
                "redis": {"enabled": True},
                "postgres": {"enabled": True},
                "temporal": {"enabled": True},
            },
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.KUBERNETES)

        assert result.success

        k8s_dir = tmp_path / "kubernetes"
        assert (k8s_dir / "10-redis.yaml").exists()
        assert (k8s_dir / "20-postgres.yaml").exists()
        assert (k8s_dir / "30-temporal.yaml").exists()

    def test_kubernetes_project_name_validation(self, tmp_path: Path) -> None:
        """Test that invalid project names are rejected for Kubernetes."""
        config = MyceliumConfig(
            project_name="Invalid_Name",  # Underscores not allowed in k8s
            services={"redis": {"enabled": True}},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.KUBERNETES)

        assert not result.success
        assert len(result.errors) > 0
        assert any("alphanumeric" in e.lower() for e in result.errors)

    def test_kubernetes_readme_generation(self, tmp_path: Path) -> None:
        """Test Kubernetes README contains correct kubectl commands."""
        config = MyceliumConfig(
            project_name="readme-k8s",
            services={"redis": {"enabled": True}},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.KUBERNETES)

        assert result.success

        readme_file = tmp_path / "kubernetes" / "README.md"
        readme_content = readme_file.read_text()

        assert "kubectl apply" in readme_content
        assert "readme-k8s" in readme_content
        assert "kubectl get" in readme_content


# ============================================================================
# systemd Integration Tests
# ============================================================================


class TestDeploymentE2ESystemd:
    """Test complete systemd deployment generation flow."""

    def test_full_systemd_flow(self, tmp_path: Path) -> None:
        """Test complete systemd generation."""
        config = MyceliumConfig(
            project_name="systemd-test",
            services={"redis": {"enabled": True}},
            deployment={"method": "systemd"},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.SYSTEMD)

        assert result.success
        systemd_dir = tmp_path / "systemd"
        assert systemd_dir.exists()
        assert (systemd_dir / "install.sh").exists()
        assert (systemd_dir / "README.md").exists()

        # Check for service files
        service_files = list(systemd_dir.glob("*.service"))
        assert len(service_files) > 0

    def test_systemd_service_file_structure(self, tmp_path: Path) -> None:
        """Test systemd service file has correct structure."""
        config = MyceliumConfig(
            project_name="service-test",
            services={"redis": {"enabled": True}},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.SYSTEMD)

        assert result.success

        service_files = list((tmp_path / "systemd").glob("*redis*.service"))
        assert len(service_files) > 0

        service_content = service_files[0].read_text()
        assert "[Unit]" in service_content
        assert "[Service]" in service_content
        assert "[Install]" in service_content

    def test_systemd_install_script(self, tmp_path: Path) -> None:
        """Test systemd install script is executable and valid."""
        config = MyceliumConfig(
            project_name="install-test",
            services={"redis": {"enabled": True}},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.SYSTEMD)

        assert result.success

        install_script = tmp_path / "systemd" / "install.sh"
        assert install_script.exists()

        # Check executable bit
        assert install_script.stat().st_mode & 0o111  # Any execute bit set

        # Check script content
        script_content = install_script.read_text()
        assert "#!/bin/bash" in script_content
        assert "systemctl daemon-reload" in script_content

    def test_systemd_multi_service(self, tmp_path: Path) -> None:
        """Test systemd with multiple services."""
        config = MyceliumConfig(
            project_name="multi-systemd",
            services={
                "redis": {"enabled": True},
                "postgres": {"enabled": True},
            },
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.SYSTEMD)

        assert result.success

        systemd_dir = tmp_path / "systemd"
        service_files = list(systemd_dir.glob("*.service"))

        # Should have at least 2 service files
        assert len(service_files) >= 2

    def test_systemd_project_name_length_validation(self, tmp_path: Path) -> None:
        """Test that excessively long project names are rejected."""
        config = MyceliumConfig(
            project_name="a" * 60,  # Too long for systemd
            services={"redis": {"enabled": True}},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.SYSTEMD)

        assert not result.success
        assert len(result.errors) > 0

    def test_systemd_warnings(self, tmp_path: Path) -> None:
        """Test that systemd generation includes appropriate warnings."""
        config = MyceliumConfig(
            project_name="warnings-systemd",
            services={"redis": {"enabled": True}},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.SYSTEMD)

        assert result.success
        assert len(result.warnings) > 0
        assert any("root" in w.lower() for w in result.warnings)


# ============================================================================
# CLI Integration Tests
# ============================================================================


class TestCLIIntegration:
    """Test CLI integration end-to-end."""

    def test_cli_generate_command(self, tmp_path: Path, mocker) -> None:
        """Test full CLI generate workflow."""
        # Create a real config file
        config = MyceliumConfig(
            project_name="cli-test",
            services={"redis": {"enabled": True}},
            deployment={"method": "docker-compose"},
        )

        config_path = tmp_path / "config.yaml"
        config_path.write_text(config.to_yaml())

        # Mock ConfigManager to use our test config
        mocker.patch(
            "mycelium_onboarding.cli.ConfigManager.load", return_value=config
        )

        runner = CliRunner()
        result = runner.invoke(
            cli, ["deploy", "generate", "--output", str(tmp_path / "output")]
        )

        assert result.exit_code == 0
        assert "Deployment generated successfully" in result.output

    def test_cli_generate_with_method_override(self, tmp_path: Path, mocker) -> None:
        """Test CLI can override deployment method from config."""
        config = MyceliumConfig(
            project_name="override-test",
            services={"redis": {"enabled": True}},
            deployment={"method": "docker-compose"},
        )

        mocker.patch(
            "mycelium_onboarding.cli.ConfigManager.load", return_value=config
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "deploy",
                "generate",
                "--method",
                "kubernetes",
                "--output",
                str(tmp_path / "k8s"),
            ],
        )

        assert result.exit_code == 0
        assert (tmp_path / "k8s" / "kubernetes").exists()

    def test_cli_generate_without_config(self, tmp_path: Path, mocker) -> None:
        """Test CLI gracefully handles missing configuration."""
        mocker.patch(
            "mycelium_onboarding.cli.ConfigManager.load",
            side_effect=FileNotFoundError("Config not found"),
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["deploy", "generate"])

        assert result.exit_code == 1
        assert "Error loading config" in result.output

    def test_cli_secrets_command(self, tmp_path: Path, mocker) -> None:
        """Test CLI secrets management (simplified)."""
        config = MyceliumConfig(
            project_name="secrets-cli",
            services={"postgres": {"enabled": True}},
        )

        # Mock ConfigManager
        mocker.patch(
            "mycelium_onboarding.cli.ConfigManager.load", return_value=config
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["deploy", "secrets"])

        # Should exit successfully even with no secrets
        assert result.exit_code == 0
        # Should display appropriate message
        assert "secrets" in result.output.lower() or "No secrets found" in result.output

    def test_cli_generate_with_no_secrets(self, tmp_path: Path, mocker) -> None:
        """Test CLI generate without secrets generation."""
        config = MyceliumConfig(
            project_name="no-secrets",
            services={"redis": {"enabled": True}},
        )

        mocker.patch(
            "mycelium_onboarding.cli.ConfigManager.load", return_value=config
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "deploy",
                "generate",
                "--no-secrets",
                "--output",
                str(tmp_path / "output"),
            ],
        )

        assert result.exit_code == 0
        # Should not generate secrets
        assert "Secrets generated" not in result.output


# ============================================================================
# Secrets Integration Tests
# ============================================================================


class TestSecretsIntegration:
    """Test secrets integration with deployment."""

    def test_secrets_generated_with_deployment(self, tmp_path: Path) -> None:
        """Test secrets are generated along with deployment."""
        config = MyceliumConfig(
            project_name="secrets-deploy",
            services={
                "postgres": {"enabled": True},
                "redis": {"enabled": True},
            },
        )

        # Generate secrets
        secrets_mgr = SecretsManager(
            config.project_name, secrets_dir=tmp_path / "secrets"
        )
        secrets_obj = secrets_mgr.generate_secrets(postgres=True, redis=True)
        secrets_mgr.save_secrets(secrets_obj)

        # Generate deployment
        generator = DeploymentGenerator(config, output_dir=tmp_path / "deploy")
        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success
        assert (tmp_path / "secrets" / "secrets-deploy.json").exists()

    def test_secrets_rotation(self, tmp_path: Path) -> None:
        """Test secret rotation functionality."""
        secrets_mgr = SecretsManager("rotation-test", secrets_dir=tmp_path)

        # Generate initial secrets
        initial = secrets_mgr.generate_secrets(postgres=True)
        secrets_mgr.save_secrets(initial)
        initial_password = initial.postgres_password

        # Rotate secret
        rotated = secrets_mgr.rotate_secret("postgres")

        assert rotated.postgres_password != initial_password
        assert rotated.postgres_password is not None

    def test_secrets_env_vars(self, tmp_path: Path) -> None:
        """Test secrets can be converted to environment variables."""
        secrets_mgr = SecretsManager("env-test", secrets_dir=tmp_path)
        secrets_obj = secrets_mgr.generate_secrets(postgres=True, redis=True)

        env_vars = secrets_obj.to_env_vars()

        assert "POSTGRES_PASSWORD" in env_vars
        assert "REDIS_PASSWORD" in env_vars
        assert env_vars["POSTGRES_PASSWORD"] == secrets_obj.postgres_password
        assert env_vars["REDIS_PASSWORD"] == secrets_obj.redis_password

    def test_secrets_file_permissions(self, tmp_path: Path) -> None:
        """Test secrets files have secure permissions."""
        secrets_mgr = SecretsManager("perms-test", secrets_dir=tmp_path)
        secrets_obj = secrets_mgr.generate_secrets(postgres=True)
        secrets_mgr.save_secrets(secrets_obj)

        secrets_file = tmp_path / "perms-test.json"
        assert secrets_file.exists()

        # Check file permissions are secure (0o600)
        mode = secrets_file.stat().st_mode & 0o777
        assert mode == 0o600


# ============================================================================
# Template Validation Tests
# ============================================================================


class TestTemplateValidation:
    """Test all templates render valid output."""

    def test_docker_compose_template_valid_yaml(self, tmp_path: Path) -> None:
        """Test Docker Compose template produces valid YAML."""
        config = MyceliumConfig(
            project_name="yaml-test",
            services={
                "redis": {"enabled": True},
                "postgres": {"enabled": True},
                "temporal": {"enabled": True},
            },
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success

        # Parse YAML to ensure it's valid
        with open(tmp_path / "docker-compose.yml") as f:
            compose_config = yaml.safe_load(f)

        assert compose_config is not None
        assert "services" in compose_config

    def test_kubernetes_templates_valid_yaml(self, tmp_path: Path) -> None:
        """Test all Kubernetes templates produce valid YAML."""
        config = MyceliumConfig(
            project_name="k8s-yaml-test",
            services={
                "redis": {"enabled": True},
                "postgres": {"enabled": True},
            },
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.KUBERNETES)

        assert result.success

        k8s_dir = tmp_path / "kubernetes"
        yaml_files = list(k8s_dir.glob("*.yaml"))

        # Validate each YAML file
        for yaml_file in yaml_files:
            with open(yaml_file) as f:
                # Handle multi-document YAML
                docs = list(yaml.safe_load_all(f))
                assert len(docs) > 0
                for doc in docs:
                    if doc:  # Skip None documents
                        assert "kind" in doc or "resources" in doc

    def test_systemd_templates_valid_ini(self, tmp_path: Path) -> None:
        """Test systemd templates produce valid service files."""
        config = MyceliumConfig(
            project_name="systemd-ini-test",
            services={"redis": {"enabled": True}},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.SYSTEMD)

        assert result.success

        systemd_dir = tmp_path / "systemd"
        service_files = list(systemd_dir.glob("*.service"))

        # Validate service file structure
        for service_file in service_files:
            content = service_file.read_text()
            assert "[Unit]" in content
            assert "[Service]" in content
            assert "[Install]" in content


# ============================================================================
# Error Scenario Tests
# ============================================================================


class TestErrorScenarios:
    """Test error handling in deployment generation."""

    def test_no_services_enabled_error(self, tmp_path: Path) -> None:
        """Test error when no services are enabled."""
        with pytest.raises(ValueError, match="At least one service must be enabled"):
            MyceliumConfig(
                project_name="no-services",
                services={
                    "redis": {"enabled": False},
                    "postgres": {"enabled": False},
                    "temporal": {"enabled": False},
                },
            )

    def test_invalid_deployment_method(self, tmp_path: Path) -> None:
        """Test handling of invalid deployment method."""
        config = MyceliumConfig(
            project_name="invalid-method",
            services={"redis": {"enabled": True}},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)

        # Try to generate with invalid method (cast from string)
        with pytest.raises(ValueError):
            DeploymentMethod("invalid-method")

    def test_output_directory_creation(self, tmp_path: Path) -> None:
        """Test that output directories are created if they don't exist."""
        config = MyceliumConfig(
            project_name="create-dir",
            services={"redis": {"enabled": True}},
        )

        output_dir = tmp_path / "nested" / "output" / "dir"
        generator = DeploymentGenerator(config, output_dir=output_dir)
        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success
        assert output_dir.exists()

    def test_permission_error_handling(self, tmp_path: Path, mocker) -> None:
        """Test handling of permission errors during generation."""
        config = MyceliumConfig(
            project_name="perm-error",
            services={"redis": {"enabled": True}},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)

        # Mock file write to raise PermissionError
        mocker.patch("pathlib.Path.write_text", side_effect=PermissionError)

        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert not result.success
        assert len(result.errors) > 0


# ============================================================================
# Real-World Scenario Tests
# ============================================================================


class TestRealWorldScenarios:
    """Test real-world deployment scenarios."""

    def test_microservices_stack(self, tmp_path: Path) -> None:
        """Test typical microservices stack with all services."""
        config = MyceliumConfig(
            project_name="microservices-stack",
            services={
                "redis": {"enabled": True, "port": 6379, "max_memory": "512mb"},
                "postgres": {
                    "enabled": True,
                    "port": 5432,
                    "database": "services_db",
                    "max_connections": 200,
                },
                "temporal": {
                    "enabled": True,
                    "ui_port": 8080,
                    "frontend_port": 7233,
                    "namespace": "production",
                },
            },
            deployment={"method": "docker-compose", "auto_start": True},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success
        assert len(result.files_generated) >= 3  # compose, env, readme

    def test_development_environment(self, tmp_path: Path) -> None:
        """Test simple development environment setup."""
        config = MyceliumConfig(
            project_name="dev-env",
            services={
                "redis": {"enabled": True},
                "postgres": {"enabled": True, "database": "dev_db"},
                "temporal": {"enabled": False},
            },
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success

    def test_production_kubernetes_deployment(self, tmp_path: Path) -> None:
        """Test production-grade Kubernetes deployment."""
        config = MyceliumConfig(
            project_name="prod-k8s",
            services={
                "redis": {"enabled": True, "persistence": True},
                "postgres": {"enabled": True, "max_connections": 500},
                "temporal": {"enabled": True},
            },
            deployment={"method": "kubernetes", "healthcheck_timeout": 120},
        )

        generator = DeploymentGenerator(config, output_dir=tmp_path)
        result = generator.generate(DeploymentMethod.KUBERNETES)

        assert result.success
        k8s_dir = tmp_path / "kubernetes"

        # Verify all expected manifests exist
        assert (k8s_dir / "00-namespace.yaml").exists()
        assert (k8s_dir / "10-redis.yaml").exists()
        assert (k8s_dir / "20-postgres.yaml").exists()
        assert (k8s_dir / "30-temporal.yaml").exists()

    def test_migration_from_compose_to_kubernetes(self, tmp_path: Path) -> None:
        """Test migrating from Docker Compose to Kubernetes."""
        config = MyceliumConfig(
            project_name="migration-test",
            services={
                "redis": {"enabled": True, "port": 6379},
                "postgres": {"enabled": True},
            },
        )

        # First generate Docker Compose
        generator = DeploymentGenerator(config, output_dir=tmp_path / "compose")
        compose_result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)
        assert compose_result.success

        # Then generate Kubernetes with same config
        generator = DeploymentGenerator(config, output_dir=tmp_path / "k8s")
        k8s_result = generator.generate(DeploymentMethod.KUBERNETES)
        assert k8s_result.success

        # Both should exist and be valid
        assert (tmp_path / "compose" / "docker-compose.yml").exists()
        assert (tmp_path / "k8s" / "kubernetes").exists()
