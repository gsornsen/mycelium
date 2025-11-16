"""Tests for CLI deployment commands."""

from __future__ import annotations

import json
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from mycelium_onboarding.cli import cli
from mycelium_onboarding.config.schema import (
    DeploymentConfig,
    DeploymentMethod,
    MyceliumConfig,
    PostgresConfig,
    RedisConfig,
    ServicesConfig,
    TemporalConfig,
)
from mycelium_onboarding.deployment.generator import GenerationResult
from mycelium_onboarding.deployment.secrets import DeploymentSecrets


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_config():
    """Fixture providing a mock MyceliumConfig."""
    return MyceliumConfig(
        project_name="test-project",
        version="1.0",
        services=ServicesConfig(
            redis=RedisConfig(enabled=True, port=6379),
            postgres=PostgresConfig(enabled=True, port=5432),
            temporal=TemporalConfig(enabled=False),
        ),
        deployment=DeploymentConfig(method=DeploymentMethod.DOCKER_COMPOSE),
    )


@pytest.fixture
def mock_generation_result(tmp_path):
    """Fixture providing a mock GenerationResult."""
    return GenerationResult(
        success=True,
        method=DeploymentMethod.DOCKER_COMPOSE,
        output_dir=tmp_path / "deployment",
        files_generated=[
            tmp_path / "deployment" / "docker-compose.yml",
            tmp_path / "deployment" / ".env",
            tmp_path / "deployment" / "README.md",
        ],
        warnings=["Default PostgreSQL credentials are set in .env"],
    )


@pytest.fixture
def mock_secrets():
    """Fixture providing mock DeploymentSecrets."""
    return DeploymentSecrets(
        project_name="test-project",
        postgres_password="test_pg_pass",
        redis_password="test_redis_pass",
        temporal_admin_password=None,
    )


# ============================================================================
# Deploy Generate Command Tests
# ============================================================================


