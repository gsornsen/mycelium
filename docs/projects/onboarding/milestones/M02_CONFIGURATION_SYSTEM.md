# M02: Configuration System

## Overview

**Duration**: 2 days **Dependencies**: M01 (Environment Isolation) **Blocks**: M04 (Interactive Onboarding), M05
(Deployment Generation) **Lead Agent**: python-pro **Support Agents**: platform-engineer

## Why This Milestone

The configuration system is the central nervous system of the onboarding process. It must:

- Provide type-safe validation to catch errors early
- Support schema evolution as features are added
- Enable hierarchical configuration (project → user → defaults)
- Serialize cleanly to YAML for human readability
- Support programmatic access and validation

Without a robust configuration system, the onboarding wizard would have nowhere to persist user choices, and deployment
generation would lack necessary parameters.

## Requirements

### Functional Requirements (FR)

**FR-1**: Type-safe configuration schema

- All configuration values must have defined types
- Invalid values must be caught at load time, not runtime
- Support for optional fields with sensible defaults

**FR-2**: Human-readable configuration format

- Primary format: YAML (human-editable)
- Secondary format: JSON (machine-readable)
- Clear structure with comments and examples

**FR-3**: Schema migration support

- Detect configuration schema version
- Automatically migrate old schemas to current
- Preserve user customizations during migration
- Log migration actions for transparency

### Technical Requirements (TR)

**TR-1**: Use Pydantic v2 for validation

- BaseModel for all configuration schemas
- Field validators for complex constraints
- Serialization/deserialization built-in

**TR-2**: Support for hierarchical loading

- Load from project-local, user-global, or defaults
- Merge configurations with correct precedence
- Allow overrides at each level

**TR-3**: Validation on load and save

- Validate immediately on load, fail fast
- Validate before save, prevent corruption
- Provide detailed error messages with field paths

### Integration Requirements (IR)

**IR-1**: Integration with M01 environment isolation

- Use XDG config directory for storage
- Respect MYCELIUM_PROJECT_DIR for project-local config
- Follow hierarchical loading from config_loader.py

**IR-2**: Integration with M04 interactive onboarding

- Wizard saves to configuration schema
- Configuration drives wizard defaults on re-run
- Support partial configurations (incomplete wizard runs)

### Constraints (CR)

**CR-1**: Configuration must be version-controlled friendly

- YAML format with consistent ordering
- No generated timestamps or UUIDs in default config
- Deterministic serialization

**CR-2**: No secrets in configuration files

- Passwords, tokens, API keys stored separately
- Configuration references secret locations, not values
- Clear documentation on secret management

## Tasks

### Task 2.1: Design Configuration Schema

**Agent**: python-pro **Effort**: 6 hours **Dependencies**: M01 complete

**Description**: Design complete configuration schema covering all onboarding options.

**Schema Design**:

```python
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
```

**Acceptance Criteria**:

- [ ] Complete schema covers all configuration options
- [ ] All fields have appropriate types and constraints
- [ ] Validators ensure data integrity (port ranges, name format)
- [ ] Sensible defaults for all optional fields
- [ ] Schema version field for migration support
- [ ] Documented with docstrings and examples

**Deliverables**:

- `mycelium_onboarding/config/schema.py`
- Design document with field descriptions

______________________________________________________________________

### Task 2.2: Configuration Loading & Saving

**Agent**: python-pro **Effort**: 6 hours **Dependencies**: Task 2.1

**Description**: Implement configuration loading/saving with validation and error handling.

**Implementation**:

