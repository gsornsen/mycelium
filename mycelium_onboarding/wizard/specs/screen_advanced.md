# Advanced Screen Specification

## Purpose
Configure advanced service-specific settings. Only shown in Custom Setup mode.

## Layout
```
╔══════════════════════════════════════════════════════════════╗
║                  Advanced Configuration                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Configure advanced service-specific settings.              ║
║  These options are optional - defaults work for most users. ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Redis Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

? Enable Redis persistence (RDB snapshots):
  > Yes (recommended)
    No (ephemeral)

? Maximum memory limit:
  > 256mb

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PostgreSQL Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

? Maximum connections:
  > 100

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Temporal Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

? Namespace:
  > default

? History retention (days):
  > 7
```

## User Inputs

### Redis Settings (if enabled)

#### Persistence
- **Field**: `enable_persistence`
- **Type**: Boolean (yes/no)
- **Default**: `true`
- **Description**: Enable RDB snapshots for data persistence

#### Max Memory
- **Field**: `redis_max_memory`
- **Type**: Text (memory size)
- **Default**: `256mb`
- **Validation**: Must match pattern `^\d+[kmgtKMGT][bB]$`
- **Examples**: `256mb`, `1gb`, `512MB`

### PostgreSQL Settings (if enabled)

#### Max Connections
- **Field**: `postgres_max_connections`
- **Type**: Integer
- **Default**: `100`
- **Range**: 1-10000
- **Description**: Maximum concurrent database connections

### Temporal Settings (if enabled)

#### Namespace
- **Field**: `temporal_namespace`
- **Type**: Text
- **Default**: `default`
- **Validation**: Must match pattern `^[a-zA-Z0-9_-]+$`
- **Description**: Workflow namespace for isolation

#### History Retention
- **Field**: `temporal_history_retention_days`
- **Type**: Integer
- **Default**: `7`
- **Range**: 1-365
- **Description**: Days to retain workflow history

## Validation

### Redis Max Memory
```python
import re

if not re.match(r'^\d+[kmgtKMGT][bB]$', max_memory):
    raise ValueError(
        "Memory must be in format '<number><unit>' where unit is "
        "kb, mb, gb, or tb. Examples: 256mb, 1gb, 2GB"
    )
```

### PostgreSQL Max Connections
```python
if not (1 <= max_connections <= 10000):
    raise ValueError(
        f"Max connections must be between 1 and 10000, got {max_connections}"
    )
```

### Temporal Namespace
```python
import re

if not re.match(r'^[a-zA-Z0-9_-]+$', namespace):
    raise ValueError(
        "Namespace must contain only alphanumeric characters, "
        "hyphens, and underscores"
    )
```

### History Retention
```python
if not (1 <= retention_days <= 365):
    raise ValueError(
        f"Retention must be between 1 and 365 days, got {retention_days}"
    )
```

## Help Text

### Redis Persistence
```
Redis Persistence (RDB Snapshots)
═══════════════════════════════════════════════════════════

Enabled (recommended):
• Data is periodically saved to disk
• Survives restarts and crashes
• Small performance overhead
• Suitable for caching and session storage

Disabled (ephemeral):
• All data is lost on restart
• Maximum performance
• Suitable for temporary data only
• Not recommended for production

Default: Enabled
```

### Redis Max Memory
```
Redis Maximum Memory
═══════════════════════════════════════════════════════════

Controls how much RAM Redis can use.

Recommended values:
• Development: 256mb - 512mb
• Production: 1gb - 4gb
• Heavy usage: 8gb+

When limit is reached, Redis will:
• Evict keys based on policy
• Or reject new writes (depending on config)

Examples: 256mb, 1gb, 2GB, 512MB

Default: 256mb
```

### PostgreSQL Max Connections
```
PostgreSQL Maximum Connections
═══════════════════════════════════════════════════════════

Maximum number of concurrent database connections.

Recommended values:
• Development: 50-100
• Production: 100-200
• High traffic: 200-500

Higher values require more memory:
• Each connection uses ~10MB RAM
• Balance between concurrency and memory

Default: 100
```

### Temporal Namespace
```
Temporal Namespace
═══════════════════════════════════════════════════════════

Namespaces provide isolation for workflows.

Use cases:
• Separate dev/staging/prod: "dev", "staging", "prod"
• Per-team isolation: "team-a", "team-b"
• Per-project: "project-x", "project-y"

Best practices:
• Use descriptive names
• Keep it simple and consistent
• Avoid special characters

Default: "default"
```

### Temporal History Retention
```
Temporal Workflow History Retention
═══════════════════════════════════════════════════════════

Number of days to retain completed workflow history.

Considerations:
• Longer retention = more storage required
• Shorter retention = less audit trail
• Can be changed later

Recommended values:
• Development: 1-7 days
• Production: 7-30 days
• Compliance: 90-365 days

Default: 7 days
```

## Error Messages

### Invalid Memory Format
```
⚠️  Invalid memory format: "{value}"

Memory must be specified as:
• Number followed by unit
• Units: kb, mb, gb, tb (case-insensitive)

Valid examples:
• 256mb
• 1gb
• 512MB
• 2GB

Invalid examples:
• 256 (missing unit)
• 1g (use gb, not g)
• mb256 (number must come first)
```

### Connections Out of Range
```
⚠️  Max connections out of range: {value}

PostgreSQL max_connections must be between 1 and 10,000.

Considerations:
• Each connection uses ~10MB RAM
• More connections = more memory required
• Balance concurrency with available resources

Recommended: 100-200 for most applications
```

