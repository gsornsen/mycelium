# Services Screen Specification

## Purpose
Allow user to enable/disable services and configure basic service settings.

## Layout
```
╔══════════════════════════════════════════════════════════════╗
║                   Service Configuration                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Select the services you want to enable:                    ║
║                                                              ║
║  [✓] Redis (in-memory data store)                           ║
║      Port: 6379 (detected)                                  ║
║                                                              ║
║  [✓] PostgreSQL (relational database)                       ║
║      Port: 5432 (detected)                                  ║
║      Database: mycelium                                     ║
║                                                              ║
║  [ ] Temporal (workflow orchestration)                      ║
║      Port: 7233 (frontend), 8080 (UI)                      ║
║      Not detected - will be deployed                        ║
║                                                              ║
║  At least one service must be enabled.                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

? Select services to enable: (Use space to select, arrow keys to navigate)
  > [✓] Redis
    [✓] PostgreSQL
    [ ] Temporal
```

## User Inputs

### Service Selection
- **Field**: `services_enabled`
- **Type**: Multiple selection (checkbox)
- **Options**:
  - `redis`: Redis (in-memory data store)
  - `postgres`: PostgreSQL (relational database)
  - `temporal`: Temporal (workflow orchestration)
- **Default**: Pre-selected based on detection results
- **Required**: At least one service must be selected

### Project Name
- **Field**: `project_name`
- **Type**: Text input
- **Default**: `mycelium`
- **Validation**:
  - Required (min 1 char)
  - Max 100 characters
  - Only alphanumeric, hyphens, underscores
  - Must match pattern: `^[a-zA-Z0-9_-]+$`
- **Required**: Yes

### Service-Specific Settings

#### Redis (if enabled)
- **Port**: Integer (1-65535)
  - Default: 6379 or detected port
  - Pre-filled if detected

#### PostgreSQL (if enabled)
- **Port**: Integer (1-65535)
  - Default: 5432 or detected port
  - Pre-filled if detected
- **Database Name**: String
  - Default: Same as project_name
  - Validation: `^[a-zA-Z][a-zA-Z0-9_]*$`
  - Auto-generated from project_name

#### Temporal (if enabled)
- **Frontend Port**: Integer (1-65535)
  - Default: 7233 or detected port
- **UI Port**: Integer (1-65535)
  - Default: 8080 or detected port

## Validation

### Service Selection
```python
if not any(services_enabled.values()):
    raise ValueError("At least one service must be enabled")
```

### Project Name
```python
import re

if not project_name:
    raise ValueError("Project name is required")

if len(project_name) > 100:
    raise ValueError("Project name must be 100 characters or less")

if not re.match(r'^[a-zA-Z0-9_-]+$', project_name):
    raise ValueError(
        "Project name must contain only alphanumeric characters, "
        "hyphens, and underscores"
    )
```

### Port Numbers
```python
if not (1 <= port <= 65535):
    raise ValueError(f"Port must be between 1 and 65535, got {port}")
```

### Database Name
```python
import re

if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', database_name):
    raise ValueError(
        "Database name must start with a letter and contain only "
        "alphanumeric characters and underscores"
    )
```

## Help Text

### Service Descriptions

**Redis**
```
Redis is an in-memory data store used for:
• Caching and session management
• Real-time analytics
• Message queuing
• Pub/sub messaging

Recommended: Yes (required for most Mycelium features)
```

**PostgreSQL**
```
PostgreSQL is a relational database used for:
• Persistent data storage
• Complex queries and transactions
• Workflow state management
• Agent coordination

Recommended: Yes (required for Temporal workflows)
```

**Temporal**
```
Temporal is a workflow orchestration engine used for:
• Durable workflow execution
• Agent task coordination
• Fault-tolerant processing
• Long-running operations

Recommended: Optional (advanced users)
Note: Requires PostgreSQL
```

### Project Name Help
```
Project name is used to:
• Name your configuration file (mycelium-<project>.yaml)
• Set PostgreSQL database name
• Tag Docker containers
• Organize deployment resources

Examples: mycelium, my-agent-system, prod-workflow
```

## Error Messages

### No Services Selected
```
⚠️  At least one service must be enabled.
Please select at least one service to continue.
```

### Invalid Project Name
```
⚠️  Invalid project name: "{project_name}"
Project name must contain only alphanumeric characters, hyphens, and underscores.
Examples: mycelium, my-project, agent_system
```

### Port Conflict
```
⚠️  Port {port} is already in use by another service.
Please choose a different port or stop the conflicting service.
```

### Invalid Database Name
```
⚠️  Invalid database name: "{database_name}"
Database name must start with a letter and contain only alphanumeric
characters and underscores.
Examples: mycelium, agent_db, workflow_state
```

## State Updates

On completion of this screen, update `WizardState`:
- `project_name`: User-specified project name
- `services_enabled`: Dict of enabled services
- `redis_port`: Redis port if enabled
- `postgres_port`: PostgreSQL port if enabled
- `postgres_database`: PostgreSQL database name if enabled
- `temporal_frontend_port`: Temporal frontend port if enabled
- `temporal_ui_port`: Temporal UI port if enabled

## Next Step Logic

- **Continue** → Proceed to DEPLOYMENT screen
- **Back** → Return to DETECTION screen