```python
# mycelium_onboarding/config/manager.py
"""Configuration manager for loading/saving configurations."""

from pathlib import Path
from typing import Optional
import yaml
from pydantic import ValidationError

from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.config_loader import get_config_path, find_config_file


class ConfigurationError(Exception):
    """Base exception for configuration errors."""
    pass


class ConfigValidationError(ConfigurationError):
    """Configuration validation failed."""
    pass


class ConfigManager:
    """Manages configuration loading, saving, and validation."""

    CONFIG_FILENAME = "config.yaml"

    @classmethod
    def load(cls, prefer_project: bool = True) -> MyceliumConfig:
        """Load configuration from file or return defaults.

        Args:
            prefer_project: Prefer project-local over user-global config

        Returns:
            MyceliumConfig instance

        Raises:
            ConfigValidationError: If configuration is invalid
        """
        config_file = find_config_file(cls.CONFIG_FILENAME)

        if config_file is None:
            # No config file found, return defaults
            return MyceliumConfig()

        return cls.load_from_path(config_file)

    @classmethod
    def load_from_path(cls, path: Path) -> MyceliumConfig:
        """Load configuration from specific path.

        Args:
            path: Path to configuration file

        Returns:
            MyceliumConfig instance

        Raises:
            ConfigValidationError: If configuration is invalid
            FileNotFoundError: If path doesn't exist
        """
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path) as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ConfigValidationError(
                    f"Invalid YAML in {path}: {e}"
                ) from e

        if data is None:
            # Empty file, return defaults
            return MyceliumConfig()

        try:
            return MyceliumConfig.model_validate(data)
        except ValidationError as e:
            raise ConfigValidationError(
                f"Configuration validation failed in {path}:\n{e}"
            ) from e

    @classmethod
    def save(
        cls,
        config: MyceliumConfig,
        project_local: bool = False,
        create_dirs: bool = True,
    ) -> Path:
        """Save configuration to file.

        Args:
            config: Configuration to save
            project_local: Save to project-local (.mycelium/) if True,
                          user-global (~/.config/mycelium/) if False
            create_dirs: Create parent directories if they don't exist

        Returns:
            Path where configuration was saved

        Raises:
            ConfigValidationError: If configuration is invalid before save
        """
        # Validate before saving
        try:
            config.model_validate(config.model_dump())
        except ValidationError as e:
            raise ConfigValidationError(
                f"Configuration invalid, not saving:\n{e}"
            ) from e

        # Determine save path
        config_path = get_config_path(
            cls.CONFIG_FILENAME,
            prefer_project=project_local
        )

        # Create parent directories if needed
        if create_dirs:
            config_path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize to YAML with nice formatting
        config_dict = config.model_dump(mode="json", exclude_none=True)

        with open(config_path, "w") as f:
            yaml.dump(
                config_dict,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        return config_path

    @classmethod
    def exists(cls, prefer_project: bool = True) -> bool:
        """Check if configuration file exists.

        Args:
            prefer_project: Check project-local first if True

        Returns:
            True if configuration file exists
        """
        return find_config_file(cls.CONFIG_FILENAME) is not None

    @classmethod
    def get_config_location(cls, prefer_project: bool = True) -> Path:
        """Get path where configuration would be saved.

        Args:
            prefer_project: Get project-local path if True

        Returns:
            Path to configuration file (may not exist)
        """
        return get_config_path(cls.CONFIG_FILENAME, prefer_project=prefer_project)
```

**Usage Example**:

```python
# Load configuration (auto-detects location)
config = ConfigManager.load()

# Modify configuration
config.deployment.method = DeploymentMethod.JUSTFILE
config.services.redis.port = 6380

# Save to user-global config
ConfigManager.save(config, project_local=False)

# Save to project-local config
ConfigManager.save(config, project_local=True)
```

**Acceptance Criteria**:

- [ ] load() finds and loads config from hierarchical locations
- [ ] load() returns defaults if no config file exists
- [ ] save() validates before writing
- [ ] save() creates parent directories
- [ ] YAML output is clean and readable
- [ ] Clear error messages on validation failure
- [ ] Handles empty/corrupt config files gracefully

**Deliverables**:

- `mycelium_onboarding/config/manager.py`
- `tests/test_config_manager.py`

______________________________________________________________________

### Task 2.3: Schema Migration Framework

**Agent**: python-pro **Effort**: 8 hours **Dependencies**: Task 2.1, Task 2.2