### Invalid Namespace
```
⚠️  Invalid namespace: "{namespace}"

Namespace must:
• Contain only alphanumeric characters, hyphens, underscores
• Not contain spaces or special characters

Valid examples:
• default
• my-project
• team_a
• prod-env

Invalid examples:
• my project (no spaces)
• prod.env (no dots)
• team@a (no special chars)
```

### Retention Out of Range
```
⚠️  History retention out of range: {value} days

Retention must be between 1 and 365 days.

Considerations:
• Longer retention = more storage
• Minimum 1 day recommended
• Maximum 365 days (1 year)

Adjust based on:
• Storage capacity
• Audit requirements
• Compliance needs
```

## State Updates

On completion of this screen, update `WizardState`:
- `enable_persistence`: Redis persistence setting
- `redis_max_memory`: Redis memory limit (stored in RedisConfig.max_memory)
- `postgres_max_connections`: PostgreSQL connection limit (stored in PostgresConfig.max_connections)
- `temporal_namespace`: Temporal namespace
- `temporal_history_retention_days`: Retention period (stored in custom_config)

## Next Step Logic

- **Continue** → Proceed to REVIEW screen
- **Back** → Return to DEPLOYMENT screen

## InquirerPy Implementation

```python
from InquirerPy import inquirer
from InquirerPy.validator import NumberValidator
import re

def advanced_screen(state: WizardState) -> str:
    """Display advanced configuration screen.

    Only shown in Custom Setup mode.

    Args:
        state: Current wizard state

    Returns:
        Action: "continue" or "back"
    """
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                  Advanced Configuration                      ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║                                                              ║")
    print("║  Configure advanced service-specific settings.              ║")
    print("║  These options are optional - defaults work for most users. ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Redis advanced settings
    if state.services_enabled.get("redis"):
        print("━" * 64)
        print("Redis Configuration")
        print("━" * 64)
        print()

        enable_persistence = inquirer.confirm(
            message="Enable Redis persistence (RDB snapshots)?",
            default=state.enable_persistence,
            long_instruction="Recommended: saves data to disk periodically",
        ).execute()

        state.enable_persistence = enable_persistence

        max_memory = inquirer.text(
            message="Maximum memory limit:",
            default="256mb",
            validate=lambda mem: (
                bool(re.match(r'^\d+[kmgtKMGT][bB]$', mem))
                or "Format: <number><unit> (e.g., 256mb, 1gb)"
            ),
            invalid_message="Invalid memory format",
            long_instruction="Examples: 256mb, 1gb, 512MB",
        ).execute()

        # Store in state for later use in config generation
        if not hasattr(state, 'redis_max_memory'):
            state.redis_max_memory = max_memory
        else:
            state.redis_max_memory = max_memory

        print()

    # PostgreSQL advanced settings
    if state.services_enabled.get("postgres"):
        print("━" * 64)
        print("PostgreSQL Configuration")
        print("━" * 64)
        print()

        max_connections = inquirer.number(
            message="Maximum connections:",
            default="100",
            min_allowed=1,
            max_allowed=10000,
            validate=NumberValidator(),
            long_instruction="Recommended: 100-200 for most applications",
        ).execute()

        # Store in state
        if not hasattr(state, 'postgres_max_connections'):
            state.postgres_max_connections = int(max_connections)
        else:
            state.postgres_max_connections = int(max_connections)

        print()

    # Temporal advanced settings
    if state.services_enabled.get("temporal"):
        print("━" * 64)
        print("Temporal Configuration")
        print("━" * 64)
        print()

        namespace = inquirer.text(
            message="Namespace:",
            default=state.temporal_namespace,
            validate=lambda ns: (
                bool(re.match(r'^[a-zA-Z0-9_-]+$', ns))
                or "Must contain only alphanumeric, hyphens, underscores"
            ),
            invalid_message="Invalid namespace",
            long_instruction="Used for workflow isolation",
        ).execute()

        state.temporal_namespace = namespace

        history_retention = inquirer.number(
            message="History retention (days):",
            default="7",
            min_allowed=1,
            max_allowed=365,
            validate=NumberValidator(),
            long_instruction="Days to retain completed workflow history",
        ).execute()

        # Store in state
        if not hasattr(state, 'temporal_history_retention_days'):
            state.temporal_history_retention_days = int(history_retention)
        else:
            state.temporal_history_retention_days = int(history_retention)

        print()

    # Navigation
    print("━" * 64)
    print()

    action = inquirer.select(
        message="What would you like to do?",
        choices=[
            {"name": "Continue to review", "value": "continue"},
            {"name": "Back to deployment", "value": "back"},
        ],
        default="continue",
    ).execute()

    return action
```

## Accessibility Notes

- Clear section headers with separators
- Helpful defaults for all settings
- Comprehensive help text with examples
- Validation feedback
- Optional skip (can use defaults)
- Keyboard navigation

## Design Rationale

This screen provides power-user features without overwhelming beginners:

1. **Optional**: Only shown in Custom Setup mode
2. **Defaults Work**: All settings have sensible defaults
3. **Educational**: Help text explains tradeoffs
4. **Contextual**: Only shows settings for enabled services
5. **Validation**: Prevents invalid configurations
6. **Progressive Disclosure**: Each service in its own section
7. **Examples**: Concrete examples for each setting
