# M07: Configuration Management

## Overview

**Duration**: 2 days
**Dependencies**: M02 (configuration system)
**Blocks**: M10 (polish & release)
**Lead Agent**: python-pro
**Support Agents**: claude-code-developer
**Parallel With**: M08 (Documentation), M09 (Testing Suite)

## Why This Milestone

Configuration management commands provide user-friendly interfaces for viewing, editing, and validating Mycelium configurations after initial onboarding. While M04 creates configuration through the wizard, users need ongoing tools to inspect settings, make adjustments, and troubleshoot issues. This milestone empowers users to maintain their infrastructure configuration without manual YAML editing.

Well-designed configuration commands:
- Lower barrier to configuration changes
- Prevent syntax errors through validation
- Provide clear visibility into current settings
- Support both interactive and scriptable workflows
- Enable troubleshooting through diagnostics

## Requirements

### Functional Requirements (FR)

- **FR-7.1**: `show` command displays current configuration in readable format
- **FR-7.2**: `edit` command opens configuration in user's preferred editor
- **FR-7.3**: `validate` command checks configuration for errors
- **FR-7.4**: `init` command creates new default configuration
- **FR-7.5**: Support for both project-local and user-global configuration

### Technical Requirements (TR)

- **TR-7.1**: Use rich library for formatted output
- **TR-7.2**: Leverage M02 Pydantic validators for validation
- **TR-7.3**: Support JSON and YAML output formats
- **TR-7.4**: Detect and use $EDITOR environment variable
- **TR-7.5**: Atomic file writes (write to temp, then rename)

### Integration Requirements (IR)

- **IR-7.1**: Integrate with M02 ConfigManager for loading/saving
- **IR-7.2**: Use M01 XDG directories for file locations
- **IR-7.3**: Integrate as `/mycelium-configuration` slash command

### Compliance Requirements (CR)

- **CR-7.1**: Never expose sensitive data in output (passwords, secrets)
- **CR-7.2**: Validate before writing to prevent corruption
- **CR-7.3**: Provide clear error messages with remediation steps

## Tasks

### Task 7.1: Implement Config Show Command

**Agent**: python-pro
**Effort**: 3 hours

**Description**: Create command to display current configuration in readable format with syntax highlighting and sensitive data masking.

**Implementation**:

```python
# mycelium_onboarding/cli/config.py
"""Configuration management CLI commands."""

import click
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel
import yaml
import json

from mycelium_onboarding.config.manager import ConfigManager
from mycelium_onboarding.config.schema import MyceliumConfig

console = Console()

@click.group()
def config():
    """Manage Mycelium configuration."""
    pass

@config.command()
@click.option(
    '--format',
    type=click.Choice(['yaml', 'json', 'table'], case_sensitive=False),
    default='table',
    help='Output format'
)
@click.option(
    '--path',
    is_flag=True,
    help='Show configuration file path'
)
@click.option(
    '--project',
    is_flag=True,
    help='Use project-local configuration'
)
def show(format: str, path: bool, project: bool):
    """Display current configuration."""

    try:
        # Load configuration
        config = ConfigManager.load(prefer_project=project)
        config_path = ConfigManager.get_config_path(prefer_project=project)

        if path:
            # Just show path
            console.print(f"[cyan]{config_path}[/cyan]")
            return

        # Display based on format
        if format == 'table':
            _show_table_format(config)
        elif format == 'yaml':
            _show_yaml_format(config)
        elif format == 'json':
            _show_json_format(config)

        # Show file location
        console.print(f"\n[dim]Configuration: {config_path}[/dim]")

    except FileNotFoundError:
        console.print("[yellow]⚠ No configuration found. Run /mycelium-onboarding to create one.[/yellow]")
        raise click.Abort()

def _show_table_format(config: MyceliumConfig):
    """Display configuration as formatted table."""

    # Project Info
    table = Table(title="Project Configuration", show_header=False)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Project Name", config.project_name)
    table.add_row("Deployment Method", config.deployment.method)

    console.print(table)
    console.print()

    # Services
    table = Table(title="Enabled Services")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Configuration", style="white")

    if config.services.redis.enabled:
        table.add_row(
            "Redis",
            "✓ Enabled",
            f"Port: {config.services.redis.port}, Persistence: {config.services.redis.persistence}"
        )

    if config.services.postgres.enabled:
        table.add_row(
            "PostgreSQL",
            "✓ Enabled",
            f"Port: {config.services.postgres.port}"
        )

    if config.services.temporal.enabled:
        table.add_row(
            "Temporal",
            "✓ Enabled",
            f"Port: {config.services.temporal.frontend_port}"
        )

    if config.services.taskqueue.enabled:
        table.add_row(
            "TaskQueue",
            "✓ Enabled",
            "MCP Server"
        )

    console.print(table)

def _show_yaml_format(config: MyceliumConfig):
    """Display configuration as YAML with syntax highlighting."""
    config_dict = config.model_dump()

    # Mask sensitive data
    config_dict = _mask_sensitive_data(config_dict)

    yaml_str = yaml.dump(config_dict, default_flow_style=False, sort_keys=False)

    syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=False)
    console.print(syntax)

def _show_json_format(config: MyceliumConfig):
    """Display configuration as JSON."""
    config_dict = config.model_dump()

    # Mask sensitive data
    config_dict = _mask_sensitive_data(config_dict)

    json_str = json.dumps(config_dict, indent=2)

    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
    console.print(syntax)

def _mask_sensitive_data(config_dict: dict) -> dict:
    """Mask sensitive values like passwords."""
    sensitive_keys = {'password', 'secret', 'api_key', 'token'}

    def mask_recursive(obj):
        if isinstance(obj, dict):
            return {
                k: "***REDACTED***" if any(s in k.lower() for s in sensitive_keys) else mask_recursive(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [mask_recursive(item) for item in obj]
        else:
            return obj

    return mask_recursive(config_dict)
```

