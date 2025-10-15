# Wizard Integration Guide

Guide for integrating the wizard into applications, extending functionality, and programmatic usage.

## Table of Contents

- [Overview](#overview)
- [Programmatic Usage](#programmatic-usage)
- [Extending the Wizard](#extending-the-wizard)
- [Testing Wizard Interactions](#testing-wizard-interactions)
- [Custom Deployment Methods](#custom-deployment-methods)
- [Best Practices](#best-practices)
- [Advanced Integration Patterns](#advanced-integration-patterns)

## Overview

The M04 Interactive Onboarding wizard is designed to be:

- **Modular**: Each component can be used independently
- **Extensible**: Easy to add new screens, validators, or deployment methods
- **Testable**: Mock-friendly architecture for comprehensive testing
- **Embeddable**: Can be integrated into larger applications

### Architecture Overview

```
┌─────────────────────────────────────────────────┐
│              CLI Interface (cli.py)             │
└──────────────────┬──────────────────────────────┘
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
  ┌─────────┐ ┌─────────┐ ┌──────────┐
  │  Flow   │ │ Screens │ │Validator │
  │ Control │ │   UI    │ │  Logic   │
  └────┬────┘ └────┬────┘ └────┬─────┘
       │           │           │
       └───────────┼───────────┘
                   │
            ┌──────┴──────┐
            │ WizardState │
            └─────────────┘
```

## Programmatic Usage

### Basic Wizard Execution

Use the wizard programmatically without the CLI:

```python
from mycelium_onboarding.wizard.flow import WizardFlow, WizardState, WizardStep
from mycelium_onboarding.wizard.screens import WizardScreens
from mycelium_onboarding.wizard.validation import WizardValidator
from mycelium_onboarding.wizard.persistence import WizardStatePersistence
from mycelium_onboarding.config.manager import ConfigManager

def run_wizard_programmatically():
    """Run the wizard programmatically."""
    # Initialize components
    state = WizardState()
    flow = WizardFlow(state)
    screens = WizardScreens(state)
    validator = WizardValidator(state)
    persistence = WizardStatePersistence()

    try:
        # Check for saved state
        if persistence.exists():
            state = persistence.load()
            if state:
                flow = WizardFlow(state)
                screens = WizardScreens(state)
                validator = WizardValidator(state)
                print(f"Resuming from {state.current_step}")

        # Main wizard loop
        while not state.is_complete():
            # Persist state
            persistence.save(state)

            # Execute current step
            current_step = state.current_step

            if current_step == WizardStep.WELCOME:
                setup_mode = screens.show_welcome()
                state.setup_mode = setup_mode
                flow.advance()

            elif current_step == WizardStep.DETECTION:
                summary = screens.show_detection()
                state.detection_results = summary
                flow.advance()

            elif current_step == WizardStep.SERVICES:
                # Prompt for project name if not set
                if not state.project_name:
                    state.project_name = input("Project name: ").strip()

                services = screens.show_services()
                state.services_enabled = services
                flow.advance()

            elif current_step == WizardStep.DEPLOYMENT:
                deployment = screens.show_deployment()
                state.deployment_method = deployment

                # Handle mode-specific flow
                if state.setup_mode == "quick":
                    state.current_step = WizardStep.REVIEW
                else:
                    flow.advance()

            elif current_step == WizardStep.ADVANCED:
                screens.show_advanced()
                flow.advance()

            elif current_step == WizardStep.REVIEW:
                action = screens.show_review()

                if action == "confirm":
                    # Validate before saving
                    if not validator.validate_state():
                        print("Validation errors:")
                        for error in validator.get_error_messages():
                            print(f"  - {error}")
                        continue

                    # Generate and save configuration
                    config = state.to_config()
                    manager = ConfigManager()
                    manager.save(config)

                    # Mark complete
                    state.completed = True
                    state.current_step = WizardStep.COMPLETE
                    flow.advance()

                elif action.startswith("edit:"):
                    # Jump to step for editing
                    edit_step = action.split(":")[1]
                    state.current_step = WizardStep(edit_step)

                elif action == "cancel":
                    print("Wizard cancelled")
                    return None

            elif current_step == WizardStep.COMPLETE:
                config_path = manager._determine_save_path()
                screens.show_complete(str(config_path))
                break

        # Clear saved state on success
        persistence.clear()
        return state

    except KeyboardInterrupt:
        print("\nWizard interrupted. Run again with resume.")
        persistence.save(state)
        return None
    except Exception as e:
        print(f"Error: {e}")
        persistence.save(state)
        raise

# Usage
if __name__ == "__main__":
    final_state = run_wizard_programmatically()
    if final_state:
        print(f"Wizard completed! Project: {final_state.project_name}")
```

### Non-Interactive State Building

Build wizard state without user interaction:

```python
from mycelium_onboarding.wizard.flow import WizardState
from mycelium_onboarding.wizard.validation import WizardValidator
from mycelium_onboarding.config.manager import ConfigManager

def create_config_from_template(template_name: str):
    """Create configuration from predefined template."""
    # Define templates
    templates = {
        "minimal": {
            "project_name": "minimal-project",
            "services": {"redis": True, "postgres": False, "temporal": False},
            "deployment": "docker-compose",
        },
        "full-stack": {
            "project_name": "full-stack-project",
            "services": {"redis": True, "postgres": True, "temporal": True},
            "deployment": "kubernetes",
            "postgres_database": "fullstack_db",
            "temporal_namespace": "production",
        },
        "development": {
            "project_name": "dev-project",
            "services": {"redis": True, "postgres": True, "temporal": False},
            "deployment": "docker-compose",
            "postgres_database": "dev_db",
            "auto_start": False,
        },
    }

    if template_name not in templates:
        raise ValueError(f"Unknown template: {template_name}")

    template = templates[template_name]

    # Build state
    state = WizardState()
    state.project_name = template["project_name"]
    state.services_enabled = template["services"]
    state.deployment_method = template["deployment"]

    if "postgres_database" in template:
        state.postgres_database = template["postgres_database"]
    if "temporal_namespace" in template:
        state.temporal_namespace = template["temporal_namespace"]
    if "auto_start" in template:
        state.auto_start = template["auto_start"]

    # Validate
    validator = WizardValidator(state)
    if not validator.validate_state():
        raise ValueError(f"Invalid template: {validator.get_error_messages()}")

    # Convert to config
    config = state.to_config()

    # Save
    manager = ConfigManager()
    manager.save(config)

    return config

# Usage
config = create_config_from_template("full-stack")
print(f"Created config: {config.project_name}")
```

### Headless Wizard (No User Input)

Run wizard with predetermined answers:

```python
from mycelium_onboarding.wizard.flow import WizardState, WizardStep
from mycelium_onboarding.wizard.validation import WizardValidator

def headless_wizard(answers: dict):
    """Run wizard with predefined answers (for CI/CD)."""
    state = WizardState()

    # Apply answers
    state.project_name = answers.get("project_name", "mycelium-project")
    state.setup_mode = answers.get("setup_mode", "quick")
    state.services_enabled = answers.get("services", {
        "redis": True,
        "postgres": True,
        "temporal": False,
    })
    state.deployment_method = answers.get("deployment", "docker-compose")
    state.postgres_database = answers.get("postgres_database", "mycelium")
    state.auto_start = answers.get("auto_start", True)
    state.enable_persistence = answers.get("enable_persistence", True)

    # Advanced settings
    if "redis_port" in answers:
        state.redis_port = answers["redis_port"]
    if "postgres_port" in answers:
        state.postgres_port = answers["postgres_port"]

    # Validate
    validator = WizardValidator(state)
    if not validator.validate_state():
        raise ValueError(f"Invalid configuration: {validator.get_error_messages()}")

    # Convert and return
    return state.to_config()

# Usage in CI/CD
answers = {
    "project_name": "ci-test-project",
    "services": {"redis": True, "postgres": False, "temporal": False},
    "deployment": "systemd",
}

config = headless_wizard(answers)
```

## Extending the Wizard

### Adding a New Screen

Add a custom screen for additional configuration:

```python
from mycelium_onboarding.wizard.screens import WizardScreens
from mycelium_onboarding.wizard.flow import WizardStep
from InquirerPy import inquirer
from rich.console import Console

console = Console()

class ExtendedWizardScreens(WizardScreens):
    """Extended wizard screens with custom functionality."""

    def show_monitoring(self) -> dict[str, any]:
        """Show custom monitoring configuration screen."""
        console.print("\n[bold]Monitoring Configuration[/bold]\n")

        # Monitoring provider selection
        provider = inquirer.select(
            message="Select monitoring provider:",
            choices=[
                {"value": "prometheus", "name": "Prometheus + Grafana"},
                {"value": "datadog", "name": "Datadog"},
                {"value": "none", "name": "No monitoring"},
            ],
            default="prometheus",
        ).execute()

        config = {"provider": provider}

        if provider == "prometheus":
            # Prometheus-specific config
            port = inquirer.number(
                message="Prometheus port:",
                default=9090,
                min_allowed=1024,
                max_allowed=65535,
            ).execute()
            config["prometheus_port"] = port

        elif provider == "datadog":
            # Datadog-specific config
            api_key = inquirer.secret(
                message="Datadog API key:",
            ).execute()
            config["datadog_api_key"] = api_key

        return config

# Usage
state = WizardState()
screens = ExtendedWizardScreens(state)
monitoring_config = screens.show_monitoring()
```

### Adding Custom Validation

Extend validation with custom rules:

```python
from mycelium_onboarding.wizard.validation import WizardValidator, ValidationError

class ExtendedWizardValidator(WizardValidator):
    """Extended validator with custom rules."""

    def validate_custom_naming_convention(self, name: str) -> bool:
        """Validate project name follows company naming convention."""
        # Example: Must start with "proj-" or "svc-"
        valid_prefixes = ["proj-", "svc-"]

        if not any(name.startswith(prefix) for prefix in valid_prefixes):
            self.errors.append(
                ValidationError(
                    field="project_name",
                    message=f"Project name must start with one of: {', '.join(valid_prefixes)}",
                    severity="error",
                )
            )
            return False
        return True

    def validate_production_requirements(self) -> bool:
        """Validate production deployment requirements."""
        if self.state.deployment_method == "kubernetes":
            # Require persistence for production
            if not self.state.enable_persistence:
                self.errors.append(
                    ValidationError(
                        field="enable_persistence",
                        message="Persistence must be enabled for Kubernetes deployment",
                        severity="error",
                    )
                )
                return False
        return True

    def validate_state(self) -> bool:
        """Override to include custom validations."""
        # Run base validations
        if not super().validate_state():
            return False

        # Add custom validations
        if self.state.project_name:
            self.validate_custom_naming_convention(self.state.project_name)

        self.validate_production_requirements()

        return len(self.errors) == 0

# Usage
state = WizardState()
state.project_name = "proj-myapp"
validator = ExtendedWizardValidator(state)
if validator.validate_state():
    print("Validation passed!")
```

### Custom Persistence Backend

Implement custom state persistence:

```python
from mycelium_onboarding.wizard.persistence import WizardStatePersistence
from mycelium_onboarding.wizard.flow import WizardState
import redis
import pickle

class RedisWizardPersistence(WizardStatePersistence):
    """Persist wizard state in Redis."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize Redis persistence."""
        self.redis_client = redis.from_url(redis_url)
        self.state_key = "mycelium:wizard:state"

    def save(self, state: WizardState) -> None:
        """Save state to Redis."""
        state_bytes = pickle.dumps(state)
        self.redis_client.set(self.state_key, state_bytes)
        # Set TTL: expire after 24 hours
        self.redis_client.expire(self.state_key, 86400)

    def load(self) -> WizardState | None:
        """Load state from Redis."""
        state_bytes = self.redis_client.get(self.state_key)
        if state_bytes:
            return pickle.loads(state_bytes)
        return None

    def clear(self) -> None:
        """Clear state from Redis."""
        self.redis_client.delete(self.state_key)

    def exists(self) -> bool:
        """Check if state exists in Redis."""
        return self.redis_client.exists(self.state_key) > 0

# Usage
persistence = RedisWizardPersistence()
state = WizardState()
persistence.save(state)
```

## Testing Wizard Interactions

### Mocking User Input

Test wizard flows with mocked prompts:

```python
import pytest
from unittest.mock import MagicMock, patch
from mycelium_onboarding.wizard.screens import WizardScreens
from mycelium_onboarding.wizard.flow import WizardState

def test_services_screen_with_mocks():
    """Test services screen with mocked InquirerPy."""
    state = WizardState()
    screens = WizardScreens(state)

    # Mock InquirerPy
    with patch("mycelium_onboarding.wizard.screens.inquirer") as mock_inquirer:
        # Mock checkbox for service selection
        mock_inquirer.checkbox.return_value = MagicMock(
            execute=lambda: ["redis", "postgres"]
        )

        # Mock text input for database name
        mock_inquirer.text.return_value = MagicMock(
            execute=lambda: "test_db"
        )

        # Execute
        services = screens.show_services()

        # Assert
        assert services == {"redis": True, "postgres": True, "temporal": False}
        assert state.postgres_database == "test_db"

def test_wizard_flow_with_mock_detection():
    """Test complete wizard flow with mocked detection."""
    from mycelium_onboarding.detection.orchestrator import DetectionSummary
    from mycelium_onboarding.wizard.flow import WizardFlow
    from unittest.mock import Mock

    # Create mock detection
    mock_detection = Mock(spec=DetectionSummary)
    mock_detection.has_docker = True
    mock_detection.has_redis = True
    mock_detection.has_postgres = False

    # Create state
    state = WizardState()
    state.detection_results = mock_detection

    flow = WizardFlow(state)

    # Test flow can proceed with detection
    assert state.can_proceed_to(WizardStep.SERVICES)
```

### Integration Test Example

Complete integration test for wizard:

```python
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from pathlib import Path

from mycelium_onboarding.cli import cli
from mycelium_onboarding.wizard.flow import WizardState

def test_wizard_quick_mode_e2e(tmp_path: Path):
    """End-to-end test for quick mode wizard."""
    runner = CliRunner()

    with patch("mycelium_onboarding.wizard.persistence.WizardStatePersistence") as mock_pers:
        # Setup persistence mock
        mock_persistence = MagicMock()
        mock_persistence.exists.return_value = False
        mock_pers.return_value = mock_persistence

        # Mock all prompts
        with patch("mycelium_onboarding.wizard.screens.inquirer") as mock_inquirer:
            mock_inquirer.select.side_effect = [
                MagicMock(execute=lambda: "quick"),  # Setup mode
                MagicMock(execute=lambda: "docker-compose"),  # Deployment
                MagicMock(execute=lambda: "confirm"),  # Review
            ]

            mock_inquirer.confirm.side_effect = [
                MagicMock(execute=lambda: False),  # Don't re-run detection
                MagicMock(execute=lambda: True),  # Auto-start
            ]

            mock_inquirer.checkbox.return_value = MagicMock(
                execute=lambda: ["redis", "postgres"]
            )

            mock_inquirer.text.return_value = MagicMock(
                execute=lambda: "test_db"
            )

            # Mock detection
            with patch("mycelium_onboarding.wizard.screens.detect_all") as mock_detect:
                mock_detect.return_value = Mock()

                # Mock config manager
                with patch("mycelium_onboarding.config.manager.ConfigManager") as mock_cfg:
                    mock_config = MagicMock()
                    mock_config._determine_save_path.return_value = tmp_path / "config.yaml"
                    mock_cfg.return_value = mock_config

                    # Mock project name prompt
                    with patch("click.prompt", return_value="test-project"):
                        # Execute wizard
                        result = runner.invoke(cli, ["init", "--no-resume"])

                    # Verify
                    assert result.exit_code == 0
                    mock_config.save.assert_called_once()
```

## Custom Deployment Methods

### Adding a New Deployment Method

Extend deployment options:

```python
from mycelium_onboarding.config.schema import DeploymentMethod
from enum import Enum

# Extend DeploymentMethod enum (in config/schema.py)
class ExtendedDeploymentMethod(str, Enum):
    """Extended deployment methods."""
    DOCKER_COMPOSE = "docker-compose"
    KUBERNETES = "kubernetes"
    SYSTEMD = "systemd"
    MANUAL = "manual"
    NOMAD = "nomad"  # New method
    DOCKER_SWARM = "docker-swarm"  # New method

# Add to validator
def validate_deployment_method_extended(method: str) -> bool:
    """Validate extended deployment methods."""
    valid = [m.value for m in ExtendedDeploymentMethod]
    return method in valid

# Update screens to show new options
def show_extended_deployment(self) -> str:
    """Show deployment screen with extended options."""
    choices = [
        {"value": "docker-compose", "name": "Docker Compose"},
        {"value": "kubernetes", "name": "Kubernetes"},
        {"value": "systemd", "name": "systemd"},
        {"value": "nomad", "name": "HashiCorp Nomad"},
        {"value": "docker-swarm", "name": "Docker Swarm"},
    ]

    deployment = inquirer.select(
        message="Select deployment method:",
        choices=choices,
    ).execute()

    return deployment
```

## Best Practices

### 1. State Management

**DO**:
```python
# Always save state before potentially failing operations
persistence.save(state)
try:
    risky_operation()
except Exception:
    # State is already saved for resume
    raise
```

**DON'T**:
```python
# Don't modify state without validation
state.postgres_database = user_input  # Could be invalid!

# DO validate first
validator = WizardValidator(state)
if validator.validate_postgres_database(user_input):
    state.postgres_database = user_input
```

### 2. Error Handling

**DO**:
```python
# Provide helpful error messages
try:
    config = state.to_config()
except ValueError as e:
    print(f"Configuration error: {e}")
    print("Please check your settings and try again.")
    # Keep state for retry
```

**DON'T**:
```python
# Don't silently fail
try:
    config = state.to_config()
except ValueError:
    pass  # User has no idea what went wrong!
```

### 3. User Experience

**DO**:
```python
# Provide defaults based on context
default_db = state.project_name.lower().replace("-", "_")
db_name = inquirer.text(
    message="Database name:",
    default=default_db,
).execute()
```

**DON'T**:
```python
# Don't make users type everything
db_name = inquirer.text(
    message="Database name:",
    # No default - forces manual input
).execute()
```

### 4. Testing

**DO**:
```python
# Test with realistic mock data
mock_detection = Mock(spec=DetectionSummary)
mock_detection.has_docker = True
mock_detection.docker = Mock(version="24.0.0")

# Test error paths
def test_validation_failure():
    state = WizardState()
    state.project_name = ""  # Invalid
    validator = WizardValidator(state)
    assert not validator.validate_state()
```

**DON'T**:
```python
# Don't only test happy paths
def test_wizard():
    # Only tests successful completion
    assert wizard_completes_successfully()
```

### 5. Documentation

**DO**:
```python
def custom_screen(self) -> dict:
    """Show custom configuration screen.

    Returns:
        dict: Configuration with keys:
            - option1 (str): Description
            - option2 (bool): Description

    Example:
        >>> screens = CustomScreens(state)
        >>> config = screens.custom_screen()
        >>> print(config["option1"])
    """
```

### 6. Backward Compatibility

**DO**:
```python
# Handle old state format gracefully
def _deserialize_state(self, data: dict) -> WizardState:
    # Provide defaults for new fields
    auto_start = data.get("auto_start", True)  # Default if missing
    enable_persistence = data.get("enable_persistence", True)
```

## Advanced Integration Patterns

### Pattern 1: Wizard as a Service

Expose wizard as a web service:

```python
from fastapi import FastAPI, WebSocket
from mycelium_onboarding.wizard.flow import WizardState, WizardFlow

app = FastAPI()

# Store active wizard sessions
sessions = {}

@app.websocket("/ws/wizard/{session_id}")
async def wizard_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for interactive wizard."""
    await websocket.accept()

    # Create or resume session
    if session_id in sessions:
        state = sessions[session_id]
    else:
        state = WizardState()
        sessions[session_id] = state

    flow = WizardFlow(state)

    try:
        while not state.is_complete():
            # Send current step info
            await websocket.send_json({
                "step": state.current_step.value,
                "state": state.to_dict(),
            })

            # Receive user input
            data = await websocket.receive_json()

            # Process input based on current step
            # ... handle step logic ...

            # Advance
            flow.advance()

        # Send completion
        await websocket.send_json({"status": "complete"})

    except WebSocketDisconnect:
        # Save state for resume
        pass
```

### Pattern 2: Wizard Orchestration

Orchestrate multiple wizards:

```python
from mycelium_onboarding.wizard.flow import WizardState

class WizardOrchestrator:
    """Orchestrate multiple related wizards."""

    def __init__(self):
        self.wizards = {}

    def run_sequential_wizards(self, wizard_specs: list[dict]):
        """Run multiple wizards in sequence, passing state."""
        results = []

        for spec in wizard_specs:
            wizard_type = spec["type"]
            state = self.create_wizard_state(wizard_type)

            # Pass data from previous wizard
            if results:
                self.apply_previous_results(state, results[-1])

            # Run wizard
            result = self.run_wizard(state)
            results.append(result)

        return results

    def create_wizard_state(self, wizard_type: str) -> WizardState:
        """Create wizard state based on type."""
        # Factory pattern for different wizard types
        pass

    def apply_previous_results(self, state: WizardState, previous: dict):
        """Apply results from previous wizard to current state."""
        # Data flow between wizards
        pass
```

### Pattern 3: Plugin System

Create a plugin system for wizard extensions:

```python
from abc import ABC, abstractmethod

class WizardPlugin(ABC):
    """Base class for wizard plugins."""

    @abstractmethod
    def get_screen_name(self) -> str:
        """Get plugin screen name."""
        pass

    @abstractmethod
    def show_screen(self, state: WizardState) -> dict:
        """Show plugin screen and return data."""
        pass

    @abstractmethod
    def validate(self, state: WizardState) -> list[ValidationError]:
        """Validate plugin-specific state."""
        pass

class MonitoringPlugin(WizardPlugin):
    """Plugin for monitoring configuration."""

    def get_screen_name(self) -> str:
        return "monitoring"

    def show_screen(self, state: WizardState) -> dict:
        # Show monitoring configuration screen
        return {"provider": "prometheus", "port": 9090}

    def validate(self, state: WizardState) -> list[ValidationError]:
        # Validate monitoring settings
        return []

# Plugin registry
class WizardPluginRegistry:
    def __init__(self):
        self.plugins = {}

    def register(self, plugin: WizardPlugin):
        self.plugins[plugin.get_screen_name()] = plugin

    def get_plugin(self, name: str) -> WizardPlugin:
        return self.plugins.get(name)

# Usage
registry = WizardPluginRegistry()
registry.register(MonitoringPlugin())
```

## Resources

- [Wizard Guide](./wizard-guide.md) - User documentation
- [API Reference](./wizard-reference.md) - Complete API docs
- [Testing Guide](./testing.md) - Testing best practices
- [Configuration Schema](./config-schema.md) - Config format details

---

**Last Updated**: 2025-10-14
**Version**: M04 (Interactive Onboarding)
