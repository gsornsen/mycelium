"""Tests for deployment configuration generator.

This module contains comprehensive tests for the DeploymentGenerator class,
covering all deployment methods, validation logic, and error handling.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from mycelium_onboarding.config.schema import (
    DeploymentMethod,
    MyceliumConfig,
    PostgresConfig,
    RedisConfig,
    ServicesConfig,
    TemporalConfig,
)
from mycelium_onboarding.deployment.generator import (
    DeploymentGenerator,
    GenerationResult,
)


class TestDeploymentGeneratorInitialization:
    """Tests for DeploymentGenerator initialization."""

    def test_generator_initialization_default_output_dir(self) -> None:
        """Test DeploymentGenerator initialization with default output dir."""
        config = MyceliumConfig(project_name="test")
        gen = DeploymentGenerator(config)

        assert gen.config == config
        assert gen.output_dir.name == "test"
        assert "deployments" in str(gen.output_dir)
        assert gen.renderer is not None

    def test_generator_initialization_custom_output_dir(self, tmp_path: Path) -> None:
        """Test DeploymentGenerator initialization with custom output dir."""
        config = MyceliumConfig(project_name="test")
        output_dir = tmp_path / "custom"
        gen = DeploymentGenerator(config, output_dir=output_dir)

        assert gen.config == config
        assert gen.output_dir == output_dir
        assert gen.renderer is not None

    def test_generator_stores_config(self) -> None:
        """Test that generator stores config correctly."""
        config = MyceliumConfig(
            project_name="myproject",
            services=ServicesConfig(
                redis=RedisConfig(enabled=True, port=6380),
            ),
        )
        gen = DeploymentGenerator(config)

        assert gen.config.project_name == "myproject"
        assert gen.config.services.redis.port == 6380


class TestDockerComposeGeneration:
    """Tests for Docker Compose generation."""

    def test_generate_docker_compose_success(self, tmp_path: Path) -> None:
        """Test successful Docker Compose generation."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        result = gen.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success
        assert result.method == DeploymentMethod.DOCKER_COMPOSE
        assert result.output_dir == tmp_path
        assert len(result.files_generated) == 3
        assert len(result.errors) == 0

    def test_docker_compose_creates_compose_file(self, tmp_path: Path) -> None:
        """Test that docker-compose.yml is created."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        result = gen.generate(DeploymentMethod.DOCKER_COMPOSE)

        compose_file = tmp_path / "docker-compose.yml"
        assert compose_file.exists()
        assert compose_file in result.files_generated

        content = compose_file.read_text()
        assert "version:" in content or "services:" in content

    def test_docker_compose_creates_env_file(self, tmp_path: Path) -> None:
        """Test that .env file is created."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(
                postgres=PostgresConfig(enabled=True, database="testdb")
            ),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        result = gen.generate(DeploymentMethod.DOCKER_COMPOSE)

        env_file = tmp_path / ".env"
        assert env_file.exists()
        assert env_file in result.files_generated

        content = env_file.read_text()
        assert "POSTGRES_USER" in content
        assert "POSTGRES_PASSWORD" in content
        assert "POSTGRES_DB=testdb" in content

    def test_docker_compose_creates_readme(self, tmp_path: Path) -> None:
        """Test that README.md is created."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        result = gen.generate(DeploymentMethod.DOCKER_COMPOSE)

        readme_file = tmp_path / "README.md"
        assert readme_file.exists()
        assert readme_file in result.files_generated

        content = readme_file.read_text()
        assert "Docker Compose" in content
        assert "docker-compose up" in content

    def test_docker_compose_postgres_warning(self, tmp_path: Path) -> None:
        """Test that PostgreSQL credential warning is generated."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(postgres=PostgresConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        result = gen.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert len(result.warnings) > 0
        assert any("credentials" in w.lower() for w in result.warnings)

    def test_docker_compose_all_services(self, tmp_path: Path) -> None:
        """Test Docker Compose with all services enabled."""
        config = MyceliumConfig(
            project_name="fullstack",
            services=ServicesConfig(
                redis=RedisConfig(enabled=True, port=6379),
                postgres=PostgresConfig(enabled=True, port=5432),
                temporal=TemporalConfig(enabled=True, ui_port=8080),
            ),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        result = gen.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success

        # Check compose file has all services
        compose_file = tmp_path / "docker-compose.yml"
        content = compose_file.read_text()
        assert "redis" in content.lower()
        assert "postgres" in content.lower()
        assert "temporal" in content.lower()

        # Check env file
        env_file = tmp_path / ".env"
        env_content = env_file.read_text()
        assert "POSTGRES" in env_content
        assert "REDIS" in env_content
        assert "TEMPORAL" in env_content

    def test_docker_compose_directory_creation(self, tmp_path: Path) -> None:
        """Test that output directory is created if it doesn't exist."""
        output_dir = tmp_path / "nested" / "deployment"
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=output_dir)
        result = gen.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success
        assert output_dir.exists()