**Test Plan**:

```python
# tests/test_config_show.py
"""Tests for config show command."""

import pytest
from click.testing import CliRunner
from mycelium_onboarding.cli.config import show

def test_show_table_format(tmp_config):
    """Show command should display table format."""
    runner = CliRunner()
    result = runner.invoke(show, ['--format', 'table'])

    assert result.exit_code == 0
    assert 'Project Configuration' in result.output

def test_show_yaml_format(tmp_config):
    """Show command should display YAML format."""
    runner = CliRunner()
    result = runner.invoke(show, ['--format', 'yaml'])

    assert result.exit_code == 0
    assert 'project_name:' in result.output

def test_show_masks_sensitive_data(tmp_config_with_password):
    """Sensitive data should be masked."""
    runner = CliRunner()
    result = runner.invoke(show, ['--format', 'yaml'])

    assert '***REDACTED***' in result.output
    assert 'actual_password' not in result.output

def test_show_path_only():
    """Show --path should only display config path."""
    runner = CliRunner()
    result = runner.invoke(show, ['--path'])

    assert result.exit_code == 0
    assert 'mycelium.yaml' in result.output
```

**Acceptance Criteria**:
- [ ] Table format shows key configuration settings
- [ ] YAML/JSON formats display complete configuration
- [ ] Sensitive data is masked in all formats
- [ ] --path option shows configuration file location
- [ ] Clear error when no configuration exists

### Task 7.2: Implement Config Edit Command

**Agent**: python-pro
**Effort**: 4 hours

**Description**: Create command to open configuration in user's preferred editor with validation after editing.

**Implementation**:

```python
# mycelium_onboarding/cli/config.py (continued)

import subprocess
import os
import tempfile

@config.command()
@click.option(
    '--project',
    is_flag=True,
    help='Edit project-local configuration'
)
@click.option(
    '--editor',
    envvar='EDITOR',
    default='nano',
    help='Editor to use (default: $EDITOR or nano)'
)
def edit(project: bool, editor: str):
    """Edit configuration in your preferred editor."""

    try:
        # Load current configuration
        config = ConfigManager.load(prefer_project=project)
        config_path = ConfigManager.get_config_path(prefer_project=project)

    except FileNotFoundError:
        console.print("[yellow]⚠ No configuration found. Creating new one...[/yellow]")
        config = MyceliumConfig()
        config_path = ConfigManager.get_config_path(prefer_project=project)
        config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        tmp_path = Path(tmp.name)
        yaml_content = yaml.dump(
            config.model_dump(),
            default_flow_style=False,
            sort_keys=False
        )
        tmp.write(yaml_content)

    # Open in editor
    try:
        subprocess.run([editor, str(tmp_path)], check=True)

    except subprocess.CalledProcessError:
        console.print(f"[red]✗ Editor '{editor}' failed[/red]")
        tmp_path.unlink()
        raise click.Abort()

    except FileNotFoundError:
        console.print(f"[red]✗ Editor '{editor}' not found[/red]")
        console.print(f"[dim]Set EDITOR environment variable or use --editor[/dim]")
        tmp_path.unlink()
        raise click.Abort()

    # Load edited content
    try:
        edited_yaml = tmp_path.read_text()
        edited_dict = yaml.safe_load(edited_yaml)

        # Validate
        edited_config = MyceliumConfig(**edited_dict)

        # Save if valid
        ConfigManager.save(edited_config, project_local=project)

        console.print(f"[green]✓ Configuration saved to {config_path}[/green]")

    except yaml.YAMLError as e:
        console.print(f"[red]✗ Invalid YAML syntax:[/red]")
        console.print(str(e))
        console.print("\n[yellow]Configuration not saved. Fix errors and try again.[/yellow]")

    except Exception as e:
        console.print(f"[red]✗ Validation failed:[/red]")
        console.print(str(e))
        console.print("\n[yellow]Configuration not saved. Fix errors and try again.[/yellow]")

    finally:
        # Cleanup temp file
        tmp_path.unlink()
```