**Description**: Implement schema migration system to handle configuration upgrades.

**Implementation**:

```python
# mycelium_onboarding/config/migrations.py
"""Configuration schema migrations."""

from typing import Any, Callable
import logging

logger = logging.getLogger(__name__)

# Type alias for migration function
MigrationFunc = Callable[[dict[str, Any]], dict[str, Any]]

# Registry of migrations: version -> migration function
_MIGRATIONS: dict[str, MigrationFunc] = {}


def register_migration(from_version: str, to_version: str):
    """Decorator to register a migration function.

    Args:
        from_version: Source schema version
        to_version: Target schema version
    """
    def decorator(func: MigrationFunc) -> MigrationFunc:
        key = f"{from_version}->{to_version}"
        _MIGRATIONS[key] = func
        logger.debug(f"Registered migration: {key}")
        return func
    return decorator


def migrate_config(config_dict: dict[str, Any]) -> dict[str, Any]:
    """Migrate configuration to latest schema version.

    Args:
        config_dict: Raw configuration dictionary

    Returns:
        Migrated configuration dictionary

    Raises:
        ValueError: If migration path not found
    """
    current_version = config_dict.get("version", "0.9")  # Assume 0.9 if missing
    target_version = "1.0"

    if current_version == target_version:
        logger.debug(f"Configuration already at version {target_version}")
        return config_dict

    # Find migration path
    migration_path = _find_migration_path(current_version, target_version)

    if not migration_path:
        raise ValueError(
            f"No migration path from {current_version} to {target_version}"
        )

    # Apply migrations in sequence
    migrated = config_dict.copy()
    for from_ver, to_ver in migration_path:
        key = f"{from_ver}->{to_ver}"
        migration_func = _MIGRATIONS[key]

        logger.info(f"Applying migration: {key}")
        migrated = migration_func(migrated)
        migrated["version"] = to_ver

    return migrated


def _find_migration_path(
    from_version: str,
    to_version: str
) -> list[tuple[str, str]]:
    """Find shortest migration path between versions.

    Args:
        from_version: Starting version
        to_version: Target version

    Returns:
        List of (from, to) version tuples forming migration path
    """
    # Simple linear path for now (can extend to graph search later)
    if from_version == "0.9" and to_version == "1.0":
        return [("0.9", "1.0")]

    return []


# Define migrations

@register_migration("0.9", "1.0")
def migrate_0_9_to_1_0(config: dict[str, Any]) -> dict[str, Any]:
    """Migrate from schema 0.9 to 1.0.

    Changes:
    - Add deployment.healthcheck_timeout field
    - Rename service.redis.memory to service.redis.max_memory
    - Add service.postgres.max_connections field
    """
    migrated = config.copy()

    # Add deployment.healthcheck_timeout
    if "deployment" not in migrated:
        migrated["deployment"] = {}
    if "healthcheck_timeout" not in migrated["deployment"]:
        migrated["deployment"]["healthcheck_timeout"] = 60

    # Rename redis.memory to redis.max_memory
    if "services" in migrated and "redis" in migrated["services"]:
        redis = migrated["services"]["redis"]
        if "memory" in redis:
            redis["max_memory"] = redis.pop("memory")

    # Add postgres.max_connections
    if "services" in migrated and "postgres" in migrated["services"]:
        postgres = migrated["services"]["postgres"]
        if "max_connections" not in postgres:
            postgres["max_connections"] = 100

    return migrated
```

**Integration with ConfigManager**:

```python
# In mycelium_onboarding/config/manager.py

from mycelium_onboarding.config.migrations import migrate_config

class ConfigManager:
    @classmethod
    def load_from_path(cls, path: Path) -> MyceliumConfig:
        """Load configuration from specific path with migration."""
        # ... existing code to load YAML ...

        # Apply migrations if needed
        if data.get("version") != "1.0":
            logger.info(f"Migrating configuration from {data.get('version')} to 1.0")
            data = migrate_config(data)

        try:
            return MyceliumConfig.model_validate(data)
        except ValidationError as e:
            raise ConfigValidationError(
                f"Configuration validation failed in {path}:\n{e}"
            ) from e
```

