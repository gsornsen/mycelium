# M04: Interactive Onboarding

## Overview

**Duration**: 3 days **Dependencies**: M01 (environment isolation), M02 (configuration system), M03 (service detection)
**Blocks**: M05 (deployment generation) **Lead Agent**: python-pro **Support Agents**: devops-engineer,
claude-code-developer

## Why This Milestone

The interactive onboarding wizard is the primary user touchpoint for Mycelium setup. It transforms detected
infrastructure into user-friendly choices, guides deployment method selection, and captures configuration in a type-safe
manner. This milestone bridges technical detection (M03) with automated deployment (M05), making complex distributed
system setup accessible to users of all skill levels.

A well-designed wizard:

- Reduces cognitive load through progressive disclosure
- Provides intelligent defaults based on detection results
- Offers clear explanations for each decision point
- Validates inputs before proceeding
- Allows review and modification before finalizing

## Requirements

### Functional Requirements (FR)

- **FR-4.1**: CLI wizard using InquirerPy with clear prompts and help text
- **FR-4.2**: Service selection interface presenting detected services with recommendations
- **FR-4.3**: Deployment method chooser (Docker Compose recommended, Justfile for bare-metal)
- **FR-4.4**: Configuration preview showing final selections before writing
- **FR-4.5**: Support for graceful exit at any point without partial writes
- **FR-4.6**: Resume support for interrupted onboarding sessions

### Technical Requirements (TR)

- **TR-4.1**: Integration with M03 DetectionResults for intelligent defaults
- **TR-4.2**: Integration with M02 ConfigManager for configuration persistence
- **TR-4.3**: Input validation using Pydantic validators from M02 schema
- **TR-4.4**: Colorized terminal output with rich formatting
- **TR-4.5**: Non-interactive mode support via CLI flags (for CI/CD)

### Integration Requirements (IR)

- **IR-4.1**: Read detection results from M03 orchestrator cache
- **IR-4.2**: Write final configuration using M02 ConfigManager.save()
- **IR-4.3**: Respect M01 environment isolation (XDG directories)
- **IR-4.4**: Integrate as `/mycelium-onboarding` slash command

### Compliance Requirements (CR)

- **CR-4.1**: Accessibility - keyboard-only navigation, screen reader friendly prompts
- **CR-4.2**: UX - consistent terminology, clear error messages, contextual help
- **CR-4.3**: Security - validate all inputs, sanitize file paths, no credential exposure

## Tasks

### Task 4.1: Design Wizard Flow and UX

**Agent**: python-pro (lead), devops-engineer (review) **Effort**: 4 hours

**Description**: Design the complete onboarding flow with decision trees, prompt sequences, and error handling
strategies. Create mockups of each screen with example inputs/outputs.

**Implementation**:

```python
# mycelium_onboarding/wizard/flow.py
"""
Wizard flow design and orchestration.

Flow Sequence:
1. Welcome screen with system detection summary
2. Service selection (Redis, Postgres, Temporal, TaskQueue)
3. Service configuration (ports, persistence, memory limits)
4. Deployment method selection (Docker Compose, Justfile)
5. Project metadata (name, description)
6. Configuration review and confirmation
7. Write configuration and show next steps
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass

class WizardStep(str, Enum):
    WELCOME = "welcome"
    SERVICE_SELECTION = "service_selection"
    SERVICE_CONFIG = "service_config"
    DEPLOYMENT_METHOD = "deployment_method"
    PROJECT_METADATA = "project_metadata"
    REVIEW = "review"
    FINALIZE = "finalize"

@dataclass
class WizardState:
    """Maintains state across wizard steps."""
    current_step: WizardStep
    detection_results: Optional['DetectionResults'] = None
    selected_services: set[str] = None
    deployment_method: Optional[str] = None
    config: Optional['MyceliumConfig'] = None

    def can_proceed(self) -> bool:
        """Validate if current step is complete."""
        if self.current_step == WizardStep.SERVICE_SELECTION:
            return self.selected_services is not None
        elif self.current_step == WizardStep.DEPLOYMENT_METHOD:
            return self.deployment_method is not None
        return True

    def next_step(self) -> Optional[WizardStep]:
        """Determine next step in flow."""
        steps = list(WizardStep)
        current_idx = steps.index(self.current_step)
        if current_idx < len(steps) - 1:
            return steps[current_idx + 1]
        return None

def create_wizard_state(detection_results: 'DetectionResults') -> WizardState:
    """Initialize wizard state with detection results."""
    return WizardState(
        current_step=WizardStep.WELCOME,
        detection_results=detection_results,
        selected_services=set(),
    )
```