**Acceptance Criteria**:
- [ ] Opens configuration in $EDITOR (or specified editor)
- [ ] Validates edited configuration before saving
- [ ] Provides clear error messages for validation failures
- [ ] Does not overwrite config if validation fails
- [ ] Supports both project and user configurations

### Task 7.3: Implement Config Validate Command

**Agent**: python-pro
**Effort**: 2 hours

**Description**: Create command to validate configuration file without making changes, useful for CI/CD and troubleshooting.

**Implementation**:

```python
# mycelium_onboarding/cli/config.py (continued)

@config.command()
@click.option(
    '--project',
    is_flag=True,
    help='Validate project-local configuration'
)
@click.option(
    '--strict',
    is_flag=True,
    help='Enable strict validation (warnings as errors)'
)
def validate(project: bool, strict: bool):
    """Validate configuration file."""

    try:
        config_path = ConfigManager.get_config_path(prefer_project=project)

        if not config_path.exists():
            console.print(f"[yellow]⚠ Configuration file not found: {config_path}[/yellow]")
            raise click.Abort()

        # Load and validate
        console.print(f"[cyan]Validating: {config_path}[/cyan]\n")

        config = ConfigManager.load_from_path(config_path)

        # Run additional checks
        warnings = _check_configuration_warnings(config)

        if warnings:
            console.print("[yellow]Warnings:[/yellow]")
            for warning in warnings:
                console.print(f"  ⚠ {warning}")

            if strict:
                console.print("\n[red]✗ Validation failed (strict mode)[/red]")
                raise click.ClickException("Configuration has warnings")

        # Success
        console.print("\n[green]✓ Configuration is valid[/green]")

        # Show summary
        _show_validation_summary(config)

    except Exception as e:
        console.print(f"\n[red]✗ Validation failed:[/red]")
        console.print(f"  {e}")
        raise click.ClickException("Invalid configuration")

def _check_configuration_warnings(config: MyceliumConfig) -> list[str]:
    """Check for configuration warnings (non-fatal issues)."""
    warnings = []

    # Check for deprecated settings
    # (Add checks as configuration evolves)

    # Check for unusual port numbers
    if config.services.redis.enabled:
        if config.services.redis.port < 1024:
            warnings.append("Redis port < 1024 requires root privileges")

    # Check for missing recommended settings
    if config.services.redis.enabled and not config.services.redis.persistence:
        warnings.append("Redis persistence disabled (data loss on restart)")

    return warnings

def _show_validation_summary(config: MyceliumConfig):
    """Show validation summary."""
    table = Table(title="Configuration Summary", show_header=False)
    table.add_column("Item", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Version", config.version)
    table.add_row("Project Name", config.project_name)
    table.add_row("Deployment Method", config.deployment.method)

    enabled_services = []
    if config.services.redis.enabled:
        enabled_services.append("Redis")
    if config.services.postgres.enabled:
        enabled_services.append("PostgreSQL")
    if config.services.temporal.enabled:
        enabled_services.append("Temporal")
    if config.services.taskqueue.enabled:
        enabled_services.append("TaskQueue")

    table.add_row("Enabled Services", ", ".join(enabled_services))

    console.print(table)
```

**Test Plan**:

```python
# tests/test_config_validate.py
"""Tests for config validate command."""

def test_validate_success(tmp_valid_config):
    """Validate should pass for valid configuration."""
    runner = CliRunner()
    result = runner.invoke(validate)

    assert result.exit_code == 0
    assert '✓ Configuration is valid' in result.output

def test_validate_detects_warnings(tmp_config_with_warnings):
    """Validate should show warnings."""
    runner = CliRunner()
    result = runner.invoke(validate)

    assert result.exit_code == 0
    assert '⚠' in result.output

def test_validate_strict_fails_on_warnings(tmp_config_with_warnings):
    """Validate --strict should fail on warnings."""
    runner = CliRunner()
    result = runner.invoke(validate, ['--strict'])

    assert result.exit_code != 0

def test_validate_invalid_config(tmp_invalid_config):
    """Validate should fail for invalid configuration."""
    runner = CliRunner()
    result = runner.invoke(validate)

    assert result.exit_code != 0
    assert 'Validation failed' in result.output
```

