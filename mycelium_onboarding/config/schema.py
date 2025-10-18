"""Configuration schema using Pydantic v2.

This module defines the complete type-safe configuration schema for the Mycelium
onboarding system. All configuration is validated using Pydantic v2 models with
comprehensive field validators and clear error messages.

The schema supports:
- Multiple service configurations (Redis, PostgreSQL, Temporal)
- Deployment method configuration (Docker Compose, Kubernetes, systemd, manual)
- Schema versioning for migrations
- Serialization to/from YAML and JSON
- Comprehensive validation with helpful error messages

Example:
    >>> from mycelium_onboarding.config.schema import MyceliumConfig
    >>> config = MyceliumConfig(project_name="my-project")
    >>> config.services.redis.port = 6380
    >>> config_dict = config.model_dump()
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Module exports
__all__ = [
    "DeploymentMethod",
    "ServiceConfig",
    "RedisConfig",
    "PostgresConfig",
    "TemporalConfig",
    "ServicesConfig",
    "DeploymentConfig",
    "MyceliumConfig",
]


class DeploymentMethod(str, Enum):
    """Supported deployment methods.

    Attributes:
        DOCKER_COMPOSE: Deploy using Docker Compose
        KUBERNETES: Deploy to Kubernetes cluster
        SYSTEMD: Deploy as systemd services
        MANUAL: Manual deployment (user-managed)
    """

    DOCKER_COMPOSE = "docker-compose"
    KUBERNETES = "kubernetes"
    SYSTEMD = "systemd"
    MANUAL = "manual"


class ServiceConfig(BaseModel):
    """Base configuration for a service.

    Attributes:
        enabled: Whether the service is enabled
        version: Optional specific version to use (e.g., "7.0", "15")
        custom_config: Additional service-specific configuration options
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    enabled: bool = Field(
        default=True,
        description="Whether this service is enabled",
    )
    version: str | None = Field(
        default=None,
        description="Specific version to use (e.g., '7.0', 'latest')",
    )
    custom_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional service-specific configuration",
    )

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str | None) -> str | None:
        """Validate version string format.

        Args:
            v: Version string to validate

        Returns:
            Validated version string

        Raises:
            ValueError: If version contains invalid characters
        """
        if v is None:
            return v

        # Allow alphanumeric, dots, hyphens (e.g., "7.0", "15", "latest", "7.0-alpine")
        if not re.match(r"^[a-zA-Z0-9._-]+$", v):
            raise ValueError(
                f"Version must contain only alphanumeric characters, dots, "
                f"hyphens, and underscores. Got: {v}"
            )
        return v


class RedisConfig(ServiceConfig):
    """Redis-specific configuration.

    Attributes:
        port: Redis port number (1-65535)
        persistence: Enable RDB persistence
        max_memory: Maximum memory limit (e.g., "256mb", "1gb")
    """

    port: int = Field(
        default=6379,
        ge=1,
        le=65535,
        description="Redis port number",
    )
    persistence: bool = Field(
        default=True,
        description="Enable RDB snapshots for persistence",
    )
    max_memory: str = Field(
        default="256mb",
        description="Maximum memory limit (e.g., '256mb', '1gb')",
    )

    @field_validator("max_memory")
    @classmethod
    def validate_max_memory(cls, v: str) -> str:
        """Validate memory size format.

        Args:
            v: Memory size string to validate

        Returns:
            Validated memory size string

        Raises:
            ValueError: If memory format is invalid
        """
        # Allow formats like "256mb", "1gb", "512MB", "2GB"
        if not re.match(r"^\d+[kmgtKMGT][bB]$", v):
            raise ValueError(
                f"Memory must be in format '<number><unit>' where unit is "
                f"kb, mb, gb, or tb (case-insensitive). Got: {v}"
            )
        return v.lower()  # Normalize to lowercase


class PostgresConfig(ServiceConfig):
    """PostgreSQL-specific configuration.

    Attributes:
        port: PostgreSQL port number (1-65535)
        database: Default database name
        max_connections: Maximum number of connections
    """

    port: int = Field(
        default=5432,
        ge=1,
        le=65535,
        description="PostgreSQL port number",
    )
    database: str = Field(
        default="mycelium",
        min_length=1,
        max_length=63,
        description="Default database name",
    )
    max_connections: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum number of concurrent connections",
    )

    @field_validator("database")
    @classmethod
    def validate_database(cls, v: str) -> str:
        """Validate database name format.

        Args:
            v: Database name to validate

        Returns:
            Validated database name

        Raises:
            ValueError: If database name is invalid
        """
        # PostgreSQL database names: alphanumeric, underscores, must start with letter
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", v):
            raise ValueError(
                f"Database name must start with a letter and contain only "
                f"alphanumeric characters and underscores. Got: {v}"
            )
        return v