**Acceptance Criteria**:

- [ ] Migration framework supports version detection
- [ ] Migrations registered via decorator pattern
- [ ] Migrations applied automatically on load
- [ ] Migration path finding supports linear and branching paths
- [ ] Logged migration actions for transparency
- [ ] Existing user customizations preserved
- [ ] Failed migrations raise clear errors

**Deliverables**:

- `mycelium_onboarding/config/migrations.py`
- `tests/test_migrations.py`
- Migration guide in documentation

______________________________________________________________________

### Task 2.4: Configuration CLI Commands

**Agent**: python-pro **Effort**: 4 hours **Dependencies**: Task 2.2

**Description**: Create CLI commands for viewing and validating configuration.

**Implementation**:

```python
# mycelium_onboarding/cli/config_commands.py
"""CLI commands for configuration management."""

import click
import yaml
from pathlib import Path

from mycelium_onboarding.config.manager import ConfigManager, ConfigValidationError
from mycelium_onboarding.config.schema import MyceliumConfig


@click.group(name="config")
def config_group():
    """Configuration management commands."""
    pass


@config_group.command(name="show")
@click.option(
    "--project-local",
    is_flag=True,
    help="Show project-local configuration only"
)
@click.option(
    "--format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format"
)
def show_config(project_local: bool, format: str):
    """Show current configuration."""
    try:
        config = ConfigManager.load(prefer_project=project_local)

        if format == "yaml":
            output = yaml.dump(
                config.model_dump(mode="json"),
                default_flow_style=False,
                sort_keys=False
            )
        else:  # json
            output = config.model_dump_json(indent=2)

        click.echo(output)

    except ConfigValidationError as e:
        click.echo(f"❌ Configuration invalid: {e}", err=True)
        raise click.Abort()


@config_group.command(name="validate")
@click.argument("config_file", type=click.Path(exists=True), required=False)
def validate_config(config_file: Optional[str]):
    """Validate configuration file.

    If CONFIG_FILE not provided, validates current configuration.
    """
    try:
        if config_file:
            config = ConfigManager.load_from_path(Path(config_file))
            click.echo(f"✓ Configuration valid: {config_file}")
        else:
            config = ConfigManager.load()
            click.echo("✓ Configuration valid")

        # Show summary
        enabled_services = [
            name for name, svc in config.services.model_dump().items()
            if svc.get("enabled", False)
        ]
        click.echo(f"\nDeployment: {config.deployment.method.value}")
        click.echo(f"Services: {', '.join(enabled_services)}")

    except ConfigValidationError as e:
        click.echo(f"❌ Configuration invalid:\n{e}", err=True)
        raise click.Abort()
    except FileNotFoundError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.Abort()


@config_group.command(name="location")
@click.option(
    "--project-local",
    is_flag=True,
    help="Show project-local location"
)
def show_location(project_local: bool):
    """Show configuration file location."""
    location = ConfigManager.get_config_location(prefer_project=project_local)
    exists = location.exists()

    status = "✓" if exists else "✗"
    click.echo(f"{status} {location}")

    if not exists:
        click.echo("  (file does not exist)")


@config_group.command(name="init")
@click.option(
    "--project-local",
    is_flag=True,
    help="Create project-local configuration"
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing configuration"
)
def init_config(project_local: bool, force: bool):
    """Initialize configuration with defaults."""
    location = ConfigManager.get_config_location(prefer_project=project_local)

    if location.exists() and not force:
        click.echo(f"❌ Configuration already exists: {location}", err=True)
        click.echo("Use --force to overwrite")
        raise click.Abort()

    # Create default configuration
    config = MyceliumConfig()
    saved_path = ConfigManager.save(config, project_local=project_local)

    click.echo(f"✓ Created configuration: {saved_path}")
```