**Acceptance Criteria**:

- [ ] Flow diagram covers all user paths (happy path + error paths)
- [ ] Each step has clear entry/exit conditions
- [ ] State management handles interruption and resume
- [ ] UX reviewed by devops-engineer for clarity

### Task 4.2: Implement InquirerPy Wizard Screens

**Agent**: python-pro **Effort**: 8 hours

**Description**: Implement all wizard screens using InquirerPy with rich formatting, validation, and help text. Each
screen should be self-contained and testable.

**Implementation**:

```python
# mycelium_onboarding/wizard/screens.py
"""Individual wizard screens using InquirerPy."""

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import PathValidator
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def show_welcome_screen(detection_results: 'DetectionResults') -> None:
    """Display welcome screen with system detection summary."""
    console.clear()

    # Create detection summary table
    table = Table(title="🔍 System Detection Results")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")

    # Add detection results
    table.add_row(
        "Docker",
        "✓ Available" if detection_results.docker.available else "✗ Not Found",
        detection_results.docker.version or "N/A"
    )
    table.add_row(
        "Redis",
        "✓ Running" if detection_results.redis.reachable else "○ Available",
        f"{detection_results.redis.host}:{detection_results.redis.port}"
    )
    # ... add other services ...

    console.print(table)
    console.print("\n")
    console.print(Panel(
        "[bold]Welcome to Mycelium Onboarding![/bold]\n\n"
        "This wizard will guide you through setting up your multi-agent "
        "coordination infrastructure. We've detected your system and will "
        "recommend the best configuration.",
        border_style="blue"
    ))

    inquirer.confirm(
        message="Ready to begin?",
        default=True,
    ).execute()

def prompt_service_selection(detection_results: 'DetectionResults') -> set[str]:
    """Prompt user to select services to enable."""
    console.print("\n[bold cyan]Service Selection[/bold cyan]")
    console.print("Select which coordination services to enable:\n")

    choices = [
        Choice(
            value="redis",
            name="Redis - Pub/Sub messaging and state management",
            enabled=detection_results.redis.available,
        ),
        Choice(
            value="postgres",
            name="PostgreSQL - Persistent data storage",
            enabled=detection_results.postgres.available,
        ),
        Choice(
            value="temporal",
            name="Temporal - Workflow orchestration",
            enabled=detection_results.temporal.available,
        ),
        Choice(
            value="taskqueue",
            name="TaskQueue - Task distribution (MCP)",
            enabled=True,  # Always available via MCP
        ),
    ]

    selected = inquirer.checkbox(
        message="Select services (Space to toggle, Enter to confirm):",
        choices=choices,
        validate=lambda result: len(result) > 0,
        invalid_message="You must select at least one service",
    ).execute()

    return set(selected)

def prompt_deployment_method(has_docker: bool) -> str:
    """Prompt user to choose deployment method."""
    console.print("\n[bold cyan]Deployment Method[/bold cyan]")

    if not has_docker:
        console.print(
            "[yellow]⚠ Docker not detected. Defaulting to Justfile deployment.[/yellow]\n"
        )
        return "justfile"

    choices = [
        Choice(
            value="docker-compose",
            name="Docker Compose (Recommended) - Containerized services with automatic dependency management",
        ),
        Choice(
            value="justfile",
            name="Justfile - Bare-metal deployment with manual service management",
        ),
    ]

    method = inquirer.select(
        message="Choose deployment method:",
        choices=choices,
        default="docker-compose",
    ).execute()

    return method

def prompt_project_metadata() -> dict[str, str]:
    """Prompt for project name and description."""
    console.print("\n[bold cyan]Project Metadata[/bold cyan]\n")

    name = inquirer.text(
        message="Project name:",
        default="mycelium",
        validate=lambda x: x.isidentifier(),
        invalid_message="Must be valid Python identifier (letters, numbers, underscores)",
    ).execute()

    description = inquirer.text(
        message="Project description (optional):",
        default="Multi-agent coordination system",
    ).execute()

    return {"name": name, "description": description}

def show_configuration_review(config: 'MyceliumConfig') -> bool:
    """Display configuration review and confirm."""
    console.print("\n[bold cyan]Configuration Review[/bold cyan]\n")

    # Create configuration summary
    table = Table(title="Final Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Project Name", config.project_name)
    table.add_row("Deployment Method", config.deployment.method)
    table.add_row("Services Enabled", ", ".join([
        s for s in ["redis", "postgres", "temporal", "taskqueue"]
        if getattr(config.services, s).enabled
    ]))

    console.print(table)
    console.print("\n")

    confirmed = inquirer.confirm(
        message="Save this configuration?",
        default=True,
    ).execute()

    return confirmed
```