class TemporalConfig(ServiceConfig):
    """Temporal-specific configuration.

    Attributes:
        ui_port: Temporal UI port number (1-65535)
        frontend_port: Temporal frontend/gRPC port number (1-65535)
        namespace: Default namespace for workflows
    """

    ui_port: int = Field(
        default=8080,
        ge=1,
        le=65535,
        description="Temporal Web UI port",
    )
    frontend_port: int = Field(
        default=7233,
        ge=1,
        le=65535,
        description="Temporal frontend/gRPC port",
    )
    namespace: str = Field(
        default="default",
        min_length=1,
        max_length=255,
        description="Default namespace for workflows",
    )

    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, v: str) -> str:
        """Validate namespace format.

        Args:
            v: Namespace to validate

        Returns:
            Validated namespace

        Raises:
            ValueError: If namespace is invalid
        """
        # Namespace: alphanumeric, hyphens, underscores
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                f"Namespace must contain only alphanumeric characters, "
                f"hyphens, and underscores. Got: {v}"
            )
        return v


class ServicesConfig(BaseModel):
    """Configuration for all services.

    Attributes:
        redis: Redis configuration
        postgres: PostgreSQL configuration
        temporal: Temporal configuration
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    redis: RedisConfig = Field(
        default_factory=RedisConfig,
        description="Redis configuration",
    )
    postgres: PostgresConfig = Field(
        default_factory=PostgresConfig,
        description="PostgreSQL configuration",
    )
    temporal: TemporalConfig = Field(
        default_factory=TemporalConfig,
        description="Temporal configuration",
    )


class DeploymentConfig(BaseModel):
    """Deployment configuration.

    Attributes:
        method: Deployment method to use
        auto_start: Automatically start services on deployment
        healthcheck_timeout: Timeout in seconds for service health checks
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    method: DeploymentMethod = Field(
        default=DeploymentMethod.DOCKER_COMPOSE,
        description="Deployment method to use",
    )
    auto_start: bool = Field(
        default=True,
        description="Automatically start services on deployment",
    )
    healthcheck_timeout: int = Field(
        default=60,
        ge=10,
        le=300,
        description="Timeout in seconds for service health checks",
    )


class MyceliumConfig(BaseModel):
    """Top-level Mycelium configuration.

    This is the root configuration model that contains all configuration
    options for the Mycelium onboarding system.

    Attributes:
        version: Configuration schema version for migrations
        project_name: Project identifier (alphanumeric, hyphens, underscores)
        deployment: Deployment configuration
        services: Service configurations
        created_at: Timestamp when config was created (auto-populated)

    Example:
        >>> config = MyceliumConfig(project_name="my-project")
        >>> config.services.redis.port = 6380
        >>> config.deployment.method = DeploymentMethod.KUBERNETES
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    version: str = Field(
        default="1.0",
        description="Configuration schema version",
        pattern=r"^\d+\.\d+$",
    )
    project_name: str = Field(
        default="mycelium",
        min_length=1,
        max_length=100,
        description="Project identifier",
    )
    deployment: DeploymentConfig = Field(
        default_factory=DeploymentConfig,
        description="Deployment configuration",
    )
    services: ServicesConfig = Field(
        default_factory=ServicesConfig,
        description="Service configurations",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when configuration was created",
    )

    @field_validator("project_name")
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        """Validate project name format.

        Args:
            v: Project name to validate

        Returns:
            Validated project name

        Raises:
            ValueError: If project name contains invalid characters
        """
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                f"Project name must contain only alphanumeric characters, "
                f"hyphens, and underscores. Got: {v}"
            )
        return v

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization validation hook.

        Validates that at least one service is enabled.

        Raises:
            ValueError: If all services are disabled
        """
        if not any(
            [
                self.services.redis.enabled,
                self.services.postgres.enabled,
                self.services.temporal.enabled,
            ]
        ):
            raise ValueError(
                "At least one service must be enabled. "
                "Enable redis, postgres, or temporal."
            )

    def to_dict(self, *, exclude_none: bool = False) -> dict[str, Any]:
        """Serialize configuration to dictionary.

        Args:
            exclude_none: Exclude fields with None values

        Returns:
            Dictionary representation of configuration

        Example:
            >>> config = MyceliumConfig()
            >>> config_dict = config.to_dict()
        """
        return self.model_dump(
            mode="json",
            exclude_none=exclude_none,
        )

    def to_yaml(self, *, exclude_none: bool = False) -> str:
        """Serialize configuration to YAML string.

        Args:
            exclude_none: Exclude fields with None values

        Returns:
            YAML string representation

        Example:
            >>> config = MyceliumConfig()
            >>> yaml_str = config.to_yaml()
        """
        config_dict = self.to_dict(exclude_none=exclude_none)
        return str(
            yaml.dump(
                config_dict,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MyceliumConfig:
        """Deserialize configuration from dictionary.

        Args:
            data: Dictionary containing configuration data

        Returns:
            MyceliumConfig instance

        Raises:
            ValidationError: If data is invalid

        Example:
            >>> data = {"project_name": "my-project"}
            >>> config = MyceliumConfig.from_dict(data)
        """
        return cls.model_validate(data)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> MyceliumConfig:
        """Deserialize configuration from YAML string.

        Args:
            yaml_str: YAML string containing configuration

        Returns:
            MyceliumConfig instance

        Raises:
            ValidationError: If YAML is invalid
            yaml.YAMLError: If YAML parsing fails

        Example:
            >>> yaml_str = "project_name: my-project"
            >>> config = MyceliumConfig.from_yaml(yaml_str)
        """
        data = yaml.safe_load(yaml_str)
        if data is None:
            data = {}
        return cls.from_dict(data)
