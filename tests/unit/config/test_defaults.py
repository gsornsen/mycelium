"""Unit tests for default configuration values."""

from mycelium_onboarding.config.defaults import (
    DEFAULT_AUTO_START,
    DEFAULT_DEPLOYMENT_METHOD,
    DEFAULT_HEALTHCHECK_TIMEOUT,
    DEFAULT_POSTGRES_DATABASE,
    DEFAULT_POSTGRES_ENABLED,
    DEFAULT_POSTGRES_MAX_CONNECTIONS,
    DEFAULT_POSTGRES_PORT,
    DEFAULT_POSTGRES_VERSION,
    DEFAULT_PROJECT_NAME,
    DEFAULT_REDIS_ENABLED,
    DEFAULT_REDIS_MAX_MEMORY,
    DEFAULT_REDIS_PERSISTENCE,
    DEFAULT_REDIS_PORT,
    DEFAULT_REDIS_VERSION,
    DEFAULT_SCHEMA_VERSION,
    DEFAULT_TEMPORAL_ENABLED,
    DEFAULT_TEMPORAL_FRONTEND_PORT,
    DEFAULT_TEMPORAL_NAMESPACE,
    DEFAULT_TEMPORAL_UI_PORT,
    DEFAULT_TEMPORAL_VERSION,
    get_default_config_dict,
    get_default_deployment_config,
    get_default_postgres_config,
    get_default_redis_config,
    get_default_services_config,
    get_default_temporal_config,
)
from mycelium_onboarding.config.schema import DeploymentMethod


class TestDefaultConstants:
    """Test default constant values."""

    def test_project_defaults(self) -> None:
        """Test project-level defaults."""
        assert DEFAULT_PROJECT_NAME == "mycelium"
        assert DEFAULT_SCHEMA_VERSION == "1.0"

    def test_redis_defaults(self) -> None:
        """Test Redis default values."""
        assert DEFAULT_REDIS_PORT == 6379
        assert DEFAULT_REDIS_PERSISTENCE is True
        assert DEFAULT_REDIS_MAX_MEMORY == "256mb"
        assert DEFAULT_REDIS_VERSION is None
        assert DEFAULT_REDIS_ENABLED is True

    def test_postgres_defaults(self) -> None:
        """Test PostgreSQL default values."""
        assert DEFAULT_POSTGRES_PORT == 5432
        assert DEFAULT_POSTGRES_DATABASE == "mycelium"
        assert DEFAULT_POSTGRES_MAX_CONNECTIONS == 100
        assert DEFAULT_POSTGRES_VERSION is None
        assert DEFAULT_POSTGRES_ENABLED is True

    def test_temporal_defaults(self) -> None:
        """Test Temporal default values."""
        assert DEFAULT_TEMPORAL_UI_PORT == 8080
        assert DEFAULT_TEMPORAL_FRONTEND_PORT == 7233
        assert DEFAULT_TEMPORAL_NAMESPACE == "default"
        assert DEFAULT_TEMPORAL_VERSION is None
        assert DEFAULT_TEMPORAL_ENABLED is True

    def test_deployment_defaults(self) -> None:
        """Test deployment default values."""
        assert DEFAULT_DEPLOYMENT_METHOD == DeploymentMethod.DOCKER_COMPOSE
        assert DEFAULT_AUTO_START is True
        assert DEFAULT_HEALTHCHECK_TIMEOUT == 60


class TestRedisDefaults:
    """Test Redis default configuration."""

    def test_get_default_redis_config(self) -> None:
        """Test getting default Redis configuration."""
        config = get_default_redis_config()

        assert isinstance(config, dict)
        assert config["enabled"] is True
        assert config["version"] is None
        assert config["custom_config"] == {}
        assert config["port"] == 6379
        assert config["persistence"] is True
        assert config["max_memory"] == "256mb"

    def test_redis_config_keys(self) -> None:
        """Test that all required keys are present."""
        config = get_default_redis_config()
        required_keys = {"enabled", "version", "custom_config", "port", "persistence", "max_memory"}
        assert set(config.keys()) == required_keys


class TestPostgresDefaults:
    """Test PostgreSQL default configuration."""

    def test_get_default_postgres_config(self) -> None:
        """Test getting default PostgreSQL configuration."""
        config = get_default_postgres_config()

        assert isinstance(config, dict)
        assert config["enabled"] is True
        assert config["version"] is None
        assert config["custom_config"] == {}
        assert config["port"] == 5432
        assert config["database"] == "mycelium"
        assert config["max_connections"] == 100

    def test_postgres_config_keys(self) -> None:
        """Test that all required keys are present."""
        config = get_default_postgres_config()
        required_keys = {"enabled", "version", "custom_config", "port", "database", "max_connections"}
        assert set(config.keys()) == required_keys