**Acceptance Criteria**:

- [ ] `mycelium config show` displays current configuration
- [ ] `mycelium config validate` checks configuration validity
- [ ] `mycelium config location` shows where config is stored
- [ ] `mycelium config init` creates default configuration
- [ ] Commands support --project-local flag
- [ ] Clear success/error messages
- [ ] Help text for all commands

**Deliverables**:

- `mycelium_onboarding/cli/config_commands.py`
- CLI integration tests

______________________________________________________________________

### Task 2.5: Configuration Documentation & Examples

**Agent**: platform-engineer (support from technical-writer) **Effort**: 4 hours **Dependencies**: Tasks 2.1-2.4

**Description**: Create comprehensive configuration documentation with examples.

**Documentation Outline**:

````markdown
# Configuration Reference

## Configuration File Location

Mycelium follows XDG Base Directory specification:

**User-global**: `~/.config/mycelium/config.yaml`
**Project-local**: `.mycelium/config.yaml`

Precedence: project-local → user-global → defaults

## Configuration Schema

### Top-Level Fields

```yaml
version: "1.0"           # Schema version (required)
project_name: mycelium   # Project identifier
deployment:              # Deployment configuration
  # ... see Deployment section
services:                # Service configurations
  # ... see Services section
```

### Deployment Configuration

```yaml
deployment:
  method: docker-compose           # "docker-compose" or "justfile"
  auto_start: true                 # Auto-start services on deployment
  healthcheck_timeout: 60          # Seconds to wait for services
```

### Services Configuration

#### Redis

```yaml
services:
  redis:
    enabled: true
    version: "7"                   # Optional: specific version
    port: 6379
    persistence: true              # Enable RDB snapshots
    max_memory: "256mb"            # Memory limit
    custom_config:
      key: value                   # Additional Redis config
```

#### PostgreSQL

```yaml
services:
  postgres:
    enabled: true
    version: "15"
    port: 5432
    database: mycelium
    max_connections: 100
    custom_config: {}
```

#### Temporal

```yaml
services:
  temporal:
    enabled: true
    ui_port: 8080
    frontend_port: 7233
    namespace: default
```

## Examples

### Minimal Configuration

```yaml
version: "1.0"
```

### Docker Compose Deployment

```yaml
version: "1.0"
deployment:
  method: docker-compose
  auto_start: true
services:
  redis:
    enabled: true
  postgres:
    enabled: true
  temporal:
    enabled: true
```

### Bare-Metal Deployment

```yaml
version: "1.0"
deployment:
  method: justfile
  auto_start: false
services:
  redis:
    enabled: true
    port: 6380                     # Custom port
  postgres:
    enabled: false                 # Use external Postgres
```

### Custom Ports

```yaml
version: "1.0"
services:
  redis:
    port: 6380
  postgres:
    port: 5433
  temporal:
    ui_port: 8081
    frontend_port: 7234
```

## CLI Usage

```bash
# View current configuration
mycelium config show

# Validate configuration
mycelium config validate

# Show configuration location
mycelium config location

# Initialize with defaults
mycelium config init

# Initialize project-local config
mycelium config init --project-local
```

## Schema Migrations

Configuration schema evolves over time. Migrations are applied automatically on load.

**Current Version**: 1.0
**Previous Versions**: 0.9

To manually migrate:
```bash
# Backup first
cp ~/.config/mycelium/config.yaml ~/.config/mycelium/config.yaml.backup

# Load will automatically migrate
mycelium config validate
```

## Troubleshooting

### Validation Errors

**Problem**: `Configuration validation failed`

**Solution**: Check error message for specific field issues. Common problems:
- Invalid port number (must be 1-65535)
- Invalid project name (alphanumeric, hyphens, underscores only)
- Missing required fields

### File Not Found

**Problem**: `Configuration file not found`

**Solution**: Create default configuration:
```bash
mycelium config init
```

### YAML Syntax Errors

**Problem**: `Invalid YAML`