**Acceptance Criteria**:
- [ ] Validates configuration using Pydantic schema
- [ ] Shows clear error messages for validation failures
- [ ] Detects and reports warnings
- [ ] Strict mode treats warnings as errors
- [ ] Displays validation summary on success

### Task 7.4: Implement Config Init Command

**Agent**: python-pro
**Effort**: 2 hours

**Description**: Create command to initialize new configuration with defaults or from template.

**Implementation**:

```python
# mycelium_onboarding/cli/config.py (continued)

@config.command()
@click.option(
    '--project',
    is_flag=True,
    help='Create project-local configuration'
)
@click.option(
    '--template',
    type=click.Choice(['minimal', 'docker', 'justfile', 'full']),
    default='minimal',
    help='Configuration template to use'
)
@click.option(
    '--force',
    is_flag=True,
    help='Overwrite existing configuration'
)
def init(project: bool, template: str, force: bool):
    """Initialize new configuration."""

    config_path = ConfigManager.get_config_path(prefer_project=project)

    if config_path.exists() and not force:
        console.print(f"[yellow]⚠ Configuration already exists: {config_path}[/yellow]")
        console.print(f"[dim]Use --force to overwrite[/dim]")
        raise click.Abort()

    # Create configuration from template
    config = _create_from_template(template)

    # Save configuration
    ConfigManager.save(config, project_local=project)

    console.print(Panel(
        f"[bold green]✓ Configuration initialized![/bold green]\n\n"
        f"Location: [cyan]{config_path}[/cyan]\n"
        f"Template: [cyan]{template}[/cyan]\n\n"
        f"Next steps:\n"
        f"1. Review configuration: [bold]/mycelium-configuration show[/bold]\n"
        f"2. Edit if needed: [bold]/mycelium-configuration edit[/bold]\n"
        f"3. Generate deployment: [bold]/mycelium-generate[/bold]",
        border_style="green"
    ))

def _create_from_template(template: str) -> MyceliumConfig:
    """Create configuration from template."""
    from mycelium_onboarding.config.schema import (
        MyceliumConfig,
        DeploymentConfig,
        ServicesConfig,
        RedisConfig,
        PostgresConfig,
        TemporalConfig,
        TaskQueueConfig,
    )

    if template == 'minimal':
        # Minimal: Redis + TaskQueue
        return MyceliumConfig(
            project_name="mycelium",
            deployment=DeploymentConfig(method="docker-compose"),
            services=ServicesConfig(
                redis=RedisConfig(enabled=True),
                postgres=PostgresConfig(enabled=False),
                temporal=TemporalConfig(enabled=False),
                taskqueue=TaskQueueConfig(enabled=True),
            ),
        )

    elif template == 'docker':
        # Docker Compose with all services
        return MyceliumConfig(
            project_name="mycelium",
            deployment=DeploymentConfig(method="docker-compose"),
            services=ServicesConfig(
                redis=RedisConfig(enabled=True, persistence=True),
                postgres=PostgresConfig(enabled=True),
                temporal=TemporalConfig(enabled=True),
                taskqueue=TaskQueueConfig(enabled=True),
            ),
        )

    elif template == 'justfile':
        # Justfile with core services
        return MyceliumConfig(
            project_name="mycelium",
            deployment=DeploymentConfig(method="justfile"),
            services=ServicesConfig(
                redis=RedisConfig(enabled=True),
                postgres=PostgresConfig(enabled=True),
                temporal=TemporalConfig(enabled=False),  # Complex for bare-metal
                taskqueue=TaskQueueConfig(enabled=True),
            ),
        )

    elif template == 'full':
        # All services with recommended settings
        return MyceliumConfig(
            project_name="mycelium",
            deployment=DeploymentConfig(method="docker-compose", healthcheck_timeout=90),
            services=ServicesConfig(
                redis=RedisConfig(
                    enabled=True,
                    persistence=True,
                    max_memory="512mb",
                ),
                postgres=PostgresConfig(
                    enabled=True,
                    max_connections=100,
                ),
                temporal=TemporalConfig(
                    enabled=True,
                ),
                taskqueue=TaskQueueConfig(enabled=True),
            ),
        )

    else:
        raise ValueError(f"Unknown template: {template}")
```