class TestKubernetesGeneration:
    """Tests for Kubernetes generation."""

    def test_generate_kubernetes_success(self, tmp_path: Path) -> None:
        """Test successful Kubernetes generation."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        result = gen.generate(DeploymentMethod.KUBERNETES)

        assert result.success
        assert result.method == DeploymentMethod.KUBERNETES
        assert len(result.errors) == 0

    def test_kubernetes_creates_namespace(self, tmp_path: Path) -> None:
        """Test that namespace manifest is created."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        gen.generate(DeploymentMethod.KUBERNETES)

        k8s_dir = tmp_path / "kubernetes"
        namespace_file = k8s_dir / "00-namespace.yaml"
        assert namespace_file.exists()

        content = namespace_file.read_text()
        assert "kind: Namespace" in content
        assert "test" in content

    def test_kubernetes_creates_service_manifests(self, tmp_path: Path) -> None:
        """Test that service manifests are created."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(
                redis=RedisConfig(enabled=True),
                postgres=PostgresConfig(enabled=True),
            ),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        gen.generate(DeploymentMethod.KUBERNETES)

        k8s_dir = tmp_path / "kubernetes"
        assert (k8s_dir / "10-redis.yaml").exists()
        assert (k8s_dir / "20-postgres.yaml").exists()

    def test_kubernetes_creates_kustomization(self, tmp_path: Path) -> None:
        """Test that kustomization.yaml is created."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        gen.generate(DeploymentMethod.KUBERNETES)

        k8s_dir = tmp_path / "kubernetes"
        kustomize_file = k8s_dir / "kustomization.yaml"
        assert kustomize_file.exists()

        content = kustomize_file.read_text()
        assert "apiVersion: kustomize.config.k8s.io" in content
        assert "namespace: test" in content
        assert "resources:" in content

    def test_kubernetes_creates_readme(self, tmp_path: Path) -> None:
        """Test that README.md is created."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        gen.generate(DeploymentMethod.KUBERNETES)

        k8s_dir = tmp_path / "kubernetes"
        readme_file = k8s_dir / "README.md"
        assert readme_file.exists()

        content = readme_file.read_text()
        assert "Kubernetes" in content
        assert "kubectl apply" in content

    def test_kubernetes_only_enabled_services(self, tmp_path: Path) -> None:
        """Test that only enabled services have manifests."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(
                redis=RedisConfig(enabled=True),
                postgres=PostgresConfig(enabled=False),
                temporal=TemporalConfig(enabled=False),
            ),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        gen.generate(DeploymentMethod.KUBERNETES)

        k8s_dir = tmp_path / "kubernetes"
        assert (k8s_dir / "10-redis.yaml").exists()
        assert not (k8s_dir / "20-postgres.yaml").exists()
        assert not (k8s_dir / "30-temporal.yaml").exists()

    def test_kubernetes_manifest_ordering(self, tmp_path: Path) -> None:
        """Test that manifests are numbered for proper ordering."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(
                redis=RedisConfig(enabled=True),
                postgres=PostgresConfig(enabled=True),
                temporal=TemporalConfig(enabled=True),
            ),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        gen.generate(DeploymentMethod.KUBERNETES)

        k8s_dir = tmp_path / "kubernetes"
        manifests = sorted([f.name for f in k8s_dir.glob("*.yaml")])

        # Check ordering: namespace first, then services, then kustomization
        assert manifests[0].startswith("00-")
        assert any(m.startswith("10-") for m in manifests)

    def test_kubernetes_secrets_warning(self, tmp_path: Path) -> None:
        """Test that PostgreSQL secrets warning is generated."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(postgres=PostgresConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        result = gen.generate(DeploymentMethod.KUBERNETES)

        assert len(result.warnings) > 0
        assert any("secret" in w.lower() for w in result.warnings)


