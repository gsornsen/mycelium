# Mycelium Configuration Migration Guide

> **Comprehensive guide** for migrating configuration schemas across versions.

## Table of Contents

- [Overview](#overview)
- [When to Migrate](#when-to-migrate)
- [Migration Command](#migration-command)
- [Version History](#version-history)
- [Writing Custom Migrations](#writing-custom-migrations)
- [Rollback Procedures](#rollback-procedures)
- [Version Compatibility](#version-compatibility)

## Overview

Mycelium's configuration schema evolves over time to support new features and improvements. The migration framework ensures smooth upgrades while preserving your customizations.

### How Migrations Work

1. **Automatic Detection**: System detects configuration version when loading
2. **Migration Path Discovery**: Finds optimal path from current to target version
3. **Sequential Application**: Applies migrations in order (e.g., 1.0 → 1.1 → 1.2)
4. **Validation**: Validates before and after each migration step
5. **Backup**: Creates automatic backup before migration
6. **Persistence**: Saves migrated configuration to file

### Key Features

- **Automatic**: Migrations applied automatically when loading configuration
- **Transparent**: Detailed logging of all migration actions
- **Safe**: Backups created before migration, validation at each step
- **Reversible**: Rollback capability (where supported)
- **Customizable**: Write your own migrations

## When to Migrate

### Automatic Migration Scenarios

Migrations are applied automatically in these situations:

#### 1. Loading Configuration with Old Version

When you load a configuration file with an older schema version:

```bash
# Your config.yaml has version: "1.0"
# Current default is "1.1"
mycelium config show
# Output: Migrating configuration from 1.0 to 1.1...
```

#### 2. Using load_and_migrate()

When explicitly calling the migration-enabled load method:

```python
from mycelium_onboarding.config.manager import ConfigManager

manager = ConfigManager()
config = manager.load_and_migrate()  # Auto-migrates to latest
```

#### 3. Validation Workflow

Some commands trigger migration checks:

```bash
mycelium config validate  # May suggest migration if needed
```

### Manual Migration Scenarios

You may want to manually migrate in these cases:

#### 1. Upgrading to New Release

After updating Mycelium to a version with schema changes:

```bash
# Backup first
cp ~/.config/mycelium/config.yaml ~/.config/mycelium/config.yaml.manual-backup

# Preview migration
mycelium config migrate --dry-run

# Apply migration
mycelium config migrate
```

#### 2. Testing New Features

Before deploying to production, test migration on development config:

```bash
# Test migration on dev config
mycelium config migrate --path dev-config.yaml --target 1.2

# If successful, apply to production
mycelium config migrate --path prod-config.yaml --target 1.2
```

#### 3. Batch Migration

Migrating multiple configuration files:

```bash
# Migrate all configs in directory
for config in configs/*.yaml; do
    mycelium config migrate --path "$config" --target 1.2
done
```

### When NOT to Migrate

**Do not migrate if**:

- You're using the latest schema version (no migration needed)
- You're actively editing configuration (finish edits first)
- Your configuration has validation errors (fix errors first)
- You don't have backups (create backups first)

## Migration Command

### Basic Usage

```bash
# Migrate current configuration to latest version
mycelium config migrate

# Preview migration without applying
mycelium config migrate --dry-run

# Migrate specific file
mycelium config migrate --path /path/to/config.yaml

# Migrate to specific version
mycelium config migrate --target 1.1
```

### Command Options

#### `--path PATH`

Migrate specific configuration file.

```bash
mycelium config migrate --path custom-config.yaml
```

**Default**: Uses hierarchical search (project-local → user-global)

#### `--target VERSION`

Target schema version to migrate to.

```bash
mycelium config migrate --target 1.2
```

**Default**: Latest supported version (current default schema version)
**Format**: `"<major>.<minor>"` (e.g., "1.0", "1.1", "1.2")

#### `--dry-run`

Preview migration changes without applying them.

```bash
mycelium config migrate --dry-run
```

**Output**: Shows what would change without modifying files.

**Example output**:
```
Migration Preview: 1.0 -> 1.1

Added fields:
  + monitoring: {
      "enabled": false,
      "metrics_port": 9090,
      "health_check_interval": 30
    }
  + deployment.log_level: "INFO"

No modifications or removals.
```

#### `--force`

Force migration even if already at target version.

```bash
mycelium config migrate --force
```

**Use case**: Re-apply migration to fix manual edits or corruption.

#### `--no-backup`

Skip automatic backup creation.

```bash
mycelium config migrate --no-backup
```

**Warning**: Not recommended. Always keep backups.

### Migration Workflow

Complete workflow with safety checks:

```bash
# 1. Check current version
mycelium config show | head -1

# 2. Create manual backup
cp ~/.config/mycelium/config.yaml ~/config-backup-$(date +%Y%m%d).yaml

# 3. Preview migration
mycelium config migrate --dry-run

# 4. Review changes
cat ~/.config/mycelium/config.yaml

# 5. Apply migration
mycelium config migrate

# 6. Validate migrated config
mycelium config validate

# 7. Test with your application
mycelium status
```

## Version History

### Version 1.0 (Current)

**Release Date**: 2025-10-13

**Initial release** with core configuration schema:

- Deployment configuration (method, auto_start, healthcheck_timeout)
- Redis configuration (port, persistence, max_memory)
- PostgreSQL configuration (port, database, max_connections)
- Temporal configuration (ui_port, frontend_port, namespace)
- Project naming and versioning

**Schema**:
```yaml
version: "1.0"
project_name: mycelium
deployment: {...}
services:
  redis: {...}
  postgres: {...}
  temporal: {...}
```

### Version 1.1 (Example - Future)

**Release Date**: TBD

**Planned changes**:

- Add `monitoring` configuration section
- Add `deployment.log_level` field
- Enhanced observability features

**Migration from 1.0**:
- Adds `monitoring` section with defaults
- Adds `deployment.log_level` set to "INFO"
- All existing fields preserved

**Example migrated config**:
```yaml
version: "1.1"
project_name: mycelium

deployment:
  method: docker-compose
  auto_start: true
  healthcheck_timeout: 60
  log_level: "INFO"  # NEW

monitoring:  # NEW
  enabled: false
  metrics_port: 9090
  health_check_interval: 30

services:
  redis: {...}
  postgres: {...}
  temporal: {...}
```

### Version 1.2 (Example - Future)

**Release Date**: TBD

**Planned changes**:

- Add `backup` configuration section
- Rename `deployment.log_level` to `deployment.logging_level`
- Enhanced backup and recovery features

**Migration from 1.1**:
- Adds `backup` section with defaults
- Renames `deployment.log_level` to `deployment.logging_level`
- Preserves custom logging level value

**Example migrated config**:
```yaml
version: "1.2"
project_name: mycelium

deployment:
  method: docker-compose
  auto_start: true
  healthcheck_timeout: 60
  logging_level: "INFO"  # RENAMED from log_level

monitoring:
  enabled: false
  metrics_port: 9090
  health_check_interval: 30

backup:  # NEW
  enabled: false
  schedule: "0 2 * * *"
  retention_days: 30

services:
  redis: {...}
  postgres: {...}
  temporal: {...}
```

## Writing Custom Migrations

### Migration Class Structure

Custom migrations extend the `Migration` base class:

```python
from mycelium_onboarding.config.migrations import Migration
from typing import Any

class Migration_1_2_to_1_3(Migration):
    """Migrate from version 1.2 to 1.3.

    Changes:
    - Add security configuration section
    - Add SSL/TLS settings
    """

    @property
    def from_version(self) -> str:
        return "1.2"

    @property
    def to_version(self) -> str:
        return "1.3"

    @property
    def description(self) -> str:
        return "Add security and SSL/TLS configuration"

    def migrate(self, config_dict: dict[str, Any]) -> dict[str, Any]:
        """Perform migration."""
        # Add security section
        config_dict["security"] = {
            "ssl_enabled": False,
            "tls_version": "1.3",
            "cert_path": None,
            "key_path": None,
        }

        # Update version
        config_dict["version"] = self.to_version

        return config_dict
```

### Migration Best Practices

#### 1. Preserve User Data

Always preserve user customizations:

```python
def migrate(self, config_dict: dict[str, Any]) -> dict[str, Any]:
    # BAD: Overwrites user customization
    config_dict["redis"]["port"] = 6379

    # GOOD: Preserves existing value
    if "redis" not in config_dict:
        config_dict["redis"] = {}
    if "port" not in config_dict["redis"]:
        config_dict["redis"]["port"] = 6379

    return config_dict
```

#### 2. Handle Missing Fields Gracefully

Check for field existence before accessing:

```python
def migrate(self, config_dict: dict[str, Any]) -> dict[str, Any]:
    # Check if section exists
    if "deployment" in config_dict:
        # Safe to access
        if "auto_start" not in config_dict["deployment"]:
            config_dict["deployment"]["auto_start"] = True
    else:
        # Create section with defaults
        config_dict["deployment"] = {
            "method": "docker-compose",
            "auto_start": True,
        }

    return config_dict
```

#### 3. Rename Fields Carefully

Preserve values when renaming:

```python
def migrate(self, config_dict: dict[str, Any]) -> dict[str, Any]:
    # Rename field while preserving value
    if "deployment" in config_dict:
        if "log_level" in config_dict["deployment"]:
            # Get old value
            old_value = config_dict["deployment"].pop("log_level")
            # Set new field with old value
            config_dict["deployment"]["logging_level"] = old_value

    return config_dict
```

#### 4. Provide Sensible Defaults

Use defaults that work for most users:

```python
def migrate(self, config_dict: dict[str, Any]) -> dict[str, Any]:
    # Add new feature disabled by default (safe)
    config_dict["monitoring"] = {
        "enabled": False,  # Disabled by default
        "metrics_port": 9090,
        "interval": 30,
    }

    # User can enable explicitly
    return config_dict
```

#### 5. Log Migration Actions

Use logging to track changes:

```python
import logging

logger = logging.getLogger(__name__)

def migrate(self, config_dict: dict[str, Any]) -> dict[str, Any]:
    logger.info("Adding monitoring configuration")

    config_dict["monitoring"] = {
        "enabled": False,
        "metrics_port": 9090,
    }

    logger.debug("Monitoring config: %s", config_dict["monitoring"])

    return config_dict
```

### Registering Custom Migrations

Register your migration with the default registry:

```python
# In mycelium_onboarding/config/migrations.py

def get_default_registry() -> MigrationRegistry:
    """Get default migration registry with all migrations."""
    registry = MigrationRegistry()

    # Existing migrations
    registry.register(Migration_1_0_to_1_1())
    registry.register(Migration_1_1_to_1_2())

    # Your custom migration
    registry.register(Migration_1_2_to_1_3())

    return registry
```

### Testing Custom Migrations

Write tests for your migrations:

```python
import pytest
from mycelium_onboarding.config.migrations import Migration_1_2_to_1_3

def test_migration_1_2_to_1_3():
    """Test migration from 1.2 to 1.3."""
    # Setup: 1.2 config
    config_1_2 = {
        "version": "1.2",
        "project_name": "test",
        "deployment": {"method": "docker-compose"},
    }

    # Execute migration
    migration = Migration_1_2_to_1_3()
    migrated = migration.migrate(config_1_2.copy())

    # Verify: security section added
    assert "security" in migrated
    assert migrated["security"]["ssl_enabled"] is False

    # Verify: version updated
    assert migrated["version"] == "1.3"

    # Verify: existing fields preserved
    assert migrated["project_name"] == "test"
    assert migrated["deployment"]["method"] == "docker-compose"
```

## Rollback Procedures

### Automatic Backups

Every migration creates a backup:

**Backup location**: `<config_path>.backup`

**Example**:
```bash
# Original config
~/.config/mycelium/config.yaml

# Automatic backup
~/.config/mycelium/config.yaml.backup
```

### Manual Rollback

Restore from automatic backup:

```bash
# 1. Check backup exists
ls -la ~/.config/mycelium/config.yaml.backup

# 2. View backup content
cat ~/.config/mycelium/config.yaml.backup

# 3. Restore backup
cp ~/.config/mycelium/config.yaml.backup ~/.config/mycelium/config.yaml

# 4. Validate restored config
mycelium config validate
```

### Rollback to Specific Version

Create version-specific backups:

```bash
# Before migration
cp config.yaml config.yaml.v1.0

# After migration to 1.1
cp config.yaml config.yaml.v1.1

# After migration to 1.2
cp config.yaml config.yaml.v1.2

# Rollback to 1.0
cp config.yaml.v1.0 config.yaml
```

### Downgrade Limitations

**Important**: Downgrading (migrating to older version) is **not supported** by the migration framework.

**Why**: Older schemas may not have fields added in newer versions. Data loss would occur.

**Alternatives**:

1. **Manual restoration**: Restore from backup created before upgrade
2. **Manual editing**: Manually edit config to match older schema
3. **Fresh start**: Create new config with `mycelium config init`

**Example limitation**:
```yaml
# Version 1.2 config
version: "1.2"
backup:  # This field doesn't exist in 1.1
  enabled: true
  schedule: "0 2 * * *"

# Cannot auto-migrate to 1.1
# Would lose backup configuration
```

### Backup Best Practices

1. **Manual backups before upgrades**:
   ```bash
   cp config.yaml config.yaml.backup-$(date +%Y%m%d-%H%M%S)
   ```

2. **Version control**:
   ```bash
   git add .mycelium/config.yaml
   git commit -m "Backup config before 1.2 migration"
   ```

3. **Test migrations**:
   ```bash
   # Test on copy first
   cp config.yaml config-test.yaml
   mycelium config migrate --path config-test.yaml
   ```

4. **Keep multiple backups**:
   ```bash
   # Rotate backups
   cp config.yaml.backup config.yaml.backup.1
   cp config.yaml config.yaml.backup
   ```

## Version Compatibility

### Migration Path Matrix

Table shows which versions can directly migrate:

| From → To | 1.0 | 1.1 | 1.2 |
|-----------|-----|-----|-----|
| **1.0**   | -   | ✓   | ✓*  |
| **1.1**   | ✗   | -   | ✓   |
| **1.2**   | ✗   | ✗   | -   |

- ✓ = Direct or chained migration supported
- ✗ = Downgrade not supported
- \* = Chained migration (1.0 → 1.1 → 1.2)

### Supported Upgrade Paths

#### 1.0 → 1.1 (Direct)

Single migration step.

**Changes**:
- Adds monitoring configuration
- Adds deployment.log_level

**Command**:
```bash
mycelium config migrate --target 1.1
```

#### 1.0 → 1.2 (Chained)

Two migration steps: 1.0 → 1.1 → 1.2

**Changes**:
- 1.0 → 1.1: Adds monitoring, log_level
- 1.1 → 1.2: Adds backup, renames log_level

**Command**:
```bash
mycelium config migrate --target 1.2
```

**Automatic**: Chain is executed automatically.

#### 1.1 → 1.2 (Direct)

Single migration step.

**Changes**:
- Adds backup configuration
- Renames deployment.log_level to logging_level

**Command**:
```bash
mycelium config migrate --target 1.2
```

### Software Version Compatibility

| Mycelium Version | Config Versions Supported | Default Config Version |
|------------------|---------------------------|------------------------|
| v1.0.0           | 1.0                       | 1.0                    |
| v1.1.0           | 1.0, 1.1                  | 1.1                    |
| v1.2.0           | 1.0, 1.1, 1.2             | 1.2                    |

**Note**: Newer Mycelium versions can read and migrate older configs. Older versions cannot read newer configs.

### Checking Compatibility

```bash
# Check current config version
mycelium config show | grep version

# Check software version
mycelium --version

# Check if migration needed
mycelium config validate
```

### Migration Recommendations

**Before upgrading Mycelium**:

1. Backup your configuration
2. Review release notes for schema changes
3. Test migration on development environment
4. Apply migration to production

**Upgrade process**:

```bash
# 1. Backup configuration
cp ~/.config/mycelium/config.yaml ~/config-backup.yaml

# 2. Upgrade Mycelium software
pip install --upgrade mycelium-onboarding

# 3. Preview migration
mycelium config migrate --dry-run

# 4. Apply migration
mycelium config migrate

# 5. Validate
mycelium config validate
```

## Troubleshooting

### Migration Fails

**Problem**: Migration fails with validation error

**Solution**:
1. Check error message for specific field
2. Restore from backup
3. Fix validation errors in original config
4. Retry migration

```bash
# Restore backup
cp config.yaml.backup config.yaml

# Fix validation errors
mycelium config validate

# Retry migration
mycelium config migrate
```

### Backup Missing

**Problem**: Automatic backup not found

**Solution**: Backup only created if file exists before migration
```bash
# Create config first
mycelium config init

# Then migrate
mycelium config migrate
```

### Migration Path Not Found

**Problem**: No migration path from version X to Y

**Solution**: Upgrade Mycelium software to version supporting target schema
```bash
pip install --upgrade mycelium-onboarding
mycelium config migrate
```

### Custom Fields Lost

**Problem**: Custom fields disappear after migration

**Solution**: Custom fields in `custom_config` sections are preserved. Fields outside schema are removed.
```bash
# PRESERVED (in custom_config)
services:
  redis:
    custom_config:
      my_setting: value

# REMOVED (not in schema)
services:
  redis:
    unknown_field: value
```

## See Also

- **User Guide**: [Configuration Guide](configuration-guide.md) - Configuration basics
- **Reference**: [Configuration Reference](configuration-reference.md) - Complete field reference
- **Schema**: `mycelium_onboarding/config/schema.py` - Current schema definition
- **Migrations**: `mycelium_onboarding/config/migrations.py` - Migration implementations