**Test Plan**:

```python
# tests/test_wizard_screens.py
"""Test wizard screen rendering and validation."""

import pytest
from unittest.mock import patch, MagicMock
from mycelium_onboarding.wizard.screens import (
    prompt_service_selection,
    prompt_deployment_method,
    prompt_project_metadata,
)

def test_service_selection_requires_at_least_one():
    """Service selection should require at least one service."""
    with patch('mycelium_onboarding.wizard.screens.inquirer.checkbox') as mock:
        mock.return_value.execute.return_value = []
        # Should show validation error
        # (validation happens in InquirerPy, test the validator)

def test_deployment_method_defaults_to_justfile_without_docker():
    """Should default to Justfile when Docker unavailable."""
    method = prompt_deployment_method(has_docker=False)
    assert method == "justfile"

def test_project_metadata_validates_identifier():
    """Project name must be valid Python identifier."""
    # Test validation logic separately
    validator = lambda x: x.isidentifier()
    assert validator("mycelium") is True
    assert validator("my-project") is False
    assert validator("123project") is False
```

**Acceptance Criteria**:

- [ ] All screens render correctly with rich formatting
- [ ] Input validation prevents invalid configurations
- [ ] Help text provides clear guidance
- [ ] Color scheme is consistent and accessible
- [ ] Non-interactive mode supported via environment variables

### Task 4.3: Integrate Detection Results

**Agent**: python-pro, devops-engineer **Effort**: 3 hours

**Description**: Connect wizard to M03 service detection, using cached results to provide intelligent defaults and
disable unavailable options.

**Implementation**:

```python
# mycelium_onboarding/wizard/integration.py
"""Integration between wizard and detection system."""

from mycelium_onboarding.detection.orchestrator import detect_all_services
from mycelium_onboarding.wizard.flow import WizardState, create_wizard_state
from mycelium_onboarding.wizard.screens import (
    show_welcome_screen,
    prompt_service_selection,
    prompt_deployment_method,
)

async def run_wizard_with_detection(use_cache: bool = True) -> 'MyceliumConfig':
    """Run full wizard flow with service detection."""

    # Step 1: Detect services (use cache if available)
    console.print("[dim]Detecting available services...[/dim]")
    detection_results = await detect_all_services(use_cache=use_cache)

    # Step 2: Initialize wizard state
    state = create_wizard_state(detection_results)

    # Step 3: Show welcome with detection summary
    show_welcome_screen(detection_results)

    # Step 4: Service selection
    state.selected_services = prompt_service_selection(detection_results)

    # Step 5: Deployment method
    state.deployment_method = prompt_deployment_method(
        has_docker=detection_results.docker.available
    )

    # Step 6: Project metadata
    metadata = prompt_project_metadata()

    # Step 7: Build configuration
    config = build_config_from_selections(
        selected_services=state.selected_services,
        deployment_method=state.deployment_method,
        project_name=metadata["name"],
        detection_results=detection_results,
    )

    # Step 8: Review and confirm
    confirmed = show_configuration_review(config)
    if not confirmed:
        console.print("[yellow]Configuration not saved. Exiting.[/yellow]")
        return None

    return config

def build_config_from_selections(
    selected_services: set[str],
    deployment_method: str,
    project_name: str,
    detection_results: 'DetectionResults',
) -> 'MyceliumConfig':
    """Build MyceliumConfig from wizard selections."""
    from mycelium_onboarding.config.schema import (
        MyceliumConfig,
        DeploymentConfig,
        ServicesConfig,
        RedisConfig,
        PostgresConfig,
    )

    # Create service configs based on selections
    redis_config = RedisConfig(
        enabled="redis" in selected_services,
        port=detection_results.redis.port if detection_results.redis.reachable else 6379,
    )

    postgres_config = PostgresConfig(
        enabled="postgres" in selected_services,
        port=detection_results.postgres.port if detection_results.postgres.reachable else 5432,
    )

    # Build full config
    config = MyceliumConfig(
        project_name=project_name,
        deployment=DeploymentConfig(method=deployment_method),
        services=ServicesConfig(
            redis=redis_config,
            postgres=postgres_config,
            # ... other services ...
        ),
    )

    return config
```

**Acceptance Criteria**:

- [ ] Detection results correctly populate wizard defaults
- [ ] Unavailable services are disabled/hidden in prompts
- [ ] Detected ports/hosts are used as defaults
- [ ] Configuration builder creates valid MyceliumConfig

### Task 4.4: Implement Configuration Persistence

**Agent**: python-pro **Effort**: 2 hours

**Description**: Save final configuration using M02 ConfigManager, handle errors gracefully, provide user feedback on
success/failure.

**Implementation**:

```python
# mycelium_onboarding/wizard/persistence.py
"""Configuration persistence after wizard completion."""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from mycelium_onboarding.config.manager import ConfigManager
from mycelium_onboarding.config.schema import MyceliumConfig

console = Console()

def save_configuration(
    config: MyceliumConfig,
    project_local: bool = False
) -> tuple[bool, Optional[Path]]:
    """
    Save configuration using ConfigManager.

    Args:
        config: Configuration to save
        project_local: If True, save to project dir; else user config

    Returns:
        (success, config_path) tuple
    """
    try:
        config_path = ConfigManager.save(config, project_local=project_local)

        console.print(Panel(
            f"[bold green]✓ Configuration saved successfully![/bold green]\n\n"
            f"Location: [cyan]{config_path}[/cyan]\n\n"
            f"Next steps:\n"
            f"1. Review configuration: [bold]cat {config_path}[/bold]\n"
            f"2. Generate deployment: [bold]/mycelium-generate[/bold]\n"
            f"3. Start services: [bold]just up[/bold] or [bold]docker-compose up[/bold]",
            border_style="green",
            title="Success"
        ))

        return True, config_path

    except Exception as e:
        console.print(Panel(
            f"[bold red]✗ Failed to save configuration[/bold red]\n\n"
            f"Error: {e}\n\n"
            f"Please check permissions and try again.",
            border_style="red",
            title="Error"
        ))

        return False, None

def resume_from_previous() -> Optional[MyceliumConfig]:
    """
    Attempt to load previous configuration for resume.

    Returns:
        Previous config if found, else None
    """
    try:
        config = ConfigManager.load()

        console.print(Panel(
            f"[bold yellow]Previous configuration found![/bold yellow]\n\n"
            f"Project: {config.project_name}\n"
            f"Deployment: {config.deployment.method}\n\n"
            f"Would you like to resume or start fresh?",
            border_style="yellow",
            title="Resume Onboarding"
        ))

        from InquirerPy import inquirer
        choice = inquirer.select(
            message="Choose action:",
            choices=["Resume", "Start Fresh", "Cancel"],
        ).execute()

        if choice == "Resume":
            return config
        elif choice == "Cancel":
            return None

        # Start fresh - return None
        return None

    except FileNotFoundError:
        # No previous config - this is expected
        return None
```