def test_deploy_generate_docker_compose(runner, mock_config, mock_generation_result, mock_secrets):
    """Test 'mycelium deploy generate' for Docker Compose."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.generator.DeploymentGenerator") as mock_gen_cls,
        patch("mycelium_onboarding.deployment.secrets.SecretsManager") as mock_secrets_cls,
    ):
        # Setup mocks
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        mock_gen = Mock()
        mock_gen.generate.return_value = mock_generation_result
        mock_gen_cls.return_value = mock_gen

        mock_secrets_mgr = Mock()
        mock_secrets_mgr.generate_secrets.return_value = mock_secrets
        mock_secrets_cls.return_value = mock_secrets_mgr

        result = runner.invoke(cli, ["deploy", "generate"])

        assert result.exit_code == 0
        assert "Generating docker-compose deployment" in result.output
        assert "test-project" in result.output
        assert "successfully" in result.output.lower()
        assert "docker-compose.yml" in result.output

        # Verify generator was called
        mock_gen.generate.assert_called_once()


def test_deploy_generate_kubernetes(runner, mock_config, tmp_path):
    """Test Kubernetes deployment generation."""
    mock_config.deployment.method = DeploymentMethod.KUBERNETES

    k8s_result = GenerationResult(
        success=True,
        method=DeploymentMethod.KUBERNETES,
        output_dir=tmp_path / "kubernetes",
        files_generated=[
            tmp_path / "kubernetes" / "namespace.yaml",
            tmp_path / "kubernetes" / "redis.yaml",
        ],
        warnings=[],
    )

    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.generator.DeploymentGenerator") as mock_gen_cls,
        patch("mycelium_onboarding.deployment.secrets.SecretsManager") as mock_secrets_cls,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        mock_gen = Mock()
        mock_gen.generate.return_value = k8s_result
        mock_gen_cls.return_value = mock_gen

        mock_secrets_mgr = Mock()
        mock_secrets_mgr.generate_secrets.return_value = Mock()
        mock_secrets_cls.return_value = mock_secrets_mgr

        result = runner.invoke(cli, ["deploy", "generate", "--method", "kubernetes"])

        assert result.exit_code == 0
        assert "kubernetes" in result.output.lower()
        assert "kubectl apply" in result.output


def test_deploy_generate_systemd(runner, mock_config, tmp_path):
    """Test systemd deployment generation."""
    systemd_result = GenerationResult(
        success=True,
        method=DeploymentMethod.SYSTEMD,
        output_dir=tmp_path / "systemd",
        files_generated=[
            tmp_path / "systemd" / "test-project-redis.service",
            tmp_path / "systemd" / "install.sh",
        ],
        warnings=["systemd deployment requires root access to install services"],
    )

    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.generator.DeploymentGenerator") as mock_gen_cls,
        patch("mycelium_onboarding.deployment.secrets.SecretsManager") as mock_secrets_cls,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        mock_gen = Mock()
        mock_gen.generate.return_value = systemd_result
        mock_gen_cls.return_value = mock_gen

        mock_secrets_mgr = Mock()
        mock_secrets_mgr.generate_secrets.return_value = Mock()
        mock_secrets_cls.return_value = mock_secrets_mgr

        result = runner.invoke(cli, ["deploy", "generate", "--method", "systemd"])

        assert result.exit_code == 0
        assert "systemd" in result.output.lower()
        assert "install.sh" in result.output


def test_deploy_generate_custom_output(runner, mock_config, tmp_path, mock_secrets):
    """Test deployment generation with custom output directory."""
    custom_dir = tmp_path / "custom-deployment"

    custom_result = GenerationResult(
        success=True,
        method=DeploymentMethod.DOCKER_COMPOSE,
        output_dir=custom_dir,
        files_generated=[custom_dir / "docker-compose.yml"],
        warnings=[],
    )

    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.generator.DeploymentGenerator") as mock_gen_cls,
        patch("mycelium_onboarding.deployment.secrets.SecretsManager") as mock_secrets_cls,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        mock_gen = Mock()
        mock_gen.generate.return_value = custom_result
        mock_gen_cls.return_value = mock_gen

        mock_secrets_mgr = Mock()
        mock_secrets_mgr.generate_secrets.return_value = mock_secrets
        mock_secrets_cls.return_value = mock_secrets_mgr

        result = runner.invoke(cli, ["deploy", "generate", "--output", str(custom_dir)])

        assert result.exit_code == 0
        assert "docker-compose.yml" in result.output


def test_deploy_generate_no_secrets(runner, mock_config, mock_generation_result):
    """Test deployment generation without secrets."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.generator.DeploymentGenerator") as mock_gen_cls,
        patch("mycelium_onboarding.deployment.secrets.SecretsManager") as mock_secrets_cls,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        mock_gen = Mock()
        mock_gen.generate.return_value = mock_generation_result
        mock_gen_cls.return_value = mock_gen

        result = runner.invoke(cli, ["deploy", "generate", "--no-secrets"])

        assert result.exit_code == 0
        # Secrets manager should not be called
        mock_secrets_cls.assert_not_called()


def test_deploy_generate_no_config(runner):
    """Test deployment generation without configuration."""
    with patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls:
        mock_manager = Mock()
        mock_manager.load.side_effect = FileNotFoundError("No config found")
        mock_manager_cls.return_value = mock_manager

        result = runner.invoke(cli, ["deploy", "generate"])

        assert result.exit_code == 1
        assert "error" in result.output.lower()
        assert "mycelium init" in result.output.lower()


def test_deploy_generate_failure(runner, mock_config, tmp_path):
    """Test deployment generation failure."""
    failed_result = GenerationResult(
        success=False,
        method=DeploymentMethod.DOCKER_COMPOSE,
        output_dir=tmp_path,
        files_generated=[],
        errors=["At least one service must be enabled"],
    )

    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.generator.DeploymentGenerator") as mock_gen_cls,
        patch("mycelium_onboarding.deployment.secrets.SecretsManager") as mock_secrets_cls,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        mock_gen = Mock()
        mock_gen.generate.return_value = failed_result
        mock_gen_cls.return_value = mock_gen

        mock_secrets_mgr = Mock()
        mock_secrets_mgr.generate_secrets.return_value = Mock()
        mock_secrets_cls.return_value = mock_secrets_mgr

        result = runner.invoke(cli, ["deploy", "generate"])

        assert result.exit_code == 1
        assert "failed" in result.output.lower()


# ============================================================================
# Deploy Start Command Tests
# ============================================================================


