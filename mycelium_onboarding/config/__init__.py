"""Configuration system for Mycelium onboarding.

This package provides a type-safe configuration system using Pydantic v2.
It includes schema definitions, validation, serialization/deserialization,
and configuration management utilities.

Main Components:
    - schema: Pydantic models for configuration validation
    - defaults: Default configuration values (Sprint 2, Task A1)
    - loader: 3-tier configuration loading (Sprint 2, Task A2)
    - precedence: Deep merge logic (Sprint 2, Task A2)
    - manager: Configuration loading, saving, and management (Task 2.2)
    - migrations: Schema migration framework (Task 2.3)
    - paths: XDG-compliant path resolution (Sprint 2, Task B1)
    - path_utils: Safe file operations for migration (Sprint 2, Task B2)
    - platform: Platform detection and utilities

Example:
    >>> from mycelium_onboarding.config import ConfigLoader, MyceliumConfig
    >>> # Load configuration with 3-tier precedence (Sprint 2)
    >>> loader = ConfigLoader()
    >>> config = loader.load()
    >>> print(config.project_name)
    mycelium
    >>>
    >>> # Create and save configuration
    >>> config = MyceliumConfig(project_name="my-project")
    >>> config.services.redis.port = 6380
    >>> from mycelium_onboarding.config import ConfigManager
    >>> manager = ConfigManager()
    >>> manager.save(config)
    >>> # Load configuration
    >>> loaded_config = manager.load()
    >>> # Migrate configuration
    >>> migrated = manager.load_and_migrate()
    >>> # Use XDG-compliant paths
    >>> from mycelium_onboarding.config import get_global_config_path
    >>> global_config_path = get_global_config_path()
"""

from __future__ import annotations

from mycelium_onboarding.config.defaults import (
    DEFAULT_DEPLOYMENT_METHOD,
    DEFAULT_HEALTHCHECK_TIMEOUT,
    DEFAULT_POSTGRES_DATABASE,
    DEFAULT_POSTGRES_PORT,
    DEFAULT_PROJECT_NAME,
    DEFAULT_REDIS_PORT,
    DEFAULT_SCHEMA_VERSION,
    DEFAULT_TEMPORAL_FRONTEND_PORT,
    DEFAULT_TEMPORAL_UI_PORT,
    get_default_config_dict,
    get_default_deployment_config,
    get_default_postgres_config,
    get_default_redis_config,
    get_default_services_config,
    get_default_temporal_config,
)
from mycelium_onboarding.config.loader import (
    ConfigLoader,
    ConfigParseError,
)
from mycelium_onboarding.config.loader import (
    ConfigLoadError as LoaderConfigLoadError,
)
from mycelium_onboarding.config.loader import (
    ConfigValidationError as LoaderConfigValidationError,
)
from mycelium_onboarding.config.manager import (
    ConfigLoadError,
    ConfigManager,
    ConfigSaveError,
    ConfigValidationError,
)
from mycelium_onboarding.config.migrations import (
    Migration,
    MigrationError,
    MigrationHistory,
    MigrationPathError,
    MigrationRegistry,
    MigrationValidationError,
    get_default_registry,
)
from mycelium_onboarding.config.path_utils import (
    AtomicMoveError,
    PathMigrationError,
    SymlinkError,
    YAMLError,
    atomic_move,
    check_write_permission,
    create_backup,
    find_legacy_configs,
    is_symlink_safe,
    safe_read_yaml,
    safe_write_yaml,
)
from mycelium_onboarding.config.paths import (
    ensure_cache_dir_exists,
    ensure_config_dir_exists,
    ensure_data_dir_exists,
    ensure_dir_exists,
    ensure_log_dir_exists,
    ensure_migration_backup_dir_exists,
    ensure_state_dir_exists,
    get_cache_dir,
    get_data_dir,
    get_global_config_path,
    get_log_dir,
    get_migration_backup_dir,
    get_project_config_path,
    get_state_dir,
)
from mycelium_onboarding.config.platform import (
    Platform,
    get_home_directory,
    get_path_separator,
    get_platform,
    is_posix,
    is_windows,
    normalize_path,
)
from mycelium_onboarding.config.precedence import (
    MergeStrategy,
    deep_merge,
    deep_merge_configs,
    merge_with_precedence,
)
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

__all__ = [
    # Schema classes
    "MyceliumConfig",
    "DeploymentConfig",
    "DeploymentMethod",
    "ServicesConfig",
    "ServiceConfig",
    "RedisConfig",
    "PostgresConfig",
    "TemporalConfig",
    # Defaults (Sprint 2, Task A1)
    "DEFAULT_PROJECT_NAME",
    "DEFAULT_SCHEMA_VERSION",
    "DEFAULT_REDIS_PORT",
    "DEFAULT_POSTGRES_PORT",
    "DEFAULT_POSTGRES_DATABASE",
    "DEFAULT_TEMPORAL_UI_PORT",
    "DEFAULT_TEMPORAL_FRONTEND_PORT",
    "DEFAULT_DEPLOYMENT_METHOD",
    "DEFAULT_HEALTHCHECK_TIMEOUT",
    "get_default_config_dict",
    "get_default_redis_config",
    "get_default_postgres_config",
    "get_default_temporal_config",
    "get_default_services_config",
    "get_default_deployment_config",
    # Loader classes (Sprint 2, Task A2)
    "ConfigLoader",
    "LoaderConfigLoadError",
    "ConfigParseError",
    "LoaderConfigValidationError",
    # Precedence utilities (Sprint 2, Task A2)
    "deep_merge",
    "deep_merge_configs",
    "merge_with_precedence",
    "MergeStrategy",
    # Manager classes
    "ConfigManager",
    "ConfigLoadError",
    "ConfigSaveError",
    "ConfigValidationError",
    # Migration classes
    "Migration",
    "MigrationRegistry",
    "MigrationHistory",
    "MigrationError",
    "MigrationPathError",
    "MigrationValidationError",
    "get_default_registry",
    # Platform detection (Sprint 2, Task B1)
    "Platform",
    "get_platform",
    "is_windows",
    "is_posix",
    "get_path_separator",
    "normalize_path",
    "get_home_directory",
    # Path resolution (Sprint 2, Task B1)
    "get_global_config_path",
    "get_project_config_path",
    "get_data_dir",
    "get_state_dir",
    "get_cache_dir",
    "get_log_dir",
    "get_migration_backup_dir",
    "ensure_dir_exists",
    "ensure_config_dir_exists",
    "ensure_data_dir_exists",
    "ensure_state_dir_exists",
    "ensure_cache_dir_exists",
    "ensure_log_dir_exists",
    "ensure_migration_backup_dir_exists",
    # Path utilities (Sprint 2, Task B2)
    "find_legacy_configs",
    "atomic_move",
    "check_write_permission",
    "is_symlink_safe",
    "create_backup",
    "safe_read_yaml",
    "safe_write_yaml",
    "PathMigrationError",
    "SymlinkError",
    "AtomicMoveError",
    "YAMLError",
]