**Acceptance Criteria**:

- [ ] Configuration saved to correct location (project vs user)
- [ ] Success message includes next steps
- [ ] Error messages are actionable
- [ ] Resume functionality works correctly

### Task 4.5: Create /mycelium-onboarding Command

**Agent**: claude-code-developer, python-pro **Effort**: 4 hours

**Description**: Integrate wizard as Claude Code slash command with proper argument parsing, help text, and error
handling.

**Implementation**:

```markdown
# ~/.claude/plugins/mycelium-core/commands/mycelium-onboarding.md

# Mycelium Onboarding

Launch interactive wizard to configure Mycelium multi-agent coordination system.

## Usage

```

/mycelium-onboarding \[--project-local\] \[--force\] \[--no-cache\]

````

## Options

- `--project-local`: Save configuration to project directory instead of user config
- `--force`: Skip resume prompt and start fresh
- `--no-cache`: Re-run service detection instead of using cached results
- `--non-interactive`: Run in non-interactive mode using defaults (for CI/CD)

## Examples

```bash
# Standard onboarding with detection cache
/mycelium-onboarding

# Fresh start without resume
/mycelium-onboarding --force

# Save to project directory
/mycelium-onboarding --project-local

# Re-detect all services
/mycelium-onboarding --no-cache

# Non-interactive mode for automation
/mycelium-onboarding --non-interactive
````

## What This Command Does

1. Detects available services (Docker, Redis, PostgreSQL, Temporal, GPU)
1. Launches interactive CLI wizard
1. Guides you through service selection and deployment method
1. Generates configuration file
1. Provides next steps for deployment

## After Onboarding

Once complete, proceed with:

- `/mycelium-generate` - Generate deployment files (docker-compose.yml or Justfile)
- `/mycelium-configuration show` - View current configuration
- Start services using generated deployment method

## Requirements

- Python 3.11+
- Terminal with color support
- Write access to config directory

## Troubleshooting

- **"Detection failed"**: Run with `--no-cache` to retry detection
- **"Config not saved"**: Check permissions on ~/.config/mycelium
- **"Missing services"**: Install missing services or proceed without them

````

```python
# mycelium_onboarding/cli.py
"""CLI entry point for onboarding command."""

import asyncio
import click
from rich.console import Console

from mycelium_onboarding.wizard.integration import run_wizard_with_detection
from mycelium_onboarding.wizard.persistence import save_configuration, resume_from_previous

console = Console()

@click.command()
@click.option(
    '--project-local',
    is_flag=True,
    help='Save configuration to project directory'
)
@click.option(
    '--force',
    is_flag=True,
    help='Skip resume prompt and start fresh'
)
@click.option(
    '--no-cache',
    is_flag=True,
    help='Re-run service detection'
)
@click.option(
    '--non-interactive',
    is_flag=True,
    help='Run in non-interactive mode using defaults'
)
def onboard(project_local: bool, force: bool, no_cache: bool, non_interactive: bool):
    """Launch Mycelium onboarding wizard."""

    # Check for resume unless --force
    if not force and not non_interactive:
        previous_config = resume_from_previous()
        if previous_config is not None:
            # User chose to cancel
            return

    # Run wizard
    config = asyncio.run(run_wizard_with_detection(use_cache=not no_cache))

    if config is None:
        # User cancelled during wizard
        console.print("[yellow]Onboarding cancelled.[/yellow]")
        return

    # Save configuration
    success, config_path = save_configuration(config, project_local=project_local)

    if not success:
        raise click.ClickException("Failed to save configuration")

if __name__ == '__main__':
    onboard()