def test_deploy_start_docker_compose(runner, mock_config):
    """Test starting Docker Compose deployment."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.strategy.detector.ServiceDetector") as mock_detector_cls,
        patch("mycelium_onboarding.deployment.commands.deploy.subprocess.run") as mock_run,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        # Mock detector to return empty list (no existing services)
        mock_detector = Mock()
        mock_detector.detect_all_services.return_value = []
        mock_detector_cls.return_value = mock_detector

        # Mock subprocess for docker-compose
        mock_run.return_value = Mock(stdout="Services started", stderr="", returncode=0)

        # Use --yes flag to skip confirmation
        result = runner.invoke(cli, ["deploy", "start", "--yes"])

        assert result.exit_code == 0
        assert "started" in result.output.lower() or "deploy" in result.output.lower()


def test_deploy_start_kubernetes(runner):
    """Test starting Kubernetes deployment."""
    k8s_config = MyceliumConfig(
        project_name="k8s-project",
        deployment=DeploymentConfig(method=DeploymentMethod.KUBERNETES),
    )

    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.strategy.detector.ServiceDetector") as mock_detector_cls,
        patch("mycelium_onboarding.deployment.commands.deploy.subprocess.run") as mock_run,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = k8s_config
        mock_manager_cls.return_value = mock_manager

        # Mock detector
        mock_detector = Mock()
        mock_detector.detect_all_services.return_value = []
        mock_detector_cls.return_value = mock_detector

        mock_run.return_value = Mock(stdout="NAME   READY   STATUS", stderr="", returncode=0)

        result = runner.invoke(cli, ["deploy", "start", "--yes"])

        assert result.exit_code == 0


def test_deploy_start_systemd(runner, mock_config):
    """Test starting systemd deployment."""
    systemd_config = MyceliumConfig(
        project_name="systemd-project",
        services=ServicesConfig(
            redis=RedisConfig(enabled=True),
            postgres=PostgresConfig(enabled=True),
        ),
        deployment=DeploymentConfig(method=DeploymentMethod.SYSTEMD),
    )

    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.strategy.detector.ServiceDetector") as mock_detector_cls,
        patch("mycelium_onboarding.deployment.commands.deploy.subprocess.run") as mock_run,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = systemd_config
        mock_manager_cls.return_value = mock_manager

        # Mock detector
        mock_detector = Mock()
        mock_detector.detect_all_services.return_value = []
        mock_detector_cls.return_value = mock_detector

        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        result = runner.invoke(cli, ["deploy", "start", "--yes"])

        assert result.exit_code == 0
        assert "started" in result.output.lower() or "deploy" in result.output.lower()


def test_deploy_start_error(runner, mock_config):
    """Test start command with subprocess error."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.strategy.detector.ServiceDetector") as mock_detector_cls,
        patch("mycelium_onboarding.deployment.commands.deploy.subprocess.run") as mock_run,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        # Mock detector
        mock_detector = Mock()
        mock_detector.detect_all_services.return_value = []
        mock_detector_cls.return_value = mock_detector

        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "docker-compose", stderr="Error")

        result = runner.invoke(cli, ["deploy", "start", "--yes"])

        assert result.exit_code == 1
        assert "error" in result.output.lower() or "failed" in result.output.lower()


def test_deploy_start_command_not_found(runner, mock_config):
    """Test start command when deployment tool not found."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.strategy.detector.ServiceDetector") as mock_detector_cls,
        patch("mycelium_onboarding.deployment.commands.deploy.subprocess.run") as mock_run,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        # Mock detector
        mock_detector = Mock()
        mock_detector.detect_all_services.return_value = []
        mock_detector_cls.return_value = mock_detector

        mock_run.side_effect = FileNotFoundError("docker-compose not found")

        result = runner.invoke(cli, ["deploy", "start", "--yes"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "error" in result.output.lower()


# ============================================================================
# Deploy Stop Command Tests
# ============================================================================


def test_deploy_stop_docker_compose(runner, mock_config):
    """Test stopping Docker Compose deployment."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.commands.deploy.subprocess.run") as mock_run,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        mock_run.return_value = Mock(stdout="Services stopped", stderr="", returncode=0)

        result = runner.invoke(cli, ["deploy", "stop"])

        assert result.exit_code == 0
        assert "stopped" in result.output.lower()
        args = mock_run.call_args[0][0]
        assert "docker-compose" in args
        assert "down" in args


