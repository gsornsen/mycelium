"""Unit tests for configuration schema validation."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from mycelium_onboarding.config.schema import (
    DeploymentConfig,
    DeploymentMethod,
    MyceliumConfig,
    PostgresConfig,
    RedisConfig,
    ServiceConfig,
    ServicesConfig,
    TemporalConfig,
)


class TestServiceConfig:
    """Test base ServiceConfig model."""

    def test_default_values(self) -> None:
        """Test default values for base service config."""
        config = ServiceConfig()
        assert config.enabled is True
        assert config.version is None
        assert config.custom_config == {}

    def test_version_validation(self) -> None:
        """Test version string validation."""
        # Valid versions
        ServiceConfig(version="7.0")
        ServiceConfig(version="15")
        ServiceConfig(version="latest")
        ServiceConfig(version="7.0-alpine")

        # Invalid version
        with pytest.raises(ValidationError, match="Version must contain only"):
            ServiceConfig(version="7.0@special")

    def test_extra_fields_forbidden(self) -> None:
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError):
            ServiceConfig(extra_field="not allowed")  # type: ignore


class TestRedisConfig:
    """Test RedisConfig model."""

    def test_default_values(self) -> None:
        """Test default Redis configuration values."""
        config = RedisConfig()
        assert config.enabled is True
        assert config.port == 6379
        assert config.persistence is True
        assert config.max_memory == "256mb"

    def test_port_validation(self) -> None:
        """Test port number validation."""
        # Valid ports
        RedisConfig(port=1)
        RedisConfig(port=6379)
        RedisConfig(port=65535)

        # Invalid ports
        with pytest.raises(ValidationError):
            RedisConfig(port=0)
        with pytest.raises(ValidationError):
            RedisConfig(port=65536)
        with pytest.raises(ValidationError):
            RedisConfig(port=-1)

    def test_max_memory_validation(self) -> None:
        """Test memory size format validation."""
        # Valid formats
        RedisConfig(max_memory="256mb")
        RedisConfig(max_memory="1gb")
        RedisConfig(max_memory="512MB")
        RedisConfig(max_memory="2GB")

        # Invalid formats
        with pytest.raises(ValidationError, match="Memory must be in format"):
            RedisConfig(max_memory="256")
        with pytest.raises(ValidationError):
            RedisConfig(max_memory="256 mb")
        with pytest.raises(ValidationError):
            RedisConfig(max_memory="invalid")

    def test_max_memory_normalization(self) -> None:
        """Test that memory size is normalized to lowercase."""
        config = RedisConfig(max_memory="256MB")
        assert config.max_memory == "256mb"


class TestPostgresConfig:
    """Test PostgresConfig model."""

    def test_default_values(self) -> None:
        """Test default PostgreSQL configuration values."""
        config = PostgresConfig()
        assert config.enabled is True
        assert config.port == 5432
        assert config.database == "mycelium"
        assert config.max_connections == 100

    def test_port_validation(self) -> None:
        """Test port number validation."""
        # Valid ports
        PostgresConfig(port=5432)
        PostgresConfig(port=5433)

        # Invalid ports
        with pytest.raises(ValidationError):
            PostgresConfig(port=0)
        with pytest.raises(ValidationError):
            PostgresConfig(port=65536)

    def test_database_name_validation(self) -> None:
        """Test database name validation."""
        # Valid names
        PostgresConfig(database="mycelium")
        PostgresConfig(database="test_db")
        PostgresConfig(database="db123")

        # Invalid names
        with pytest.raises(ValidationError, match="must start with a letter"):
            PostgresConfig(database="123db")
        with pytest.raises(ValidationError):
            PostgresConfig(database="my-db")  # hyphens not allowed
        with pytest.raises(ValidationError):
            PostgresConfig(database="")

    def test_max_connections_validation(self) -> None:
        """Test max connections validation."""
        # Valid values
        PostgresConfig(max_connections=1)
        PostgresConfig(max_connections=100)
        PostgresConfig(max_connections=10000)

        # Invalid values
        with pytest.raises(ValidationError):
            PostgresConfig(max_connections=0)
        with pytest.raises(ValidationError):
            PostgresConfig(max_connections=10001)


class TestTemporalConfig:
    """Test TemporalConfig model."""

    def test_default_values(self) -> None:
        """Test default Temporal configuration values."""
        config = TemporalConfig()
        assert config.enabled is True
        assert config.ui_port == 8080
        assert config.frontend_port == 7233
        assert config.namespace == "default"

    def test_port_validation(self) -> None:
        """Test port number validation."""
        # Valid ports
        TemporalConfig(ui_port=8080, frontend_port=7233)

        # Invalid ports
        with pytest.raises(ValidationError):
            TemporalConfig(ui_port=0)
        with pytest.raises(ValidationError):
            TemporalConfig(frontend_port=65536)

    def test_namespace_validation(self) -> None:
        """Test namespace validation."""
        # Valid namespaces
        TemporalConfig(namespace="default")
        TemporalConfig(namespace="my-namespace")
        TemporalConfig(namespace="my_namespace")
        TemporalConfig(namespace="namespace123")

        # Invalid namespaces
        with pytest.raises(ValidationError, match="must contain only alphanumeric"):
            TemporalConfig(namespace="my@namespace")
        with pytest.raises(ValidationError):
            TemporalConfig(namespace="")


class TestServicesConfig:
    """Test ServicesConfig model."""

    def test_default_values(self) -> None:
        """Test default services configuration."""
        config = ServicesConfig()
        assert isinstance(config.redis, RedisConfig)
        assert isinstance(config.postgres, PostgresConfig)
        assert isinstance(config.temporal, TemporalConfig)

    def test_nested_configuration(self) -> None:
        """Test nested service configuration."""
        config = ServicesConfig(
            redis=RedisConfig(port=6380),
            postgres=PostgresConfig(database="custom"),
        )
        assert config.redis.port == 6380
        assert config.postgres.database == "custom"


class TestDeploymentConfig:
    """Test DeploymentConfig model."""

    def test_default_values(self) -> None:
        """Test default deployment configuration."""
        config = DeploymentConfig()
        assert config.method == DeploymentMethod.DOCKER_COMPOSE
        assert config.auto_start is True
        assert config.healthcheck_timeout == 60

    def test_deployment_method_enum(self) -> None:
        """Test deployment method enum values."""
        config = DeploymentConfig(method=DeploymentMethod.KUBERNETES)
        assert config.method == DeploymentMethod.KUBERNETES

        config = DeploymentConfig(method=DeploymentMethod.SYSTEMD)
        assert config.method == DeploymentMethod.SYSTEMD

    def test_healthcheck_timeout_validation(self) -> None:
        """Test healthcheck timeout validation."""
        # Valid values
        DeploymentConfig(healthcheck_timeout=10)
        DeploymentConfig(healthcheck_timeout=60)
        DeploymentConfig(healthcheck_timeout=300)

        # Invalid values
        with pytest.raises(ValidationError):
            DeploymentConfig(healthcheck_timeout=9)
        with pytest.raises(ValidationError):
            DeploymentConfig(healthcheck_timeout=301)


class TestMyceliumConfig:
    """Test MyceliumConfig root model."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = MyceliumConfig()
        assert config.version == "1.0"
        assert config.project_name == "mycelium"
        assert isinstance(config.deployment, DeploymentConfig)
        assert isinstance(config.services, ServicesConfig)
        assert isinstance(config.created_at, datetime)

    def test_project_name_validation(self) -> None:
        """Test project name validation."""
        # Valid names
        MyceliumConfig(project_name="mycelium")
        MyceliumConfig(project_name="my-project")
        MyceliumConfig(project_name="my_project")
        MyceliumConfig(project_name="project123")

        # Invalid names
        with pytest.raises(ValidationError, match="must contain only alphanumeric"):
            MyceliumConfig(project_name="my@project")
        with pytest.raises(ValidationError):
            MyceliumConfig(project_name="")

    def test_version_pattern_validation(self) -> None:
        """Test version pattern validation."""
        # Valid versions
        MyceliumConfig(version="1.0")
        MyceliumConfig(version="2.5")

        # Invalid versions
        with pytest.raises(ValidationError):
            MyceliumConfig(version="1")
        with pytest.raises(ValidationError):
            MyceliumConfig(version="1.0.0")

    def test_at_least_one_service_enabled(self) -> None:
        """Test that at least one service must be enabled."""
        # Valid: at least one enabled
        MyceliumConfig(
            services=ServicesConfig(
                redis=RedisConfig(enabled=True),
                postgres=PostgresConfig(enabled=False),
                temporal=TemporalConfig(enabled=False),
            )
        )

        # Invalid: all disabled
        with pytest.raises(ValidationError, match="At least one service must be enabled"):
            MyceliumConfig(
                services=ServicesConfig(
                    redis=RedisConfig(enabled=False),
                    postgres=PostgresConfig(enabled=False),
                    temporal=TemporalConfig(enabled=False),
                )
            )

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        config = MyceliumConfig(project_name="test")
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["project_name"] == "test"
        assert config_dict["version"] == "1.0"
        assert "services" in config_dict
        assert "deployment" in config_dict

    def test_to_yaml(self) -> None:
        """Test serialization to YAML."""
        config = MyceliumConfig(project_name="test")
        yaml_str = config.to_yaml()

        assert isinstance(yaml_str, str)
        assert "project_name: test" in yaml_str
        assert "version: '1.0'" in yaml_str

    def test_from_dict(self) -> None:
        """Test deserialization from dictionary."""
        config_dict = {
            "version": "1.0",
            "project_name": "test",
        }
        config = MyceliumConfig.from_dict(config_dict)

        assert config.project_name == "test"
        assert config.version == "1.0"

    def test_from_yaml(self) -> None:
        """Test deserialization from YAML."""
        yaml_str = """
        version: '1.0'
        project_name: test
        services:
          redis:
            port: 6380
        """
        config = MyceliumConfig.from_yaml(yaml_str)

        assert config.project_name == "test"
        assert config.services.redis.port == 6380

    def test_from_yaml_empty(self) -> None:
        """Test deserialization from empty YAML."""
        config = MyceliumConfig.from_yaml("")
        assert config.project_name == "mycelium"  # Uses defaults

    def test_validate_assignment(self) -> None:
        """Test that assignment validation is enabled."""
        config = MyceliumConfig()

        # Valid assignment
        config.project_name = "new-project"
        assert config.project_name == "new-project"

        # Invalid assignment
        with pytest.raises(ValidationError):
            config.project_name = "invalid@name"

    def test_nested_config_modification(self) -> None:
        """Test modifying nested configuration."""
        config = MyceliumConfig()
        config.services.redis.port = 6380
        config.deployment.method = DeploymentMethod.KUBERNETES

        assert config.services.redis.port == 6380
        assert config.deployment.method == DeploymentMethod.KUBERNETES