## InquirerPy Implementation

```python
from InquirerPy import inquirer
from InquirerPy.validator import EmptyInputValidator, NumberValidator
import re

def services_screen(state: WizardState) -> bool:
    """Display services configuration screen.

    Args:
        state: Current wizard state

    Returns:
        True if user wants to continue, False to go back
    """
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                   Service Configuration                      ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║                                                              ║")
    print("║  Configure your project and select services to enable.      ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Get project name
    project_name = inquirer.text(
        message="Project name:",
        default=state.project_name or "mycelium",
        validate=lambda name: (
            bool(re.match(r'^[a-zA-Z0-9_-]+$', name) and 0 < len(name) <= 100)
            or "Must contain only alphanumeric, hyphens, underscores (1-100 chars)"
        ),
        invalid_message="Invalid project name",
        long_instruction="Used for config file, database name, and Docker tags",
    ).execute()

    state.project_name = project_name

    # Auto-generate database name if not set
    if not state.postgres_database:
        state.postgres_database = project_name

    # Service selection
    selected_services = inquirer.checkbox(
        message="Select services to enable:",
        choices=[
            {
                "name": "Redis (in-memory data store)",
                "value": "redis",
                "enabled": state.services_enabled.get("redis", True),
            },
            {
                "name": "PostgreSQL (relational database)",
                "value": "postgres",
                "enabled": state.services_enabled.get("postgres", True),
            },
            {
                "name": "Temporal (workflow orchestration)",
                "value": "temporal",
                "enabled": state.services_enabled.get("temporal", False),
            },
        ],
        validate=lambda result: (
            len(result) > 0 or "At least one service must be enabled"
        ),
        invalid_message="Please select at least one service",
        instruction="Use space to select/deselect, Enter to confirm",
    ).execute()

    # Update services_enabled
    state.services_enabled = {
        "redis": "redis" in selected_services,
        "postgres": "postgres" in selected_services,
        "temporal": "temporal" in selected_services,
    }

    # Configure Redis if enabled
    if state.services_enabled["redis"]:
        detected = (
            state.detection_results
            and state.detection_results.get("redis", {}).get("available")
        )
        default_port = state.redis_port

        redis_port = inquirer.number(
            message="Redis port:",
            default=str(default_port),
            min_allowed=1,
            max_allowed=65535,
            validate=NumberValidator(),
            long_instruction=(
                f"Port {default_port} detected" if detected else "Default: 6379"
            ),
        ).execute()

        state.redis_port = int(redis_port)

    # Configure PostgreSQL if enabled
    if state.services_enabled["postgres"]:
        detected = (
            state.detection_results
            and state.detection_results.get("postgres", {}).get("available")
        )
        default_port = state.postgres_port

        postgres_port = inquirer.number(
            message="PostgreSQL port:",
            default=str(default_port),
            min_allowed=1,
            max_allowed=65535,
            validate=NumberValidator(),
            long_instruction=(
                f"Port {default_port} detected" if detected else "Default: 5432"
            ),
        ).execute()

        state.postgres_port = int(postgres_port)

        # Database name
        database_name = inquirer.text(
            message="PostgreSQL database name:",
            default=state.postgres_database,
            validate=lambda name: (
                bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name))
                or "Must start with letter, contain only alphanumeric/underscores"
            ),
            invalid_message="Invalid database name",
        ).execute()

        state.postgres_database = database_name

    # Configure Temporal if enabled
    if state.services_enabled["temporal"]:
        detected = (
            state.detection_results
            and state.detection_results.get("temporal", {}).get("available")
        )
        default_frontend = state.temporal_frontend_port
        default_ui = state.temporal_ui_port

        frontend_port = inquirer.number(
            message="Temporal frontend port (gRPC):",
            default=str(default_frontend),
            min_allowed=1,
            max_allowed=65535,
            validate=NumberValidator(),
            long_instruction=(
                f"Port {default_frontend} detected" if detected else "Default: 7233"
            ),
        ).execute()

        ui_port = inquirer.number(
            message="Temporal UI port:",
            default=str(default_ui),
            min_allowed=1,
            max_allowed=65535,
            validate=NumberValidator(),
            long_instruction=(
                f"Port {default_ui} detected" if detected else "Default: 8080"
            ),
        ).execute()

        state.temporal_frontend_port = int(frontend_port)
        state.temporal_ui_port = int(ui_port)

    # Navigation
    action = inquirer.select(
        message="What would you like to do?",
        choices=[
            {"name": "Continue to deployment", "value": "continue"},
            {"name": "Back to detection", "value": "back"},
        ],
        default="continue",
    ).execute()

    return action == "continue"
```

## Accessibility Notes

- Clear service descriptions with use cases
- Keyboard navigation for all inputs
- Validation feedback on each field
- Default values pre-populated
- Help text for complex fields
- Screen reader friendly labels

## Design Rationale

This screen balances simplicity with configurability:

1. **Smart Defaults**: Pre-populate from detection results
2. **Guided Choices**: Clear descriptions for each service
3. **Validation**: Prevent invalid configurations
4. **Flexibility**: Allow customization while maintaining safety
5. **Progressive Disclosure**: Only show relevant settings per service
6. **Auto-generation**: Database name from project name reduces cognitive load