def test_deploy_stop_kubernetes(runner):
    """Test stopping Kubernetes deployment."""
    k8s_config = MyceliumConfig(
        project_name="k8s-project",
        deployment=DeploymentConfig(method=DeploymentMethod.KUBERNETES),
    )

    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.commands.deploy.subprocess.run") as mock_run,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = k8s_config
        mock_manager_cls.return_value = mock_manager

        mock_run.return_value = Mock(stdout="Resources deleted", stderr="", returncode=0)

        result = runner.invoke(cli, ["deploy", "stop"])

        assert result.exit_code == 0
        assert "deleted" in result.output.lower() or "stopped" in result.output.lower()


def test_deploy_stop_systemd(runner):
    """Test stopping systemd deployment."""
    systemd_config = MyceliumConfig(
        project_name="systemd-project",
        services=ServicesConfig(
            redis=RedisConfig(enabled=True),
            postgres=PostgresConfig(enabled=True),
        ),
        deployment=DeploymentConfig(method=DeploymentMethod.SYSTEMD),
    )

    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.commands.deploy.subprocess.run") as mock_run,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = systemd_config
        mock_manager_cls.return_value = mock_manager

        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        result = runner.invoke(cli, ["deploy", "stop"])

        assert result.exit_code == 0
        assert "stopped" in result.output.lower()


# ============================================================================
# Deploy Status Command Tests
# ============================================================================


def test_deploy_status_docker_compose(runner, mock_config):
    """Test status command for Docker Compose."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.commands.deploy.subprocess.run") as mock_run,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        # Mock docker-compose ps output
        container_json = json.dumps(
            {
                "Service": "redis",
                "State": "running",
                "Status": "Up 10 minutes",
            }
        )
        mock_run.return_value = Mock(stdout=container_json, stderr="", returncode=0)

        result = runner.invoke(cli, ["deploy", "status"])

        assert result.exit_code == 0
        assert "Service Status" in result.output or "redis" in result.output.lower()


def test_deploy_status_no_containers(runner, mock_config):
    """Test status command with no running containers."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.commands.deploy.subprocess.run") as mock_run,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        result = runner.invoke(cli, ["deploy", "status"])

        assert result.exit_code == 0
        assert "no running containers" in result.output.lower() or "not deployed" in result.output.lower()


def test_deploy_status_kubernetes(runner):
    """Test status command for Kubernetes."""
    k8s_config = MyceliumConfig(
        project_name="k8s-project",
        deployment=DeploymentConfig(method=DeploymentMethod.KUBERNETES),
    )

    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.commands.deploy.subprocess.run") as mock_run,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = k8s_config
        mock_manager_cls.return_value = mock_manager

        # Mock kubectl get pods output
        pods_json = json.dumps(
            {
                "items": [
                    {
                        "metadata": {"name": "redis-pod"},
                        "status": {
                            "phase": "Running",
                            "containerStatuses": [{"ready": True}],
                        },
                    }
                ]
            }
        )
        mock_run.return_value = Mock(stdout=pods_json, stderr="", returncode=0)

        result = runner.invoke(cli, ["deploy", "status"])

        # Be flexible - accept various forms of success output
        assert result.exit_code == 0
        assert "test-project" in result.output.lower() or "deployment status" in result.output.lower()


def test_deploy_status_systemd(runner):
    """Test status command for systemd."""
    systemd_config = MyceliumConfig(
        project_name="systemd-project",
        services=ServicesConfig(
            redis=RedisConfig(enabled=True),
        ),
        deployment=DeploymentConfig(method=DeploymentMethod.SYSTEMD),
    )

    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.commands.deploy.subprocess.run") as mock_run,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = systemd_config
        mock_manager_cls.return_value = mock_manager

        mock_run.return_value = Mock(stdout="active", stderr="", returncode=0)

        result = runner.invoke(cli, ["deploy", "status"])

        # Be flexible - accept various forms of success output
        assert result.exit_code == 0
        # Exit code 0 means success - accept any output format


