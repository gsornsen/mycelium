# Wizard API Reference

Complete API documentation for the M04 Interactive Onboarding wizard system.

## Table of Contents

- [Module Overview](#module-overview)
- [flow.py](#flowpy)
- [screens.py](#screenspy)
- [validation.py](#validationpy)
- [persistence.py](#persistencepy)
- [Usage Examples](#usage-examples)

## Module Overview

The wizard system consists of four main modules:

| Module           | Purpose                        | Key Classes                               |
| ---------------- | ------------------------------ | ----------------------------------------- |
| `flow.py`        | State machine and flow control | `WizardState`, `WizardFlow`, `WizardStep` |
| `screens.py`     | Interactive UI screens         | `WizardScreens`                           |
| `validation.py`  | Input validation               | `WizardValidator`, `ValidationError`      |
| `persistence.py` | State save/load                | `WizardStatePersistence`                  |

### Module Dependency Graph

```
cli.py
  ├── flow.py (WizardFlow, WizardState)
  ├── screens.py (WizardScreens)
  │   └── detection/orchestrator.py
  ├── validation.py (WizardValidator)
  └── persistence.py (WizardStatePersistence)
```

## flow.py

Core state machine implementation for wizard flow control.

### WizardStep Enum

Enumeration of all wizard steps in order.

```python
class WizardStep(str, Enum):
    """Wizard steps in order."""
    WELCOME = "welcome"
    DETECTION = "detection"
    SERVICES = "services"
    DEPLOYMENT = "deployment"
    ADVANCED = "advanced"
    REVIEW = "review"
    COMPLETE = "complete"
```

**Members**:

- `WELCOME`: Initial welcome screen with setup mode selection
- `DETECTION`: Service detection screen
- `SERVICES`: Service selection and configuration
- `DEPLOYMENT`: Deployment method selection
- `ADVANCED`: Advanced configuration (custom mode only)
- `REVIEW`: Configuration review and confirmation
- `COMPLETE`: Completion screen with next steps

**Usage**:

```python
from mycelium_onboarding.wizard.flow import WizardStep

current_step = WizardStep.WELCOME
if current_step == WizardStep.WELCOME:
    print("Starting wizard")
```

### WizardState Dataclass

Complete wizard state container maintaining all user selections.

```python
@dataclass
class WizardState:
    """Complete wizard state with user selections."""

    # Step tracking
    current_step: WizardStep = WizardStep.WELCOME
    started_at: datetime = field(default_factory=datetime.now)

    # Detection results (from M03)
    detection_results: dict[str, Any] | None = None

    # User selections
    project_name: str = ""
    services_enabled: dict[str, bool] = field(default_factory=dict)
    deployment_method: str = "docker-compose"

    # Service-specific settings
    redis_port: int = 6379
    postgres_port: int = 5432
    postgres_database: str = ""
    temporal_namespace: str = "default"
    temporal_ui_port: int = 8080
    temporal_frontend_port: int = 7233

    # Advanced settings
    auto_start: bool = True
    enable_persistence: bool = True

    # Wizard metadata
    setup_mode: str = "quick"  # "quick" or "custom"
    completed: bool = False
    resumed: bool = False
```

#### Attributes

**Step Tracking**:

- `current_step: WizardStep` - Current wizard step
- `started_at: datetime` - Timestamp when wizard was started

**Detection Results**:

- `detection_results: dict[str, Any] | None` - Results from M03 detection orchestrator

**User Selections**:

- `project_name: str` - User-specified project identifier
- `services_enabled: dict[str, bool]` - Dict mapping service names to enabled status
- `deployment_method: str` - Chosen deployment method (docker-compose, kubernetes, systemd)

**Service-Specific Settings**:

- `redis_port: int` - Redis port configuration (default: 6379)
- `postgres_port: int` - PostgreSQL port configuration (default: 5432)
- `postgres_database: str` - PostgreSQL database name
- `temporal_namespace: str` - Temporal namespace configuration (default: "default")
- `temporal_ui_port: int` - Temporal UI port (default: 8080)
- `temporal_frontend_port: int` - Temporal frontend/gRPC port (default: 7233)

**Advanced Settings**:

- `auto_start: bool` - Whether to auto-start services (default: True)
- `enable_persistence: bool` - Whether to enable data persistence (default: True)

**Wizard Metadata**:

- `setup_mode: str` - Quick or custom setup mode (default: "quick")
- `completed: bool` - Whether wizard is fully completed (default: False)
- `resumed: bool` - Whether this wizard was resumed from saved state (default: False)

#### Methods

##### `can_proceed_to(step: WizardStep) -> bool`

Check if wizard can proceed to given step.

**Parameters**:

- `step: WizardStep` - Target wizard step

**Returns**:

- `bool` - True if prerequisites are met, False otherwise

**Example**:

```python
state = WizardState()
state.detection_results = summary

if state.can_proceed_to(WizardStep.SERVICES):
    print("Can proceed to services")
```

**Prerequisites by Step**:

- `WELCOME`: Always True
- `DETECTION`: Always True
- `SERVICES`: Requires `detection_results` is not None
- `DEPLOYMENT`: Requires `detection_results` is not None
- `ADVANCED`: Requires `detection_results` is not None
- `REVIEW`: Requires `project_name` and at least one service enabled
- `COMPLETE`: Requires `completed` is True

##### `get_next_step() -> WizardStep | None`

Get next step in wizard flow, respecting setup mode.

**Returns**:

- `WizardStep | None` - Next step, or None if at end

**Behavior**:

- In quick mode: Skips `ADVANCED` step (jumps from `DEPLOYMENT` to `REVIEW`)
- In custom mode: Includes all steps
- Returns `None` if at `COMPLETE` step

**Example**:

```python
state = WizardState()
state.setup_mode = "quick"
state.current_step = WizardStep.DEPLOYMENT

next_step = state.get_next_step()
# Returns WizardStep.REVIEW (skips ADVANCED)
```

##### `get_previous_step() -> WizardStep | None`

Get previous step for back navigation.

**Returns**:

- `WizardStep | None` - Previous step, or None if at beginning

**Behavior**:

- Cannot go back from `WELCOME` or `COMPLETE`
- In quick mode: Skips `ADVANCED` when going back from `REVIEW`
- Returns `None` at beginning

**Example**:

```python
state = WizardState()
state.current_step = WizardStep.SERVICES

prev_step = state.get_previous_step()
# Returns WizardStep.DETECTION
```

##### `is_complete() -> bool`

Check if wizard is complete.

**Returns**:

- `bool` - True if at COMPLETE step and marked completed

**Example**:

```python
state = WizardState()
state.current_step = WizardStep.COMPLETE
state.completed = True

if state.is_complete():
    print("Wizard is complete!")
```

##### `to_config() -> MyceliumConfig`

Convert wizard state to MyceliumConfig for saving.

**Returns**:

- `MyceliumConfig` - Configuration built from wizard state

**Raises**:

- `ValueError` - If required fields are missing or invalid

**Behavior**:

- Validates at least one service is enabled
- Sanitizes database name (replaces hyphens with underscores)
- Uses defaults for empty fields

**Example**:

```python
state = WizardState()
state.project_name = "my-project"
state.services_enabled = {"redis": True, "postgres": True, "temporal": False}
state.postgres_database = "my_db"

config = state.to_config()
# Returns MyceliumConfig instance
```

##### `to_dict() -> dict[str, Any]`

Convert wizard state to dictionary for serialization.

**Returns**:

- `dict[str, Any]` - Dictionary representation

**Behavior**:

- Converts `datetime` to ISO format string
- Converts enums to string values
- All fields included

**Example**:

```python
state = WizardState()
state_dict = state.to_dict()
# Returns: {"current_step": "welcome", "started_at": "2025-10-14T...", ...}
```

##### `from_dict(data: dict[str, Any]) -> WizardState` (classmethod)

Create wizard state from dictionary.

**Parameters**:

- `data: dict[str, Any]` - Dictionary containing state data

**Returns**:

- `WizardState` - Deserialized instance

**Raises**:

- `ValueError` - If data format is invalid

**Example**:

```python
data = {"current_step": "services", "project_name": "test"}
state = WizardState.from_dict(data)
```

### WizardFlow Class

Orchestrates wizard flow logic including step transitions and validation.

```python
class WizardFlow:
    """Manages wizard flow logic."""

    def __init__(self, state: WizardState | None = None) -> None:
        """Initialize wizard flow."""
        self.state = state or WizardState()
```

#### Attributes

- `state: WizardState` - Current wizard state

#### Methods

##### `__init__(state: WizardState | None = None)`

Initialize wizard flow.

**Parameters**:

- `state: WizardState | None` - Optional existing state (creates new if None)

**Example**:

```python
# New flow
flow = WizardFlow()

# With existing state
state = WizardState()
flow = WizardFlow(state)
```

##### `advance() -> WizardStep`

Advance to next step with validation.

**Returns**:

- `WizardStep` - Current step after advancement

**Raises**:

- `ValueError` - If cannot advance (at end or prerequisites not met)

**Example**:

```python
flow = WizardFlow()
try:
    next_step = flow.advance()
    print(f"Advanced to {next_step}")
except ValueError as e:
    print(f"Cannot advance: {e}")
```

##### `go_back() -> WizardStep`

Go back to previous step.

**Returns**:

- `WizardStep` - Current step after going back

**Raises**:

- `ValueError` - If cannot go back (at beginning)

**Example**:

```python
flow = WizardFlow()
flow.state.current_step = WizardStep.SERVICES

prev_step = flow.go_back()
# Returns WizardStep.DETECTION
```

##### `jump_to(step: WizardStep) -> WizardStep`

Jump to a specific step (used for editing from review).

**Parameters**:

- `step: WizardStep` - Target step

**Returns**:

- `WizardStep` - Current step after jump

**Raises**:

- `ValueError` - If cannot jump (prerequisites not met)

**Example**:

```python
flow = WizardFlow()
flow.state.current_step = WizardStep.REVIEW

# Jump back to edit services
flow.jump_to(WizardStep.SERVICES)
```

##### `save_state(path: str | Path) -> None`

Save wizard state for resume capability.

**Parameters**:

- `path: str | Path` - File path to save state to

**Example**:

```python
flow = WizardFlow()
flow.save_state("/tmp/wizard_state.json")
```

##### `load_state(path: str | Path) -> WizardFlow` (classmethod)

Load saved wizard state.

**Parameters**:

- `path: str | Path` - File path to load state from

**Returns**:

- `WizardFlow` - Flow instance with loaded state

**Raises**:

- `FileNotFoundError` - If state file doesn't exist
- `ValueError` - If state file is invalid

**Example**:

```python
flow = WizardFlow.load_state("/tmp/wizard_state.json")
print(f"Resumed from {flow.state.current_step}")
```

##### `mark_complete() -> None`

Mark wizard as completed.

**Example**:

```python
flow = WizardFlow()
flow.mark_complete()
assert flow.state.is_complete()
```

## screens.py

Interactive UI screens using InquirerPy and Rich for display.

### WizardScreens Class

All wizard screen implementations with interactive prompts.

```python
class WizardScreens:
    """All wizard screen implementations."""

    def __init__(self, state: WizardState) -> None:
        """Initialize wizard screens with state."""
        self.state = state
```

#### Attributes

- `state: WizardState` - Current wizard state

#### Methods

##### `__init__(state: WizardState)`

Initialize wizard screens.

**Parameters**:

- `state: WizardState` - Wizard state to work with

**Example**:

```python
state = WizardState()
screens = WizardScreens(state)
```

##### `show_welcome() -> str`

Show welcome screen and return setup mode.

**Returns**:

- `str` - Setup mode: "quick" or "custom"

**Raises**:

- `SystemExit` - If user chooses to exit

**UI Elements**:

- Welcome banner with Mycelium description
- Setup mode selection (quick/custom/exit)
- Exit confirmation if selected

**Example**:

```python
screens = WizardScreens(state)
setup_mode = screens.show_welcome()
# Returns "quick" or "custom"
```

##### `show_detection() -> DetectionSummary`

Show detection screen with progress and results.

**Returns**:

- `DetectionSummary` - Detection results

**UI Elements**:

- Progress indicator during detection
- Formatted results table
- Re-run detection option

**Side Effects**:

- Updates `state.detection_results`

**Example**:

```python
screens = WizardScreens(state)
summary = screens.show_detection()
print(f"Detected services: {summary.has_redis}, {summary.has_postgres}")
```

##### `show_services() -> dict[str, bool]`

Show services selection screen.

**Returns**:

- `dict[str, bool]` - Dictionary mapping service names to enabled status

**UI Elements**:

- Multi-select checkbox for services
- Service-specific configuration prompts:
  - PostgreSQL: database name
  - Temporal: namespace

**Validation**:

- At least one service must be selected
- Database name must be alphanumeric with underscores

**Side Effects**:

- Updates `state.services_enabled`
- Updates service-specific settings

**Example**:

```python
screens = WizardScreens(state)
services = screens.show_services()
# Returns: {"redis": True, "postgres": True, "temporal": False}
```

##### `show_deployment() -> str`

Show deployment method selection screen.

**Returns**:

- `str` - Selected deployment method

**UI Elements**:

- Deployment method selection
- Auto-start confirmation

**Options**:

- docker-compose
- kubernetes
- systemd

**Side Effects**:

- Updates `state.deployment_method`
- Updates `state.auto_start`

**Example**:

```python
screens = WizardScreens(state)
deployment = screens.show_deployment()
# Returns: "docker-compose"
```

##### `show_advanced() -> None`

Show advanced configuration screen (Custom mode only).

**Returns**:

- `None`

**UI Elements**:

- Data persistence toggle
- Port configuration for enabled services:
  - Redis port
  - PostgreSQL port

**Validation**:

- Ports must be in range 1024-65535

**Side Effects**:

- Updates `state.enable_persistence`
- Updates service port settings

**Example**:

```python
screens = WizardScreens(state)
state.setup_mode = "custom"
screens.show_advanced()
```

##### `show_review() -> str`

Show review screen with summary and confirmation.

**Returns**:

- `str` - Action: "confirm", "edit:<step>", or "cancel"

**UI Elements**:

- Configuration summary table
- Action selection (confirm/edit/cancel)
- Edit step selection if edit chosen

**Actions**:

- `"confirm"`: Proceed to save configuration
- `"edit:services"`: Jump back to services screen
- `"edit:deployment"`: Jump back to deployment screen
- `"edit:advanced"`: Jump back to advanced screen (if available)
- `"cancel"`: Cancel wizard

**Example**:

```python
screens = WizardScreens(state)
action = screens.show_review()

if action == "confirm":
    # Save configuration
elif action.startswith("edit:"):
    step = action.split(":")[1]
    # Jump to step for editing
```

##### `show_complete(config_path: str) -> None`

Show completion screen with success message.

**Parameters**:

- `config_path: str` - Path to saved configuration

**Returns**:

- `None`

**UI Elements**:

- Success banner
- Configuration file path
- Next steps instructions

**Example**:

```python
screens = WizardScreens(state)
screens.show_complete("/home/user/.config/mycelium/config.yaml")
```

## validation.py

Comprehensive input validation ensuring data integrity.

### ValidationError Dataclass

Container for validation errors.

```python
@dataclass
class ValidationError:
    """Validation error with field and message."""
    field: str
    message: str
    severity: str = "error"  # "error" or "warning"
```

#### Attributes

- `field: str` - Name of field that failed validation
- `message: str` - Human-readable error message
- `severity: str` - Error severity ("error" or "warning")

#### Methods

##### `__str__() -> str`

Format error for display.

**Returns**:

- `str` - Formatted error message

**Example**:

```python
error = ValidationError("project_name", "Cannot be empty")
print(error)  # Outputs: "project_name: Cannot be empty"
```

### WizardValidator Class

Validates wizard state and user inputs.

```python
class WizardValidator:
    """Validates wizard state and user inputs."""

    def __init__(self, state: WizardState) -> None:
        """Initialize validator with wizard state."""
        self.state = state
        self.errors: list[ValidationError] = []
```

#### Attributes

- `state: WizardState` - Wizard state to validate
- `errors: list[ValidationError]` - List of validation errors found

#### Methods

##### `__init__(state: WizardState)`

Initialize validator.

**Parameters**:

- `state: WizardState` - State to validate

**Example**:

```python
state = WizardState()
validator = WizardValidator(state)
```

##### `validate_project_name(name: str) -> bool`

Validate project name format.

**Parameters**:

- `name: str` - Project name to validate

**Returns**:

- `bool` - True if valid, False otherwise

**Rules**:

- Cannot be empty
- Must contain only alphanumeric, hyphens, underscores
- Maximum 100 characters

**Example**:

```python
validator = WizardValidator(state)
if not validator.validate_project_name("my-project"):
    print(validator.get_error_messages())
```

##### `validate_services() -> bool`

Validate at least one service is selected.

**Returns**:

- `bool` - True if at least one service enabled

**Example**:

```python
validator = WizardValidator(state)
if not validator.validate_services():
    print("No services enabled!")
```

##### `validate_postgres_database(db_name: str) -> bool`

Validate PostgreSQL database name.

**Parameters**:

- `db_name: str` - Database name to validate

**Returns**:

- `bool` - True if valid

**Rules**:

- Cannot be empty
- Must start with a letter
- Only alphanumeric and underscores (no hyphens)
- Maximum 63 characters

**Example**:

```python
validator = WizardValidator(state)
if not validator.validate_postgres_database("my_db"):
    print("Invalid database name")
```

##### `validate_port(port: int, service: str) -> bool`

Validate port number range.

**Parameters**:

- `port: int` - Port number
- `service: str` - Service name for error message

**Returns**:

- `bool` - True if valid

**Rules**:

- Must be between 1024 and 65535 (non-privileged range)

**Example**:

```python
validator = WizardValidator(state)
if not validator.validate_port(6379, "redis"):
    print("Invalid port")
```

##### `validate_deployment_method(method: str) -> bool`

Validate deployment method is supported.

**Parameters**:

- `method: str` - Deployment method

**Returns**:

- `bool` - True if valid

**Valid Methods**:

- docker-compose
- kubernetes
- systemd
- manual

**Example**:

```python
validator = WizardValidator(state)
if not validator.validate_deployment_method("docker-compose"):
    print("Invalid deployment method")
```

##### `validate_temporal_namespace(namespace: str) -> bool`

Validate Temporal namespace format.

**Parameters**:

- `namespace: str` - Namespace to validate

**Returns**:

- `bool` - True if valid

**Rules**:

- Cannot be empty
- Alphanumeric, hyphens, underscores only
- Maximum 255 characters

**Example**:

```python
validator = WizardValidator(state)
if not validator.validate_temporal_namespace("production"):
    print("Invalid namespace")
```

##### `validate_port_conflicts() -> bool`

Validate that no ports conflict.

**Returns**:

- `bool` - True if no conflicts

**Checks**:

- Redis, PostgreSQL, Temporal UI, Temporal frontend ports
- Ensures each port is unique

**Example**:

```python
validator = WizardValidator(state)
if not validator.validate_port_conflicts():
    print("Port conflicts detected!")
```

##### `validate_state() -> bool`

Validate complete wizard state.

**Returns**:

- `bool` - True if all validations pass

**Performs**:

- All individual validations
- Comprehensive state check
- Populates `self.errors` list

**Example**:

```python
validator = WizardValidator(state)
if not validator.validate_state():
    for error in validator.get_errors():
        print(f"{error.field}: {error.message}")
```

##### `get_errors() -> list[ValidationError]`

Get all validation errors.

**Returns**:

- `list[ValidationError]` - List of errors

**Example**:

```python
validator = WizardValidator(state)
validator.validate_state()
errors = validator.get_errors()
```

##### `get_error_messages() -> list[str]`

Get formatted error messages.

**Returns**:

- `list[str]` - Formatted error messages

**Example**:

```python
validator = WizardValidator(state)
validator.validate_state()
for msg in validator.get_error_messages():
    print(msg)
```

##### `has_errors() -> bool`

Check if there are any validation errors.

**Returns**:

- `bool` - True if errors exist

**Example**:

```python
validator = WizardValidator(state)
validator.validate_state()
if validator.has_errors():
    print("Validation failed!")
```

## persistence.py

State persistence for resume functionality with atomic writes.

### PersistenceError Exception

Exception raised when persistence operations fail.

```python
class PersistenceError(Exception):
    """Raised when state persistence operations fail."""
    pass
```

### WizardStatePersistence Class

Manages saving and loading wizard state.

```python
class WizardStatePersistence:
    """Manages saving and loading wizard state."""

    def __init__(self, state_dir: Path | None = None) -> None:
        """Initialize persistence manager."""
        self.state_dir = state_dir or get_state_dir()
        self.state_file = self.state_dir / "wizard_state.json"
```

#### Attributes

- `state_dir: Path` - Directory where state files are stored
- `state_file: Path` - Path to wizard state file

#### Methods

##### `__init__(state_dir: Path | None = None)`

Initialize persistence manager.

**Parameters**:

- `state_dir: Path | None` - Optional state directory (uses XDG_STATE_HOME if None)

**Example**:

```python
# Use default XDG location
persistence = WizardStatePersistence()

# Use custom location
persistence = WizardStatePersistence(state_dir=Path("/tmp/state"))
```

##### `save(state: WizardState) -> None`

Save wizard state to disk with atomic write.

**Parameters**:

- `state: WizardState` - State to save

**Raises**:

- `PersistenceError` - If save operation fails

**Behavior**:

- Creates state directory if needed
- Uses atomic write (temp file + rename)
- Prevents corruption on interrupt

**Example**:

```python
persistence = WizardStatePersistence()
state = WizardState()
persistence.save(state)
```

##### `load() -> WizardState | None`

Load wizard state from disk.

**Returns**:

- `WizardState | None` - Loaded state or None if not found/corrupted

**Behavior**:

- Returns None if file doesn't exist
- Returns None if file is corrupted
- Marks state as resumed

**Example**:

```python
persistence = WizardStatePersistence()
state = persistence.load()
if state:
    print(f"Resuming from {state.current_step}")
```

##### `clear() -> None`

Clear saved wizard state.

**Raises**:

- `PersistenceError` - If clear operation fails

**Example**:

```python
persistence = WizardStatePersistence()
persistence.clear()
```

##### `exists() -> bool`

Check if saved state exists.

**Returns**:

- `bool` - True if state file exists

**Example**:

```python
persistence = WizardStatePersistence()
if persistence.exists():
    print("Saved state found")
```

##### `get_state_path() -> Path`

Get path to state file.

**Returns**:

- `Path` - Path to wizard state file

**Example**:

```python
persistence = WizardStatePersistence()
path = persistence.get_state_path()
print(f"State file: {path}")
```

##### `backup() -> Path | None`

Create backup of current state.

**Returns**:

- `Path | None` - Path to backup file or None if no state exists

**Raises**:

- `PersistenceError` - If backup operation fails

**Example**:

```python
persistence = WizardStatePersistence()
backup_path = persistence.backup()
if backup_path:
    print(f"Backed up to {backup_path}")
```

##### `restore_from_backup(backup_path: Path) -> None`

Restore state from backup file.

**Parameters**:

- `backup_path: Path` - Path to backup file

**Raises**:

- `PersistenceError` - If restore operation fails
- `FileNotFoundError` - If backup doesn't exist

**Example**:

```python
persistence = WizardStatePersistence()
persistence.restore_from_backup(Path("/tmp/backup.json"))
```

## Usage Examples

### Basic Wizard Flow

```python
from mycelium_onboarding.wizard.flow import WizardFlow, WizardState, WizardStep
from mycelium_onboarding.wizard.screens import WizardScreens
from mycelium_onboarding.wizard.validation import WizardValidator
from mycelium_onboarding.wizard.persistence import WizardStatePersistence

# Initialize
state = WizardState()
flow = WizardFlow(state)
screens = WizardScreens(state)
validator = WizardValidator(state)
persistence = WizardStatePersistence()

# Main wizard loop
while not state.is_complete():
    # Save state for resume
    persistence.save(state)

    current_step = state.current_step

    if current_step == WizardStep.WELCOME:
        setup_mode = screens.show_welcome()
        state.setup_mode = setup_mode
        flow.advance()

    elif current_step == WizardStep.DETECTION:
        summary = screens.show_detection()
        flow.advance()

    elif current_step == WizardStep.SERVICES:
        services = screens.show_services()
        flow.advance()

    elif current_step == WizardStep.REVIEW:
        action = screens.show_review()
        if action == "confirm":
            if validator.validate_state():
                config = state.to_config()
                # Save config
                flow.mark_complete()
        elif action.startswith("edit:"):
            step = action.split(":")[1]
            flow.jump_to(WizardStep(step))

# Clear saved state on completion
persistence.clear()
```

### Resume Wizard

```python
from mycelium_onboarding.wizard.persistence import WizardStatePersistence

persistence = WizardStatePersistence()

if persistence.exists():
    state = persistence.load()
    if state:
        print(f"Resuming from {state.current_step}")
        # Continue wizard with loaded state
    else:
        print("Saved state corrupted, starting fresh")
        state = WizardState()
else:
    state = WizardState()
```

### Custom Validation

```python
from mycelium_onboarding.wizard.validation import WizardValidator, ValidationError

validator = WizardValidator(state)

# Validate specific fields
if not validator.validate_project_name(state.project_name):
    print("Invalid project name")

# Validate port range
if not validator.validate_port(state.redis_port, "redis"):
    print("Invalid Redis port")

# Comprehensive validation
if not validator.validate_state():
    for error in validator.get_errors():
        print(f"Error in {error.field}: {error.message}")
```

### Programmatic State Building

```python
from mycelium_onboarding.wizard.flow import WizardState

# Build state programmatically
state = WizardState()
state.project_name = "my-project"
state.setup_mode = "quick"
state.services_enabled = {
    "redis": True,
    "postgres": True,
    "temporal": False,
}
state.deployment_method = "docker-compose"
state.postgres_database = "my_db"
state.auto_start = True

# Convert to config
config = state.to_config()

# Save config
from mycelium_onboarding.config.manager import ConfigManager
manager = ConfigManager()
manager.save(config)
```

### State Serialization

```python
from mycelium_onboarding.wizard.flow import WizardState

# Serialize to dict
state = WizardState()
state_dict = state.to_dict()

# Save to JSON
import json
with open("state.json", "w") as f:
    json.dump(state_dict, f)

# Load from dict
with open("state.json") as f:
    loaded_dict = json.load(f)
loaded_state = WizardState.from_dict(loaded_dict)
```

______________________________________________________________________

**Last Updated**: 2025-10-14 **Version**: M04 (Interactive Onboarding)