class TestTemporalDefaults:
    """Test Temporal default configuration."""

    def test_get_default_temporal_config(self) -> None:
        """Test getting default Temporal configuration."""
        config = get_default_temporal_config()

        assert isinstance(config, dict)
        assert config["enabled"] is True
        assert config["version"] is None
        assert config["custom_config"] == {}
        assert config["ui_port"] == 8080
        assert config["frontend_port"] == 7233
        assert config["namespace"] == "default"

    def test_temporal_config_keys(self) -> None:
        """Test that all required keys are present."""
        config = get_default_temporal_config()
        required_keys = {"enabled", "version", "custom_config", "ui_port", "frontend_port", "namespace"}
        assert set(config.keys()) == required_keys


class TestServicesDefaults:
    """Test services default configuration."""

    def test_get_default_services_config(self) -> None:
        """Test getting default services configuration."""
        config = get_default_services_config()

        assert isinstance(config, dict)
        assert "redis" in config
        assert "postgres" in config
        assert "temporal" in config

    def test_services_config_structure(self) -> None:
        """Test services configuration structure."""
        config = get_default_services_config()

        # Redis
        assert config["redis"]["port"] == 6379
        assert config["redis"]["enabled"] is True

        # PostgreSQL
        assert config["postgres"]["port"] == 5432
        assert config["postgres"]["database"] == "mycelium"

        # Temporal
        assert config["temporal"]["ui_port"] == 8080
        assert config["temporal"]["namespace"] == "default"


class TestDeploymentDefaults:
    """Test deployment default configuration."""

    def test_get_default_deployment_config(self) -> None:
        """Test getting default deployment configuration."""
        config = get_default_deployment_config()

        assert isinstance(config, dict)
        assert config["method"] == "docker-compose"
        assert config["auto_start"] is True
        assert config["healthcheck_timeout"] == 60

    def test_deployment_config_keys(self) -> None:
        """Test that all required keys are present."""
        config = get_default_deployment_config()
        required_keys = {"method", "auto_start", "healthcheck_timeout"}
        assert set(config.keys()) == required_keys


class TestCompleteDefaults:
    """Test complete default configuration."""

    def test_get_default_config_dict(self) -> None:
        """Test getting complete default configuration."""
        config = get_default_config_dict()

        assert isinstance(config, dict)
        assert "version" in config
        assert "project_name" in config
        assert "deployment" in config
        assert "services" in config
        assert "created_at" in config

    def test_config_dict_structure(self) -> None:
        """Test complete configuration structure."""
        config = get_default_config_dict()

        # Top level
        assert config["version"] == "1.0"
        assert config["project_name"] == "mycelium"

        # Deployment
        assert config["deployment"]["method"] == "docker-compose"
        assert config["deployment"]["auto_start"] is True

        # Services
        assert "redis" in config["services"]
        assert "postgres" in config["services"]
        assert "temporal" in config["services"]

        # Service details
        assert config["services"]["redis"]["port"] == 6379
        assert config["services"]["postgres"]["database"] == "mycelium"
        assert config["services"]["temporal"]["namespace"] == "default"

    def test_created_at_is_iso_format(self) -> None:
        """Test that created_at is in ISO format."""
        config = get_default_config_dict()
        created_at = config["created_at"]

        assert isinstance(created_at, str)
        # Should be parseable as ISO datetime
        from datetime import datetime

        datetime.fromisoformat(created_at)

    def test_default_config_is_valid(self) -> None:
        """Test that default config can be loaded into MyceliumConfig."""
        from mycelium_onboarding.config.schema import MyceliumConfig

        config_dict = get_default_config_dict()
        config = MyceliumConfig.from_dict(config_dict)

        assert config.version == "1.0"
        assert config.project_name == "mycelium"
        assert config.services.redis.port == 6379
        assert config.deployment.auto_start is True


class TestDefaultsIndependence:
    """Test that default getters return independent copies."""

    def test_redis_config_independence(self) -> None:
        """Test that each call returns a new dict."""
        config1 = get_default_redis_config()
        config2 = get_default_redis_config()

        # Modify first config
        config1["port"] = 9999

        # Second config should be unchanged
        assert config2["port"] == 6379

    def test_services_config_independence(self) -> None:
        """Test that nested configs are independent."""
        config1 = get_default_services_config()
        config2 = get_default_services_config()

        # Modify first config
        config1["redis"]["port"] = 9999

        # Second config should be unchanged
        assert config2["redis"]["port"] == 6379

    def test_complete_config_independence(self) -> None:
        """Test that complete configs are independent."""
        config1 = get_default_config_dict()
        config2 = get_default_config_dict()

        # Modify first config
        config1["services"]["redis"]["port"] = 9999

        # Second config should be unchanged
        assert config2["services"]["redis"]["port"] == 6379