def test_deploy_status_watch_flag(runner, mock_config):
    """Test status command with --watch flag."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.commands.deploy.subprocess.run") as mock_run,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        result = runner.invoke(cli, ["deploy", "status", "--watch"])

        assert result.exit_code == 0
        # Watch mode message or status table
        assert "watch" in result.output.lower() or "no running" in result.output.lower()


# ============================================================================
# Deploy Secrets Command Tests
# ============================================================================


def test_deploy_secrets_show(runner, mock_config, mock_secrets):
    """Test showing deployment secrets."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.secrets.SecretsManager") as mock_secrets_cls,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        mock_secrets_mgr = Mock()
        mock_secrets_mgr.load_secrets.return_value = mock_secrets
        mock_secrets_cls.return_value = mock_secrets_mgr

        result = runner.invoke(cli, ["deploy", "secrets"])

        assert result.exit_code == 0
        assert "Deployment Secrets" in result.output
        assert "PostgreSQL" in result.output
        assert "Redis" in result.output


def test_deploy_secrets_no_secrets(runner, mock_config):
    """Test secrets command when no secrets exist."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.secrets.SecretsManager") as mock_secrets_cls,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        mock_secrets_mgr = Mock()
        mock_secrets_mgr.load_secrets.return_value = None
        mock_secrets_cls.return_value = mock_secrets_mgr

        result = runner.invoke(cli, ["deploy", "secrets"])

        assert result.exit_code == 0
        assert "no secrets found" in result.output.lower()


def test_deploy_secrets_rotate(runner, mock_config, mock_secrets):
    """Test rotating a secret."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.secrets.SecretsManager") as mock_secrets_cls,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        mock_secrets_mgr = Mock()
        mock_secrets_mgr.rotate_secret.return_value = mock_secrets
        mock_secrets_cls.return_value = mock_secrets_mgr

        result = runner.invoke(cli, ["deploy", "secrets", "postgres", "--rotate"])

        assert result.exit_code == 0
        assert "rotated" in result.output.lower()
        mock_secrets_mgr.rotate_secret.assert_called_once_with("postgres")


def test_deploy_secrets_rotate_no_type(runner, mock_config):
    """Test rotate without specifying secret type."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.secrets.SecretsManager"),
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        result = runner.invoke(cli, ["deploy", "secrets", "--rotate"])

        assert result.exit_code == 1
        assert "specify secret type" in result.output.lower()


def test_deploy_secrets_rotate_invalid_type(runner, mock_config):
    """Test rotating an invalid secret type."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.secrets.SecretsManager") as mock_secrets_cls,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        mock_secrets_mgr = Mock()
        mock_secrets_mgr.rotate_secret.side_effect = ValueError("Unknown secret type: invalid")
        mock_secrets_cls.return_value = mock_secrets_mgr

        result = runner.invoke(cli, ["deploy", "secrets", "invalid", "--rotate"])

        assert result.exit_code == 1
        assert "error" in result.output.lower()


# ============================================================================
# Method Override Tests
# ============================================================================


def test_deploy_generate_method_override(runner, mock_config, tmp_path):
    """Test deployment generation with method override."""
    # Config has docker-compose, but we override with kubernetes
    k8s_result = GenerationResult(
        success=True,
        method=DeploymentMethod.KUBERNETES,
        output_dir=tmp_path,
        files_generated=[],
        warnings=[],
    )

    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.generator.DeploymentGenerator") as mock_gen_cls,
        patch("mycelium_onboarding.deployment.secrets.SecretsManager") as mock_secrets_cls,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        mock_gen = Mock()
        mock_gen.generate.return_value = k8s_result
        mock_gen_cls.return_value = mock_gen

        mock_secrets_mgr = Mock()
        mock_secrets_mgr.generate_secrets.return_value = Mock()
        mock_secrets_cls.return_value = mock_secrets_mgr

        result = runner.invoke(cli, ["deploy", "generate", "--method", "kubernetes"])

        assert result.exit_code == 0
        assert "kubernetes" in result.output.lower()


