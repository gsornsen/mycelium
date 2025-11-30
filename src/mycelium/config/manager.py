"""Configuration management for Mycelium.

Implements .env hierarchy loading following node/vite patterns:
1. .env.defaults - Safe defaults (committed to repo)
2. .env - Local overrides (gitignored)
3. .env.local - Local overrides (gitignored)
4. .env.[mode] - Mode-specific (development, production)
5. .env.[mode].local - Mode-specific local (gitignored)
6. Environment variables - Override all
"""

import os
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

from dotenv import dotenv_values


@dataclass
class MyceliumConfig:
    """Mycelium configuration with type-safe defaults.

    Attributes:
        redis_url: Redis connection URL for agent registry
        dev_server_port: Development server port
        api_port: API server port
        agent_port_start: Starting port for agent processes
        plugin_dir: Directory containing agent plugins
        log_dir: Directory for log files
        auto_discover: Auto-discover agents on startup
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """

    # Registry
    redis_url: str = "redis://localhost:6379"

    # Ports
    dev_server_port: int = 15850
    api_port: int = 15900
    agent_port_start: int = 17000

    # Paths
    plugin_dir: Path = field(
        default_factory=lambda: Path.home() / "git" / "mycelium" / "plugins" / "mycelium-core" / "agents"
    )
    log_dir: Path = field(default_factory=lambda: Path.home() / ".local" / "share" / "mycelium" / "logs")

    # Behavior
    auto_discover: bool = True
    log_level: str = "INFO"

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of config with Path objects as strings.
        """
        result = {}
        for key, value in asdict(self).items():
            if isinstance(value, Path):
                result[key] = str(value)
            else:
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MyceliumConfig":
        """Create configuration from dictionary.

        Args:
            data: Dictionary with configuration values.

        Returns:
            MyceliumConfig instance.
        """
        # Start with defaults
        defaults = cls()
        converted: dict[str, Any] = {}

        # Get field types
        field_types = {f.name: f.type for f in fields(cls)}

        for key, value in data.items():
            if key in field_types:
                field_type = field_types[key]
                if field_type == Path and isinstance(value, str):
                    # Expand ~ in paths
                    converted[key] = Path(value).expanduser()
                elif field_type is int and isinstance(value, str):
                    converted[key] = int(value)
                elif field_type is bool and isinstance(value, str):
                    converted[key] = value.lower() in ("true", "1", "yes", "on")
                else:
                    converted[key] = value

        # Merge with defaults
        default_dict = asdict(defaults)
        default_dict.update(converted)

        return cls(**default_dict)


class ConfigManager:
    """Configuration manager with .env hierarchy support.

    Loads configuration from multiple sources in order of precedence:
    1. .env.defaults (lowest priority)
    2. .env
    3. .env.local
    4. .env.[mode]
    5. .env.[mode].local
    6. Environment variables (highest priority)
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize configuration manager.

        Args:
            config_dir: Directory containing .env files. Defaults to cwd.
        """
        self.config_dir = config_dir or Path.cwd()
        self._config: MyceliumConfig | None = None

    def load(self, mode: str = "development") -> MyceliumConfig:
        """Load configuration from .env files and environment.

        Args:
            mode: Configuration mode (development, production, test).

        Returns:
            Loaded MyceliumConfig instance.
        """
        # Start with empty config dict
        config_dict: dict[str, Any] = {}

        # Load files in order (later overrides earlier)
        env_files = [
            self.config_dir / ".env.defaults",
            self.config_dir / ".env",
            self.config_dir / ".env.local",
            self.config_dir / f".env.{mode}",
            self.config_dir / f".env.{mode}.local",
        ]

        # Merge all .env files
        for env_file in env_files:
            if env_file.exists():
                file_values = dotenv_values(env_file)
                # Convert keys to lowercase and remove MYCELIUM_ prefix
                for key, value in file_values.items():
                    if value is not None:  # Skip None values
                        clean_key = key.lower()
                        if clean_key.startswith("mycelium_"):
                            clean_key = clean_key[9:]  # Remove "mycelium_" prefix
                        config_dict[clean_key] = value

        # Override with environment variables (highest priority)
        for key in [
            "REDIS_URL",
            "DEV_SERVER_PORT",
            "API_PORT",
            "AGENT_PORT_START",
            "PLUGIN_DIR",
            "LOG_DIR",
            "AUTO_DISCOVER",
            "LOG_LEVEL",
        ]:
            # Check both with and without MYCELIUM_ prefix
            env_value = os.getenv(f"MYCELIUM_{key}") or os.getenv(key)
            if env_value:
                config_dict[key.lower()] = env_value

        # Create config instance with merged values
        self._config = MyceliumConfig.from_dict(config_dict)
        return self._config

    def validate(self) -> list[str]:
        """Validate current configuration.

        Returns:
            List of validation error messages. Empty list if valid.
        """
        errors: list[str] = []

        if self._config is None:
            errors.append("Configuration not loaded. Call load() first.")
            return errors

        # Validate redis_url format
        if not self._config.redis_url.startswith(("redis://", "rediss://")):
            errors.append(f"Invalid redis_url format: {self._config.redis_url}")

        # Validate ports are in valid range
        for port_name in ["dev_server_port", "api_port", "agent_port_start"]:
            port_value = getattr(self._config, port_name)
            if not (1024 <= port_value <= 65535):
                errors.append(f"Invalid {port_name}: {port_value} (must be 1024-65535)")

        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self._config.log_level.upper() not in valid_levels:
            errors.append(f"Invalid log_level: {self._config.log_level} (must be one of {valid_levels})")

        # Validate paths exist or can be created
        for path_name in ["plugin_dir", "log_dir"]:
            path_value = getattr(self._config, path_name)
            if not isinstance(path_value, Path):
                errors.append(f"Invalid {path_name}: {path_value} (must be a Path)")
                continue

            # Check if parent directory exists for creation
            if not path_value.exists():
                parent = path_value.parent
                if not parent.exists():
                    errors.append(f"Parent directory does not exist for {path_name}: {parent}")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of current config.

        Raises:
            RuntimeError: If configuration not loaded.
        """
        if self._config is None:
            msg = "Configuration not loaded. Call load() first."
            raise RuntimeError(msg)
        return self._config.to_dict()

    def reload(self, mode: str = "development") -> MyceliumConfig:
        """Reload configuration from files.

        Args:
            mode: Configuration mode.

        Returns:
            Reloaded MyceliumConfig instance.
        """
        self._config = None
        return self.load(mode=mode)

    def get(self) -> MyceliumConfig:
        """Get current configuration.

        Returns:
            Current MyceliumConfig instance.

        Raises:
            RuntimeError: If configuration not loaded.
        """
        if self._config is None:
            msg = "Configuration not loaded. Call load() first."
            raise RuntimeError(msg)
        return self._config


# Global config instance
_global_config: ConfigManager | None = None


def get_config(reload: bool = False, mode: str = "development") -> MyceliumConfig:
    """Get global configuration instance.

    Args:
        reload: Force reload of configuration.
        mode: Configuration mode.

    Returns:
        MyceliumConfig instance.
    """
    global _global_config

    if _global_config is None or reload:
        _global_config = ConfigManager()
        _global_config.load(mode=mode)

    return _global_config.get()