**Acceptance Criteria**:
- [ ] Creates configuration from template
- [ ] Supports multiple templates (minimal, docker, justfile, full)
- [ ] Respects --force flag for overwriting
- [ ] Shows clear next steps after initialization
- [ ] Works for both project and user configurations

### Task 7.5: Create /mycelium-configuration Command

**Agent**: claude-code-developer, python-pro
**Effort**: 2 hours

**Description**: Integrate configuration management as `/mycelium-configuration` command with all subcommands.

**Implementation**:

```markdown
# ~/.claude/plugins/mycelium-core/commands/mycelium-configuration.md

# Mycelium Configuration

Manage Mycelium configuration files.

## Usage

```
/mycelium-configuration <subcommand> [options]
```

## Subcommands

### show

Display current configuration.

```bash
# Show as table (default)
/mycelium-configuration show

# Show as YAML
/mycelium-configuration show --format yaml

# Show as JSON
/mycelium-configuration show --format json

# Show configuration file path
/mycelium-configuration show --path
```

### edit

Edit configuration in your preferred editor.

```bash
# Edit user configuration
/mycelium-configuration edit

# Edit project configuration
/mycelium-configuration edit --project

# Use specific editor
/mycelium-configuration edit --editor vim
```

### validate

Validate configuration file.

```bash
# Validate configuration
/mycelium-configuration validate

# Strict mode (warnings as errors)
/mycelium-configuration validate --strict
```

### init

Initialize new configuration.

```bash
# Minimal configuration
/mycelium-configuration init

# Docker Compose template
/mycelium-configuration init --template docker

# Justfile template
/mycelium-configuration init --template justfile

# Full configuration
/mycelium-configuration init --template full

# Project-local configuration
/mycelium-configuration init --project
```

## Configuration Locations

- **User Config**: `~/.config/mycelium/mycelium.yaml`
- **Project Config**: `.mycelium/mycelium.yaml`

## Examples

```bash
# View current settings
/mycelium-configuration show

# Edit deployment method
/mycelium-configuration edit

# Validate after changes
/mycelium-configuration validate

# Create new project config
/mycelium-configuration init --project --template docker
```

## Troubleshooting

### Invalid Configuration

```bash
# Validate to see errors
/mycelium-configuration validate

# Edit to fix
/mycelium-configuration edit
```

### Editor Not Found

```bash
# Set EDITOR environment variable
export EDITOR=vim

# Or specify editor
/mycelium-configuration edit --editor nano
```
```

**Acceptance Criteria**:
- [ ] All subcommands accessible via slash command
- [ ] Help text comprehensive and clear
- [ ] Examples demonstrate common workflows
- [ ] Troubleshooting section addresses common issues

## Exit Criteria

- [ ] All config subcommands implemented (show, edit, validate, init)
- [ ] Sensitive data masking working correctly
- [ ] Validation provides clear error messages
- [ ] Editor integration works with $EDITOR
- [ ] `/mycelium-configuration` command functional
- [ ] ≥80% test coverage for config commands
- [ ] Documentation includes usage examples
- [ ] Code reviewed by python-pro + code-reviewer

## Deliverables

1. **CLI Commands**:
   - `mycelium_onboarding/cli/config.py` - Configuration CLI

2. **Command Integration**:
   - `~/.claude/plugins/mycelium-core/commands/mycelium-configuration.md`

3. **Tests**:
   - `tests/unit/test_config_show.py`
   - `tests/unit/test_config_edit.py`
   - `tests/unit/test_config_validate.py`
   - `tests/unit/test_config_init.py`

4. **Documentation**:
   - `docs/guides/configuration-management.md`

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Editor integration failures | Low | Medium | Detect $EDITOR, provide fallback to nano |
| Configuration corruption | Low | High | Validate before save, atomic writes, backups |
| Sensitive data leakage | Low | High | Mask passwords, audit output formats |
| Cross-platform editor issues | Low | Medium | Test on Linux, macOS, Windows (WSL2) |

## Dependencies for Next Milestones

**M10 (Polish & Release)** requires:
- Working configuration management for user adjustments
- Validation as quality gate
- Documentation for configuration options

---

**Milestone Owner**: python-pro
**Reviewers**: claude-code-developer, code-reviewer
**Status**: Ready for Implementation
**Created**: 2025-10-13
**Target Completion**: Day 19 (parallel with M08, M09)