class TestSystemdGeneration:
    """Tests for systemd generation."""

    def test_generate_systemd_success(self, tmp_path: Path) -> None:
        """Test successful systemd generation."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        result = gen.generate(DeploymentMethod.SYSTEMD)

        assert result.success
        assert result.method == DeploymentMethod.SYSTEMD
        assert len(result.errors) == 0

    def test_systemd_creates_service_files(self, tmp_path: Path) -> None:
        """Test that systemd service files are created."""
        config = MyceliumConfig(
            project_name="myapp",
            services=ServicesConfig(
                redis=RedisConfig(enabled=True),
                postgres=PostgresConfig(enabled=True),
            ),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        gen.generate(DeploymentMethod.SYSTEMD)

        systemd_dir = tmp_path / "systemd"
        assert (systemd_dir / "myapp-redis.service").exists()
        assert (systemd_dir / "myapp-postgres.service").exists()

        redis_content = (systemd_dir / "myapp-redis.service").read_text()
        assert "[Unit]" in redis_content
        assert "[Service]" in redis_content

    def test_systemd_creates_install_script(self, tmp_path: Path) -> None:
        """Test that installation script is created."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        gen.generate(DeploymentMethod.SYSTEMD)

        systemd_dir = tmp_path / "systemd"
        install_script = systemd_dir / "install.sh"
        assert install_script.exists()

        content = install_script.read_text()
        assert "#!/bin/bash" in content
        assert "systemctl daemon-reload" in content
        assert "cp" in content

    def test_systemd_install_script_executable(self, tmp_path: Path) -> None:
        """Test that install script is executable."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        gen.generate(DeploymentMethod.SYSTEMD)

        systemd_dir = tmp_path / "systemd"
        install_script = systemd_dir / "install.sh"

        # Check that file is executable
        import stat

        mode = install_script.stat().st_mode
        assert mode & stat.S_IXUSR

    def test_systemd_creates_readme(self, tmp_path: Path) -> None:
        """Test that README.md is created."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        gen.generate(DeploymentMethod.SYSTEMD)

        systemd_dir = tmp_path / "systemd"
        readme_file = systemd_dir / "README.md"
        assert readme_file.exists()

        content = readme_file.read_text()
        assert "systemd" in content
        assert "systemctl" in content

    def test_systemd_only_enabled_services(self, tmp_path: Path) -> None:
        """Test that only enabled services have files."""
        config = MyceliumConfig(
            project_name="myapp",
            services=ServicesConfig(
                redis=RedisConfig(enabled=True),
                postgres=PostgresConfig(enabled=False),
            ),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        gen.generate(DeploymentMethod.SYSTEMD)

        systemd_dir = tmp_path / "systemd"
        assert (systemd_dir / "myapp-redis.service").exists()
        assert not (systemd_dir / "myapp-postgres.service").exists()

    def test_systemd_warnings(self, tmp_path: Path) -> None:
        """Test that systemd warnings are generated."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        result = gen.generate(DeploymentMethod.SYSTEMD)

        assert len(result.warnings) > 0
        assert any("root" in w.lower() for w in result.warnings)


class TestValidation:
    """Tests for configuration validation."""

    def test_validation_no_services_caught_by_schema(self) -> None:
        """Test that no services enabled is caught by schema validation."""
        with pytest.raises(ValidationError) as exc_info:
            MyceliumConfig(
                project_name="test",
                services=ServicesConfig(
                    redis=RedisConfig(enabled=False),
                    postgres=PostgresConfig(enabled=False),
                    temporal=TemporalConfig(enabled=False),
                ),
            )

        # Verify the error message mentions services
        assert "service" in str(exc_info.value).lower()

    def test_validation_kubernetes_naming(self, tmp_path: Path) -> None:
        """Test Kubernetes naming validation."""
        config = MyceliumConfig(
            project_name="test_invalid_name",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        result = gen.generate(DeploymentMethod.KUBERNETES)

        assert not result.success
        assert len(result.errors) > 0
        assert any("alphanumeric" in e.lower() for e in result.errors)

    def test_validation_kubernetes_valid_name(self, tmp_path: Path) -> None:
        """Test Kubernetes accepts valid names."""
        config = MyceliumConfig(
            project_name="my-valid-app",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        result = gen.generate(DeploymentMethod.KUBERNETES)

        assert result.success

    def test_validation_systemd_long_name(self, tmp_path: Path) -> None:
        """Test systemd validation for long names."""
        long_name = "x" * 60
        config = MyceliumConfig(
            project_name=long_name,
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        result = gen.generate(DeploymentMethod.SYSTEMD)

        assert not result.success
        assert len(result.errors) > 0
        assert any("50 characters" in e for e in result.errors)

    def test_validation_passes_with_services(self, tmp_path: Path) -> None:
        """Test validation passes with at least one service."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        errors = gen._validate_config(DeploymentMethod.DOCKER_COMPOSE)

        assert len(errors) == 0


class TestUnsupportedMethod:
    """Tests for unsupported deployment methods."""

    def test_unsupported_method(self, tmp_path: Path) -> None:
        """Test handling of unsupported deployment method."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        result = gen.generate(DeploymentMethod.MANUAL)

        assert not result.success
        assert len(result.errors) > 0
        assert any("unsupported" in e.lower() for e in result.errors)


class TestGenerationResult:
    """Tests for GenerationResult dataclass."""

    def test_generation_result_success(self) -> None:
        """Test successful GenerationResult."""
        result = GenerationResult(
            success=True,
            method=DeploymentMethod.DOCKER_COMPOSE,
            output_dir=Path("/tmp/test"),
            files_generated=[Path("/tmp/test/file.yml")],
        )

        assert result.success
        assert result.method == DeploymentMethod.DOCKER_COMPOSE
        assert len(result.files_generated) == 1
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_generation_result_failure(self) -> None:
        """Test failed GenerationResult."""
        result = GenerationResult(
            success=False,
            method=DeploymentMethod.KUBERNETES,
            output_dir=Path("/tmp/test"),
            files_generated=[],
            errors=["Error 1", "Error 2"],
        )

        assert not result.success
        assert len(result.errors) == 2
        assert len(result.files_generated) == 0

    def test_generation_result_with_warnings(self) -> None:
        """Test GenerationResult with warnings."""
        result = GenerationResult(
            success=True,
            method=DeploymentMethod.SYSTEMD,
            output_dir=Path("/tmp/test"),
            files_generated=[Path("/tmp/test/service.service")],
            warnings=["Warning 1"],
        )

        assert result.success
        assert len(result.warnings) == 1
        assert len(result.errors) == 0


class TestHelperMethods:
    """Tests for private helper methods."""

    def test_generate_env_file_postgres(self, tmp_path: Path) -> None:
        """Test _generate_env_file with PostgreSQL."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(
                postgres=PostgresConfig(enabled=True, database="mydb")
            ),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        env_content = gen._generate_env_file()

        assert "POSTGRES_USER" in env_content
        assert "POSTGRES_PASSWORD" in env_content
        assert "POSTGRES_DB=mydb" in env_content
        assert "WARNING" in env_content

    def test_generate_env_file_redis(self, tmp_path: Path) -> None:
        """Test _generate_env_file with Redis."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(
                redis=RedisConfig(enabled=True, max_memory="512mb")
            ),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        env_content = gen._generate_env_file()

        assert "REDIS_MAX_MEMORY=512mb" in env_content

    def test_generate_env_file_temporal(self, tmp_path: Path) -> None:
        """Test _generate_env_file with Temporal."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(
                temporal=TemporalConfig(enabled=True, namespace="production")
            ),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        env_content = gen._generate_env_file()

        assert "TEMPORAL_NAMESPACE=production" in env_content

    def test_generate_kustomization_content(self, tmp_path: Path) -> None:
        """Test _generate_kustomization content."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)

        manifest_files = [
            tmp_path / "00-namespace.yaml",
            tmp_path / "10-redis.yaml",
        ]
        kustomize_content = gen._generate_kustomization(manifest_files)

        assert "apiVersion: kustomize.config.k8s.io" in kustomize_content
        assert "namespace: test" in kustomize_content
        assert "00-namespace.yaml" in kustomize_content
        assert "10-redis.yaml" in kustomize_content

    def test_generate_systemd_install_script_content(self, tmp_path: Path) -> None:
        """Test _generate_systemd_install_script content."""
        config = MyceliumConfig(
            project_name="myapp",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)

        service_files = ["myapp-redis.service", "myapp-postgres.service"]
        script_content = gen._generate_systemd_install_script(service_files)

        assert "#!/bin/bash" in script_content
        assert "myapp-redis.service" in script_content
        assert "myapp-postgres.service" in script_content
        assert "systemctl daemon-reload" in script_content
        assert "EUID" in script_content  # Root check


class TestReadmeGeneration:
    """Tests for README generation."""

    def test_readme_docker_compose_content(self, tmp_path: Path) -> None:
        """Test Docker Compose README content."""
        config = MyceliumConfig(
            project_name="myproject",
            services=ServicesConfig(
                redis=RedisConfig(enabled=True, port=6379),
                postgres=PostgresConfig(enabled=True, port=5432),
            ),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        readme = gen._generate_readme("docker-compose")

        assert "myproject" in readme
        assert "Docker Compose" in readme
        assert "docker-compose up" in readme
        assert "Redis (port 6379)" in readme
        assert "PostgreSQL (port 5432)" in readme

    def test_readme_kubernetes_content(self, tmp_path: Path) -> None:
        """Test Kubernetes README content."""
        config = MyceliumConfig(
            project_name="myproject",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        readme = gen._generate_readme("kubernetes")

        assert "myproject" in readme
        assert "Kubernetes" in readme
        assert "kubectl apply" in readme
        assert "kubectl get" in readme

    def test_readme_systemd_content(self, tmp_path: Path) -> None:
        """Test systemd README content."""
        config = MyceliumConfig(
            project_name="myproject",
            services=ServicesConfig(
                redis=RedisConfig(enabled=True),
                temporal=TemporalConfig(enabled=True),
            ),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        readme = gen._generate_readme("systemd")

        assert "myproject" in readme
        assert "systemd" in readme
        assert "systemctl" in readme
        assert "sudo ./install.sh" in readme

    def test_readme_includes_enabled_services_only(self, tmp_path: Path) -> None:
        """Test README only includes enabled services."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(
                redis=RedisConfig(enabled=True),
                postgres=PostgresConfig(enabled=False),
            ),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)
        readme = gen._generate_readme("docker-compose")

        assert "Redis" in readme
        assert "PostgreSQL" not in readme


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_project_name_handled_by_schema(self) -> None:
        """Test that empty project name is caught by schema validation."""
        with pytest.raises(ValidationError):
            MyceliumConfig(project_name="")

    def test_output_dir_already_exists(self, tmp_path: Path) -> None:
        """Test generation when output directory already exists."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )

        # Create directory first
        output_dir = tmp_path / "deployment"
        output_dir.mkdir()

        gen = DeploymentGenerator(config, output_dir=output_dir)
        result = gen.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result.success

    def test_multiple_generations_same_directory(self, tmp_path: Path) -> None:
        """Test multiple generations to same directory (overwrite)."""
        config = MyceliumConfig(
            project_name="test",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )
        gen = DeploymentGenerator(config, output_dir=tmp_path)

        # Generate twice
        result1 = gen.generate(DeploymentMethod.DOCKER_COMPOSE)
        result2 = gen.generate(DeploymentMethod.DOCKER_COMPOSE)

        assert result1.success
        assert result2.success

    def test_all_deployment_methods(self, tmp_path: Path) -> None:
        """Test generating all deployment methods for same config."""
        config = MyceliumConfig(
            project_name="test-app",
            services=ServicesConfig(redis=RedisConfig(enabled=True)),
        )

        # Docker Compose
        gen_docker = DeploymentGenerator(config, output_dir=tmp_path / "docker")
        result_docker = gen_docker.generate(DeploymentMethod.DOCKER_COMPOSE)
        assert result_docker.success

        # Kubernetes
        gen_k8s = DeploymentGenerator(config, output_dir=tmp_path / "k8s")
        result_k8s = gen_k8s.generate(DeploymentMethod.KUBERNETES)
        assert result_k8s.success

        # systemd
        gen_systemd = DeploymentGenerator(config, output_dir=tmp_path / "systemd")
        result_systemd = gen_systemd.generate(DeploymentMethod.SYSTEMD)
        assert result_systemd.success
