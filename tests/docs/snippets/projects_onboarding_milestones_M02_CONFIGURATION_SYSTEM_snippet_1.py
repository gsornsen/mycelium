# Source: projects/onboarding/milestones/M02_CONFIGURATION_SYSTEM.md
# Line: 95
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/config/schema.py
"""Configuration schema using Pydantic v2."""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from pathlib import Path
from enum import Enum


class DeploymentMethod(str, Enum):
    """Supported deployment methods."""
    DOCKER_COMPOSE = "docker-compose"
    JUSTFILE = "justfile"


class ServiceConfig(BaseModel):
    """Configuration for a single service."""
    enabled: bool = True
    version: Optional[str] = None
    custom_config: dict[str, str] = Field(default_factory=dict)


class RedisConfig(ServiceConfig):
    """Redis-specific configuration."""
    port: int = Field(default=6379, ge=1, le=65535)
    persistence: bool = True
    max_memory: str = "256mb"


class PostgresConfig(ServiceConfig):
    """PostgreSQL-specific configuration."""
    port: int = Field(default=5432, ge=1, le=65535)
    database: str = "mycelium"
    max_connections: int = 100


class TemporalConfig(ServiceConfig):
    """Temporal-specific configuration."""
    ui_port: int = Field(default=8080, ge=1, le=65535)
    frontend_port: int = Field(default=7233, ge=1, le=65535)
    namespace: str = "default"


class ServicesConfig(BaseModel):
    """All service configurations."""
    redis: RedisConfig = Field(default_factory=RedisConfig)
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    temporal: TemporalConfig = Field(default_factory=TemporalConfig)


class DeploymentConfig(BaseModel):
    """Deployment configuration."""
    method: DeploymentMethod = DeploymentMethod.DOCKER_COMPOSE
    auto_start: bool = True
    healthcheck_timeout: int = Field(default=60, ge=10, le=300)


class MyceliumConfig(BaseModel):
    """Top-level Mycelium configuration."""
    version: Literal["1.0"] = "1.0"  # Schema version
    deployment: DeploymentConfig = Field(default_factory=DeploymentConfig)
    services: ServicesConfig = Field(default_factory=ServicesConfig)
    project_name: str = "mycelium"

    @field_validator("project_name")
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        """Validate project name is alphanumeric with hyphens/underscores."""
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Project name must contain only alphanumeric characters, "
                "hyphens, and underscores"
            )
        return v

    def model_post_init(self, __context) -> None:
        """Post-initialization hook for custom validation."""
        # Ensure at least one service is enabled
        if not any([
            self.services.redis.enabled,
            self.services.postgres.enabled,
            self.services.temporal.enabled,
        ]):
            raise ValueError("At least one service must be enabled")