````

**Acceptance Criteria**:

- [ ] Command registered and discoverable via `/mycelium-onboarding`
- [ ] All flags work correctly
- [ ] Help text is clear and comprehensive
- [ ] Errors are handled gracefully with helpful messages

### Task 4.6: Testing and Documentation

**Agent**: test-automator (lead), python-pro (support) **Effort**: 4 hours

**Description**: Create comprehensive test suite covering wizard flow, validation, error handling. Write user-facing
documentation.

**Test Plan**:

```python
# tests/integration/test_wizard_flow.py
"""Integration tests for complete wizard flow."""

import pytest
from unittest.mock import patch, AsyncMock
from mycelium_onboarding.wizard.integration import run_wizard_with_detection

@pytest.mark.asyncio
async def test_complete_wizard_flow():
    """Test complete wizard flow from detection to config."""

    # Mock detection results
    mock_detection = AsyncMock(return_value=mock_detection_results())

    # Mock user inputs
    mock_inputs = {
        'service_selection': {'redis', 'temporal'},
        'deployment_method': 'docker-compose',
        'project_name': 'test-project',
        'confirm': True,
    }

    with patch('mycelium_onboarding.wizard.integration.detect_all_services', mock_detection):
        with patch_wizard_prompts(mock_inputs):
            config = await run_wizard_with_detection()

    assert config is not None
    assert config.project_name == 'test-project'
    assert config.services.redis.enabled is True
    assert config.services.temporal.enabled is True
    assert config.deployment.method == 'docker-compose'

@pytest.mark.asyncio
async def test_wizard_handles_no_docker():
    """Wizard should default to Justfile when Docker unavailable."""
    mock_detection = AsyncMock(return_value=mock_detection_results(docker_available=False))

    with patch('mycelium_onboarding.wizard.integration.detect_all_services', mock_detection):
        # ... run wizard ...
        config = await run_wizard_with_detection()

    assert config.deployment.method == 'justfile'

def test_wizard_resume_functionality():
    """Resume should load previous config and offer choices."""
    # Create previous config
    # Mock resume prompt
    # Verify correct behavior
    pass
```

**Documentation**:

````markdown
# docs/guides/interactive-onboarding.md

# Interactive Onboarding Guide

## Overview

The Mycelium onboarding wizard helps you configure your multi-agent coordination infrastructure through an interactive CLI interface.

## Prerequisites

- Python 3.11 or later
- Terminal with color support
- Optional: Docker, Redis, PostgreSQL, Temporal

## Running the Wizard

### Basic Usage

```bash
/mycelium-onboarding
````

This will:

1. Detect available services on your system
1. Launch interactive wizard
1. Guide you through configuration
1. Save configuration file
1. Show next steps

### Advanced Options

```bash
# Save to project directory (not user config)
/mycelium-onboarding --project-local

# Force fresh start (skip resume)
/mycelium-onboarding --force

# Re-detect services (don't use cache)
/mycelium-onboarding --no-cache

# Non-interactive mode (use defaults)
/mycelium-onboarding --non-interactive
```

## Wizard Screens

### 1. Welcome & Detection

Shows detected services with status indicators:

- ✓ Available: Service installed and working
- ○ Available: Service installed but not running
- ✗ Not Found: Service not detected

### 2. Service Selection

Choose which coordination services to enable:

- **Redis**: Fast pub/sub messaging and state management
- **PostgreSQL**: Persistent data storage
- **Temporal**: Workflow orchestration
- **TaskQueue**: Task distribution (MCP-based, always available)

💡 Tip: Start with Redis + TaskQueue for basic coordination

### 3. Deployment Method

Choose how to deploy services:

**Docker Compose** (Recommended)

- ✓ Automatic dependency management
- ✓ Isolated environments
- ✓ Easy to start/stop
- ✗ Requires Docker

**Justfile** (Bare-metal)

- ✓ No container overhead
- ✓ Direct system access
- ✗ Manual service management

### 4. Project Metadata

Enter project details:

- **Name**: Valid Python identifier (e.g., `mycelium`, `my_project`)
- **Description**: Optional project description

### 5. Configuration Review

Review all selections before saving. You can:

- Confirm and save
- Cancel and start over

## After Onboarding

Once configuration is saved:

```bash
# 1. View configuration
/mycelium-configuration show

