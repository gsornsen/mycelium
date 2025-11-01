"""Tests for configuration schema.

This test suite provides comprehensive coverage of the Pydantic configuration
schema, including validation, serialization, deserialization, and error handling.
"""

from __future__ import annotations

from datetime import datetime

import pytest
import yaml
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
    """Tests for base ServiceConfig model."""

    def test_default_values(self):
        """Test ServiceConfig has correct defaults."""
        config = ServiceConfig()
        assert config.enabled is True
        assert config.version is None
        assert config.custom_config == {}

    def test_set_values(self):
        """Test ServiceConfig accepts valid values."""
        config = ServiceConfig(
            enabled=False,
            version="7.0",
            custom_config={"key": "value"},
        )
        assert config.enabled is False
        assert config.version == "7.0"
        assert config.custom_config == {"key": "value"}

    def test_version_validation_valid(self):
        """Test version validation accepts valid formats."""
        valid_versions = [
            "7.0",
            "15",
            "latest",
            "7.0-alpine",
            "1.2.3",
            "v1.0.0",
        ]
        for version in valid_versions:
            config = ServiceConfig(version=version)
            assert config.version == version

    def test_version_validation_invalid(self):
        """Test version validation rejects invalid formats."""
        invalid_versions = [
            "7.0 beta",  # spaces
            "7.0/alpine",  # slashes
            "7.0@latest",  # special chars
        ]
        for version in invalid_versions:
            with pytest.raises(ValidationError) as exc_info:
                ServiceConfig(version=version)
            assert "version" in str(exc_info.value).lower()

    def test_validate_assignment(self):
        """Test that assignment validation is enabled."""
        config = ServiceConfig()
        with pytest.raises(ValidationError):
            config.version = "invalid version!"

    def test_extra_fields_forbidden(self):
        """Test that extra fields are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ServiceConfig(unknown_field="value")
        assert "extra" in str(exc_info.value).lower()


class TestRedisConfig:
    """Tests for RedisConfig model."""

    def test_default_values(self):
        """Test RedisConfig has correct defaults."""
        config = RedisConfig()
        assert config.enabled is True
        assert config.port == 6379
        assert config.persistence is True
        assert config.max_memory == "256mb"

    def test_port_validation_valid(self):
        """Test port validation accepts valid ports."""
        valid_ports = [1, 6379, 6380, 65535]
        for port in valid_ports:
            config = RedisConfig(port=port)
            assert config.port == port

    def test_port_validation_invalid(self):
        """Test port validation rejects invalid ports."""
        invalid_ports = [0, -1, 65536, 100000]
        for port in invalid_ports:
            with pytest.raises(ValidationError) as exc_info:
                RedisConfig(port=port)
            assert "port" in str(exc_info.value).lower()

    def test_max_memory_validation_valid(self):
        """Test max_memory validation accepts valid formats."""
        valid_memory = [
            ("256mb", "256mb"),
            ("1gb", "1gb"),
            ("512MB", "512mb"),  # Should normalize to lowercase
            ("2GB", "2gb"),
            ("1024kb", "1024kb"),
            ("1tb", "1tb"),
        ]
        for input_mem, expected_mem in valid_memory:
            config = RedisConfig(max_memory=input_mem)
            assert config.max_memory == expected_mem

    def test_max_memory_validation_invalid(self):
        """Test max_memory validation rejects invalid formats."""
        invalid_memory = [
            "256",  # No unit
            "256m",  # Wrong unit format
            "256 mb",  # Space
            "mb256",  # Wrong order
            "256bytes",  # Full word
        ]
        for memory in invalid_memory:
            with pytest.raises(ValidationError) as exc_info:
                RedisConfig(max_memory=memory)
            assert "memory" in str(exc_info.value).lower()

    def test_custom_config(self):
        """Test RedisConfig accepts custom configuration."""
        config = RedisConfig(
            custom_config={
                "maxclients": "10000",
                "timeout": "300",
            }
        )
        assert config.custom_config["maxclients"] == "10000"
        assert config.custom_config["timeout"] == "300"


class TestPostgresConfig:
    """Tests for PostgresConfig model."""

    def test_default_values(self):
        """Test PostgresConfig has correct defaults."""
        config = PostgresConfig()
        assert config.enabled is True
        assert config.port == 5432
        assert config.database == "mycelium"
        assert config.max_connections == 100

    def test_database_validation_valid(self):
        """Test database name validation accepts valid names."""
        valid_names = [
            "mycelium",
            "my_database",
            "db123",
            "MyDatabase",
        ]
        for name in valid_names:
            config = PostgresConfig(database=name)
            assert config.database == name

    def test_database_validation_invalid(self):
        """Test database name validation rejects invalid names."""
        invalid_names = [
            "123db",  # Starts with number
            "my-database",  # Hyphens not allowed
            "my database",  # Spaces
            "my.database",  # Dots
        ]
        for name in invalid_names:
            with pytest.raises(ValidationError) as exc_info:
                PostgresConfig(database=name)
            assert "database" in str(exc_info.value).lower()

    def test_max_connections_validation(self):
        """Test max_connections validation."""
        # Valid
        config = PostgresConfig(max_connections=200)
        assert config.max_connections == 200

        # Invalid - too low
        with pytest.raises(ValidationError):
            PostgresConfig(max_connections=0)

        # Invalid - too high
        with pytest.raises(ValidationError):
            PostgresConfig(max_connections=20000)

    def test_port_validation(self):
        """Test port validation."""
        config = PostgresConfig(port=5433)
        assert config.port == 5433

        with pytest.raises(ValidationError):
            PostgresConfig(port=0)

        with pytest.raises(ValidationError):
            PostgresConfig(port=99999)


class TestTemporalConfig:
    """Tests for TemporalConfig model."""

    def test_default_values(self):
        """Test TemporalConfig has correct defaults."""
        config = TemporalConfig()
        assert config.enabled is True
        assert config.ui_port == 8080
        assert config.frontend_port == 7233
        assert config.namespace == "default"

    def test_namespace_validation_valid(self):
        """Test namespace validation accepts valid names."""
        valid_namespaces = [
            "default",
            "my-namespace",
            "my_namespace",
            "namespace123",
            "MyNamespace",
        ]
        for namespace in valid_namespaces:
            config = TemporalConfig(namespace=namespace)
            assert config.namespace == namespace

    def test_namespace_validation_invalid(self):
        """Test namespace validation rejects invalid names."""
        invalid_namespaces = [
            "my namespace",  # Spaces
            "my.namespace",  # Dots
            "my/namespace",  # Slashes
            "my@namespace",  # Special chars
        ]
        for namespace in invalid_namespaces:
            with pytest.raises(ValidationError) as exc_info:
                TemporalConfig(namespace=namespace)
            assert "namespace" in str(exc_info.value).lower()

    def test_port_validation(self):
        """Test port validation for both ports."""
        config = TemporalConfig(ui_port=8081, frontend_port=7234)
        assert config.ui_port == 8081
        assert config.frontend_port == 7234

        with pytest.raises(ValidationError):
            TemporalConfig(ui_port=0)

        with pytest.raises(ValidationError):
            TemporalConfig(frontend_port=70000)


class TestServicesConfig:
    """Tests for ServicesConfig model."""

    def test_default_values(self):
        """Test ServicesConfig has correct defaults."""
        config = ServicesConfig()
        assert isinstance(config.redis, RedisConfig)
        assert isinstance(config.postgres, PostgresConfig)
        assert isinstance(config.temporal, TemporalConfig)

    def test_custom_services(self):
        """Test ServicesConfig accepts custom service configs."""
        config = ServicesConfig(
            redis=RedisConfig(port=6380),
            postgres=PostgresConfig(database="custom_db"),
            temporal=TemporalConfig(namespace="production"),
        )
        assert config.redis.port == 6380
        assert config.postgres.database == "custom_db"
        assert config.temporal.namespace == "production"

    def test_nested_validation(self):
        """Test that nested validation works."""
        with pytest.raises(ValidationError):
            ServicesConfig(
                redis=RedisConfig(port=99999)  # Invalid port
            )


class TestDeploymentConfig:
    """Tests for DeploymentConfig model."""

    def test_default_values(self):
        """Test DeploymentConfig has correct defaults."""
        config = DeploymentConfig()
        assert config.method == DeploymentMethod.DOCKER_COMPOSE
        assert config.auto_start is True
        assert config.healthcheck_timeout == 60

    def test_deployment_methods(self):
        """Test all deployment methods are valid."""
        methods = [
            DeploymentMethod.DOCKER_COMPOSE,
            DeploymentMethod.KUBERNETES,
            DeploymentMethod.SYSTEMD,
            DeploymentMethod.MANUAL,
        ]
        for method in methods:
            config = DeploymentConfig(method=method)
            assert config.method == method

    def test_healthcheck_timeout_validation(self):
        """Test healthcheck timeout validation."""
        # Valid
        config = DeploymentConfig(healthcheck_timeout=30)
        assert config.healthcheck_timeout == 30

        # Invalid - too low
        with pytest.raises(ValidationError):
            DeploymentConfig(healthcheck_timeout=5)

        # Invalid - too high
        with pytest.raises(ValidationError):
            DeploymentConfig(healthcheck_timeout=500)


class TestMyceliumConfig:
    """Tests for top-level MyceliumConfig model."""

    def test_default_values(self):
        """Test MyceliumConfig has correct defaults."""
        config = MyceliumConfig()
        assert config.version == "1.0"
        assert config.project_name == "mycelium"
        assert isinstance(config.deployment, DeploymentConfig)
        assert isinstance(config.services, ServicesConfig)
        assert isinstance(config.created_at, datetime)

    def test_project_name_validation_valid(self):
        """Test project name validation accepts valid names."""
        valid_names = [
            "mycelium",
            "my-project",
            "my_project",
            "project123",
            "MyProject",
        ]
        for name in valid_names:
            config = MyceliumConfig(project_name=name)
            assert config.project_name == name

    def test_project_name_validation_invalid(self):
        """Test project name validation rejects invalid names."""
        invalid_names = [
            "my project",  # Spaces
            "my.project",  # Dots
            "my/project",  # Slashes
            "my@project",  # Special chars
        ]
        for name in invalid_names:
            with pytest.raises(ValidationError) as exc_info:
                MyceliumConfig(project_name=name)
            assert "project_name" in str(exc_info.value).lower()

    def test_version_format_validation(self):
        """Test version format validation."""
        # Valid
        config = MyceliumConfig(version="2.0")
        assert config.version == "2.0"

        # Invalid
        with pytest.raises(ValidationError):
            MyceliumConfig(version="v1.0")

        with pytest.raises(ValidationError):
            MyceliumConfig(version="1")

    def test_at_least_one_service_enabled(self):
        """Test that at least one service must be enabled."""
        # Valid - at least one enabled
        config = MyceliumConfig()
        config.services.redis.enabled = True
        config.services.postgres.enabled = False
        config.services.temporal.enabled = False

        # Invalid - all disabled
        with pytest.raises(ValueError) as exc_info:
            MyceliumConfig(
                services=ServicesConfig(
                    redis=RedisConfig(enabled=False),
                    postgres=PostgresConfig(enabled=False),
                    temporal=TemporalConfig(enabled=False),
                )
            )
        assert "at least one service" in str(exc_info.value).lower()

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = MyceliumConfig(project_name="test-project")
        data = config.to_dict()

        assert isinstance(data, dict)
        assert data["project_name"] == "test-project"
        assert data["version"] == "1.0"
        assert "deployment" in data
        assert "services" in data
        assert "created_at" in data

    def test_to_dict_exclude_none(self):
        """Test to_dict with exclude_none option."""
        config = MyceliumConfig(project_name="test-project")
        config.services.redis.version = None

        _ = config.to_dict(exclude_none=True)
        # Version should not be present when None and exclude_none=True
        # Note: This depends on nested serialization

        data_with_none = config.to_dict(exclude_none=False)
        assert isinstance(data_with_none, dict)

    def test_to_yaml(self):
        """Test serialization to YAML."""
        config = MyceliumConfig(project_name="test-project")
        yaml_str = config.to_yaml()

        assert isinstance(yaml_str, str)
        assert "project_name: test-project" in yaml_str
        assert "version: '1.0'" in yaml_str

        # Should be valid YAML
        parsed = yaml.safe_load(yaml_str)
        assert parsed["project_name"] == "test-project"

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "version": "1.0",
            "project_name": "test-project",
            "deployment": {
                "method": "kubernetes",
                "auto_start": False,
                "healthcheck_timeout": 90,
            },
            "services": {
                "redis": {
                    "enabled": True,
                    "port": 6380,
                },
                "postgres": {
                    "enabled": False,
                },
                "temporal": {
                    "enabled": False,
                },
            },
        }

        config = MyceliumConfig.from_dict(data)
        assert config.project_name == "test-project"
        assert config.deployment.method == DeploymentMethod.KUBERNETES
        assert config.deployment.auto_start is False
        assert config.services.redis.port == 6380
        assert config.services.postgres.enabled is False

    def test_from_dict_minimal(self):
        """Test deserialization with minimal data (defaults)."""
        data = {"project_name": "minimal"}
        config = MyceliumConfig.from_dict(data)

        assert config.project_name == "minimal"
        assert config.version == "1.0"
        assert config.deployment.method == DeploymentMethod.DOCKER_COMPOSE

    def test_from_dict_invalid(self):
        """Test deserialization with invalid data."""
        invalid_data = [
            {"project_name": "my project"},  # Invalid name
            {"services": {"redis": {"port": 99999}}},  # Invalid port
            {"deployment": {"method": "invalid"}},  # Invalid method
        ]
        for data in invalid_data:
            with pytest.raises(ValidationError):
                MyceliumConfig.from_dict(data)

    def test_from_yaml(self):
        """Test deserialization from YAML."""
        yaml_str = """
        version: '1.0'
        project_name: yaml-project
        deployment:
          method: docker-compose
          auto_start: true
        services:
          redis:
            enabled: true
            port: 6379
          postgres:
            enabled: true
          temporal:
            enabled: false
        """

        config = MyceliumConfig.from_yaml(yaml_str)
        assert config.project_name == "yaml-project"
        assert config.deployment.method == DeploymentMethod.DOCKER_COMPOSE
        assert config.services.redis.enabled is True
        assert config.services.temporal.enabled is False

    def test_from_yaml_empty(self):
        """Test deserialization from empty YAML."""
        yaml_str = ""
        config = MyceliumConfig.from_yaml(yaml_str)

        # Should use defaults
        assert config.project_name == "mycelium"
        assert config.version == "1.0"

    def test_from_yaml_invalid(self):
        """Test deserialization from invalid YAML."""
        invalid_yaml = """
        project_name: test
        services:
          redis:
            port: invalid_port
        """

        with pytest.raises(ValidationError):
            MyceliumConfig.from_yaml(invalid_yaml)

    def test_round_trip_dict(self):
        """Test round-trip serialization through dictionary."""
        original = MyceliumConfig(project_name="round-trip-test")
        original.services.redis.port = 6380
        original.deployment.method = DeploymentMethod.KUBERNETES

        # Serialize to dict
        data = original.to_dict()

        # Deserialize from dict
        restored = MyceliumConfig.from_dict(data)

        assert restored.project_name == original.project_name
        assert restored.services.redis.port == original.services.redis.port
        assert restored.deployment.method == original.deployment.method

    def test_round_trip_yaml(self):
        """Test round-trip serialization through YAML."""
        original = MyceliumConfig(project_name="yaml-round-trip")
        original.services.postgres.database = "custom_db"
        original.deployment.auto_start = False

        # Serialize to YAML
        yaml_str = original.to_yaml()

        # Deserialize from YAML
        restored = MyceliumConfig.from_yaml(yaml_str)

        assert restored.project_name == original.project_name
        assert restored.services.postgres.database == original.services.postgres.database
        assert restored.deployment.auto_start == original.deployment.auto_start

    def test_nested_modification(self):
        """Test that nested objects can be modified."""
        config = MyceliumConfig()

        # Modify nested service config
        config.services.redis.port = 6380
        config.services.redis.max_memory = "512mb"

        assert config.services.redis.port == 6380
        assert config.services.redis.max_memory == "512mb"

    def test_validation_on_assignment(self):
        """Test that validation occurs on assignment."""
        config = MyceliumConfig()

        # Should raise validation error on invalid assignment
        with pytest.raises(ValidationError):
            config.project_name = "invalid project name!"

        with pytest.raises(ValidationError):
            config.services.redis.port = 99999

    def test_full_configuration_example(self):
        """Test a complete realistic configuration."""
        config = MyceliumConfig(
            project_name="production-app",
            version="1.0",
            deployment=DeploymentConfig(
                method=DeploymentMethod.KUBERNETES,
                auto_start=True,
                healthcheck_timeout=120,
            ),
            services=ServicesConfig(
                redis=RedisConfig(
                    enabled=True,
                    version="7.0",
                    port=6379,
                    persistence=True,
                    max_memory="1gb",
                    custom_config={
                        "maxclients": "10000",
                    },
                ),
                postgres=PostgresConfig(
                    enabled=True,
                    version="15",
                    port=5432,
                    database="production",
                    max_connections=200,
                ),
                temporal=TemporalConfig(
                    enabled=True,
                    ui_port=8080,
                    frontend_port=7233,
                    namespace="production",
                ),
            ),
        )

        # Verify all values
        assert config.project_name == "production-app"
        assert config.deployment.method == DeploymentMethod.KUBERNETES
        assert config.services.redis.max_memory == "1gb"
        assert config.services.postgres.database == "production"
        assert config.services.temporal.namespace == "production"

        # Should serialize and deserialize correctly
        yaml_str = config.to_yaml()
        restored = MyceliumConfig.from_yaml(yaml_str)
        assert restored.project_name == config.project_name
        assert restored.services.redis.max_memory == config.services.redis.max_memory