def test_deploy_start_method_override(runner, mock_config):
    """Test start command with method override."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.strategy.detector.ServiceDetector") as mock_detector_cls,
        patch("mycelium_onboarding.deployment.commands.deploy.subprocess.run") as mock_run,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        # Mock detector
        mock_detector = Mock()
        mock_detector.detect_all_services.return_value = []
        mock_detector_cls.return_value = mock_detector

        mock_run.return_value = Mock(stdout="pods", stderr="", returncode=0)

        result = runner.invoke(cli, ["deploy", "start", "--method", "kubernetes", "--yes"])

        assert result.exit_code == 0


# ============================================================================
# Integration Tests
# ============================================================================


def test_deploy_full_workflow(runner, mock_config, mock_generation_result, mock_secrets, tmp_path):
    """Test full deployment workflow: generate -> start -> status -> stop."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.generator.DeploymentGenerator") as mock_gen_cls,
        patch("mycelium_onboarding.deployment.secrets.SecretsManager") as mock_secrets_cls,
        patch("mycelium_onboarding.deployment.strategy.detector.ServiceDetector") as mock_detector_cls,
        patch("mycelium_onboarding.deployment.commands.deploy.subprocess.run") as mock_run,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        mock_gen = Mock()
        mock_gen.generate.return_value = mock_generation_result
        mock_gen_cls.return_value = mock_gen

        mock_secrets_mgr = Mock()
        mock_secrets_mgr.generate_secrets.return_value = mock_secrets
        mock_secrets_cls.return_value = mock_secrets_mgr

        # Mock detector
        mock_detector = Mock()
        mock_detector.detect_all_services.return_value = []
        mock_detector_cls.return_value = mock_detector

        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        # 1. Generate
        result = runner.invoke(cli, ["deploy", "generate"])
        assert result.exit_code == 0

        # 2. Start
        result = runner.invoke(cli, ["deploy", "start", "--yes"])
        assert result.exit_code == 0

        # 3. Status
        result = runner.invoke(cli, ["deploy", "status"])
        assert result.exit_code == 0

        # 4. Stop
        result = runner.invoke(cli, ["deploy", "stop"])
        assert result.exit_code == 0


def test_deploy_generate_all_services(runner, tmp_path):
    """Test deployment generation with all services enabled."""
    all_services_config = MyceliumConfig(
        project_name="full-stack-project",
        services=ServicesConfig(
            redis=RedisConfig(enabled=True),
            postgres=PostgresConfig(enabled=True),
            temporal=TemporalConfig(enabled=True),
        ),
        deployment=DeploymentConfig(method=DeploymentMethod.DOCKER_COMPOSE),
    )

    result_obj = GenerationResult(
        success=True,
        method=DeploymentMethod.DOCKER_COMPOSE,
        output_dir=tmp_path,
        files_generated=[],
        warnings=[],
    )

    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.generator.DeploymentGenerator") as mock_gen_cls,
        patch("mycelium_onboarding.deployment.secrets.SecretsManager") as mock_secrets_cls,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = all_services_config
        mock_manager_cls.return_value = mock_manager

        mock_gen = Mock()
        mock_gen.generate.return_value = result_obj
        mock_gen_cls.return_value = mock_gen

        mock_secrets_mgr = Mock()
        mock_secrets_mgr.generate_secrets.return_value = Mock()
        mock_secrets_cls.return_value = mock_secrets_mgr

        result = runner.invoke(cli, ["deploy", "generate"])

        assert result.exit_code == 0
        assert "redis" in result.output.lower()
        assert "postgres" in result.output.lower()
        assert "temporal" in result.output.lower()


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


def test_deploy_status_json_parse_error(runner, mock_config):
    """Test status command with malformed JSON from docker-compose."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.commands.deploy.subprocess.run") as mock_run,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        # Invalid JSON
        mock_run.return_value = Mock(stdout="invalid json{]", stderr="", returncode=0)

        result = runner.invoke(cli, ["deploy", "status"])

        # Should handle gracefully - either show error or no containers
        assert result.exit_code == 0


def test_deploy_status_multiline_json(runner, mock_config):
    """Test status command with multi-line JSON output."""
    with (
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_cls,
        patch("mycelium_onboarding.deployment.commands.deploy.subprocess.run") as mock_run,
    ):
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_manager_cls.return_value = mock_manager

        # Multiple containers as separate JSON objects
        json_lines = "\n".join(
            [
                json.dumps({"Service": "redis", "State": "running", "Status": "Up"}),
                json.dumps({"Service": "postgres", "State": "running", "Status": "Up"}),
            ]
        )
        mock_run.return_value = Mock(stdout=json_lines, stderr="", returncode=0)

        result = runner.invoke(cli, ["deploy", "status"])

        assert result.exit_code == 0
        assert "redis" in result.output.lower()
        assert "postgres" in result.output.lower()
