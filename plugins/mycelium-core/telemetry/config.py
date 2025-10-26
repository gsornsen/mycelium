"""Telemetry configuration management.

Handles loading and validating telemetry configuration from environment variables.
Telemetry is DISABLED BY DEFAULT - explicit opt-in required.
"""

import os
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


class TelemetryConfig(BaseModel):
    """Configuration for telemetry system.

    Attributes:
        enabled: Whether telemetry is enabled (default: False)
        endpoint: Telemetry collection endpoint URL
        timeout: Request timeout in seconds
        batch_size: Number of events to batch before sending
        retry_attempts: Number of retry attempts on failure
        retry_backoff: Exponential backoff multiplier for retries
        salt: Salt for hashing identifiers (generated if not provided)
    """

    enabled: bool = Field(
        default=False, description="Enable telemetry collection (default: disabled)"
    )
    endpoint: HttpUrl = Field(
        default=HttpUrl("https://mycelium-telemetry.sornsen.io"),
        description="Telemetry collection endpoint",
    )
    timeout: int = Field(
        default=5, ge=1, le=30, description="Request timeout in seconds"
    )
    batch_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Number of events to batch before sending",
    )
    retry_attempts: int = Field(
        default=3, ge=0, le=10, description="Number of retry attempts on failure"
    )
    retry_backoff: float = Field(
        default=2.0,
        ge=1.0,
        le=10.0,
        description="Exponential backoff multiplier for retries",
    )
    salt: str = Field(
        default_factory=lambda: os.urandom(32).hex(),
        description="Salt for hashing identifiers",
    )

    @field_validator("endpoint", mode="before")
    @classmethod
    def validate_endpoint(cls, v: str) -> str:
        """Validate and normalize endpoint URL."""
        if isinstance(v, str) and not v.startswith(("http://", "https://")):
            # Ensure URL has scheme
            v = f"https://{v}"
        return v

    @classmethod
    def from_env(cls) -> "TelemetryConfig":
        """Load configuration from environment variables.

        Environment variables:
            TELEMETRY_ENABLED: Enable telemetry (true/false)
            TELEMETRY_ENDPOINT: Collection endpoint URL
            TELEMETRY_TIMEOUT: Request timeout in seconds
            TELEMETRY_BATCH_SIZE: Batch size for events
            TELEMETRY_RETRY_ATTEMPTS: Number of retry attempts
            TELEMETRY_RETRY_BACKOFF: Retry backoff multiplier
            TELEMETRY_SALT: Salt for hashing (auto-generated if not set)

        Returns:
            TelemetryConfig instance with values from environment
        """
        enabled = os.getenv("TELEMETRY_ENABLED", "false").lower() in (
            "true",
            "1",
            "yes",
            "on",
        )

        config_data: dict[str, Any] = {
            "enabled": enabled,
        }

        # Only load other settings if telemetry is enabled
        if enabled:
            if endpoint := os.getenv("TELEMETRY_ENDPOINT"):
                config_data["endpoint"] = endpoint

            if timeout := os.getenv("TELEMETRY_TIMEOUT"):
                config_data["timeout"] = int(timeout)

            if batch_size := os.getenv("TELEMETRY_BATCH_SIZE"):
                config_data["batch_size"] = int(batch_size)

            if retry_attempts := os.getenv("TELEMETRY_RETRY_ATTEMPTS"):
                config_data["retry_attempts"] = int(retry_attempts)

            if retry_backoff := os.getenv("TELEMETRY_RETRY_BACKOFF"):
                config_data["retry_backoff"] = float(retry_backoff)

            if salt := os.getenv("TELEMETRY_SALT"):
                config_data["salt"] = salt

        return cls(**config_data)

    def is_enabled(self) -> bool:
        """Check if telemetry is enabled.

        Returns:
            True if telemetry is enabled, False otherwise
        """
        return self.enabled