**Solution**: Validate YAML syntax using online tools or:
```bash
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```
````

**Acceptance Criteria**:

- [ ] Complete reference documentation with all fields
- [ ] Examples cover common use cases
- [ ] CLI usage documented with examples
- [ ] Migration process explained
- [ ] Troubleshooting guide addresses common issues

**Deliverables**:

- `docs/configuration-reference.md`
- `docs/examples/` directory with example configs

______________________________________________________________________

## Exit Criteria

- [ ] **Configuration Schema**

  - [ ] Complete Pydantic schema with all fields
  - [ ] Type validation for all fields
  - [ ] Sensible defaults for optional fields
  - [ ] Field validators ensure data integrity
  - [ ] Schema version for migration support

- [ ] **Configuration Manager**

  - [ ] load() finds and loads config from hierarchical locations
  - [ ] save() validates before writing
  - [ ] Clean YAML serialization
  - [ ] Clear error messages on validation failure

- [ ] **Schema Migrations**

  - [ ] Migration framework implemented
  - [ ] Migrations applied automatically on load
  - [ ] Migration actions logged
  - [ ] User customizations preserved

- [ ] **CLI Commands**

  - [ ] show, validate, location, init commands working
  - [ ] Support for --project-local flag
  - [ ] Helpful error messages

- [ ] **Testing**

  - [ ] Unit tests for all schema fields (≥85% coverage)
  - [ ] Tests for loading/saving configurations
  - [ ] Tests for migration framework
  - [ ] Tests for CLI commands

- [ ] **Documentation**

  - [ ] Complete configuration reference
  - [ ] Examples for common scenarios
  - [ ] Migration guide
  - [ ] Troubleshooting guide

## Deliverables

### Code Modules

- `mycelium_onboarding/config/schema.py` - Pydantic configuration schema
- `mycelium_onboarding/config/manager.py` - Configuration loading/saving
- `mycelium_onboarding/config/migrations.py` - Schema migration framework
- `mycelium_onboarding/cli/config_commands.py` - CLI commands

### Tests

- `tests/test_config_schema.py` - Schema validation tests
- `tests/test_config_manager.py` - Manager tests
- `tests/test_migrations.py` - Migration tests
- `tests/cli/test_config_commands.py` - CLI tests

### Documentation

- `docs/configuration-reference.md` - Complete reference
- `docs/examples/` - Example configurations
- `docs/migration-guide.md` - Schema migration guide

## Risk Assessment

### High Risk

**Schema evolution breaks existing configs**: Changes to schema structure may invalidate user configurations

- **Mitigation**: Comprehensive migration framework from day 1
- **Contingency**: Manual migration instructions as fallback

### Medium Risk

**YAML parsing edge cases**: Complex YAML may parse unexpectedly

- **Mitigation**: Use yaml.safe_load, comprehensive tests
- **Contingency**: Provide JSON format as alternative

**Validation errors too strict**: Over-validation may reject valid configs

- **Mitigation**: Reasonable validators, allow customization
- **Contingency**: Disable specific validators via config flag

### Low Risk

**File I/O errors**: Permission issues, disk full

- **Mitigation**: Clear error messages, check permissions early
- **Contingency**: None needed (standard file operations)

## Dependencies for Next Milestones

### M04: Interactive Onboarding

**Depends on**:

- Configuration schema for storing user selections
- ConfigManager for saving wizard results
- Validation for ensuring user input valid

**Will use**:

- `MyceliumConfig` schema for type-safe storage
- `ConfigManager.save()` to persist wizard results
- Field validators to check user input

### M05: Deployment Generation

**Depends on**:

- Configuration schema for deployment parameters
- ConfigManager for loading user preferences

**Will use**:

- `config.deployment.method` to choose Docker Compose vs Justfile
- `config.services` to determine which services to deploy
- Port numbers and other service-specific config

______________________________________________________________________

**Milestone Version**: 1.0 **Last Updated**: 2025-10-13 **Status**: Ready for Implementation