# 2. Generate deployment files
/mycelium-generate

# 3. Start services
just up              # Justfile deployment
docker-compose up    # Docker Compose deployment
```

## Troubleshooting

### Detection Issues

**Problem**: Services not detected correctly

```bash
# Clear cache and re-detect
/mycelium-onboarding --no-cache
```

### Permission Errors

**Problem**: Cannot write configuration

```bash
# Check directory permissions
ls -la ~/.config/mycelium

# Use project-local config instead
/mycelium-onboarding --project-local
```

### Resume Not Working

**Problem**: Cannot resume previous onboarding

```bash
# Force fresh start
/mycelium-onboarding --force
```

## Configuration File Location

Configuration is saved to:

- **User config**: `~/.config/mycelium/mycelium.yaml`
- **Project config**: `.mycelium/mycelium.yaml` (with `--project-local`)

## Next Steps

- [Configuration Management](./configuration-management.md)
- [Deployment Generation](./deployment-generation.md)
- [Testing Framework](./coordination-testing.md)

```

**Acceptance Criteria**:
- [ ] Integration tests cover happy path and error cases
- [ ] Unit tests for each wizard screen
- [ ] Documentation includes screenshots and examples
- [ ] Troubleshooting guide addresses common issues

## Exit Criteria

- [ ] InquirerPy wizard implemented with all screens
- [ ] Service detection integration working correctly
- [ ] Configuration saved using M02 ConfigManager
- [ ] `/mycelium-onboarding` command functional
- [ ] Non-interactive mode supported
- [ ] Resume functionality working
- [ ] ≥80% test coverage
- [ ] User documentation complete
- [ ] Code reviewed and approved by python-pro + devops-engineer
- [ ] Manual testing completed on Linux, macOS, Windows (WSL2)

## Deliverables

1. **Core Implementation**:
   - `mycelium_onboarding/wizard/flow.py` - Wizard state machine
   - `mycelium_onboarding/wizard/screens.py` - InquirerPy screens
   - `mycelium_onboarding/wizard/integration.py` - Detection integration
   - `mycelium_onboarding/wizard/persistence.py` - Config saving
   - `mycelium_onboarding/cli.py` - CLI entry point

2. **Command Integration**:
   - `~/.claude/plugins/mycelium-core/commands/mycelium-onboarding.md` - Command definition

3. **Tests**:
   - `tests/unit/test_wizard_flow.py` - Unit tests
   - `tests/integration/test_wizard_integration.py` - Integration tests
   - `tests/e2e/test_onboarding_command.py` - End-to-end tests

4. **Documentation**:
   - `docs/guides/interactive-onboarding.md` - User guide
   - `docs/api/wizard-api.md` - API reference
   - Screenshots of wizard screens

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| UX confusion with complex flows | Medium | High | User testing with real users, clear help text, progressive disclosure |
| InquirerPy compatibility issues | Low | Medium | Pin version, test on multiple terminals |
| Resume state corruption | Low | High | Atomic writes, validation before save, backup previous config |
| Terminal rendering issues (colors, Unicode) | Medium | Medium | Fallback to plain text, detect terminal capabilities |

## Dependencies for Next Milestones

**M05 (Deployment Generation)** requires:
- Valid `MyceliumConfig` object created by wizard
- Service selections (Redis, Postgres, Temporal, TaskQueue)
- Deployment method choice (Docker Compose vs Justfile)
- Project metadata (name, description)

---

**Milestone Owner**: python-pro
**Reviewers**: devops-engineer, code-reviewer
**Status**: Ready for Implementation
**Created**: 2025-10-13
**Target Completion**: Day 11 (3 days after M03)
```
