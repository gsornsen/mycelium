# Review Screen Specification

## Purpose

Display summary of all configuration choices, allow confirmation or editing.

## Layout

```
╔══════════════════════════════════════════════════════════════╗
║                  Configuration Review                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Please review your configuration before finalizing.        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Project Name:        mycelium
  Setup Mode:          Quick Setup

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Enabled Services
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✓ Redis
    Port:              6379
    Persistence:       Enabled
    Max Memory:        256mb

  ✓ PostgreSQL
    Port:              5432
    Database:          mycelium
    Max Connections:   100

  ✗ Temporal
    (Not enabled)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Deployment Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Method:              Docker Compose
  Auto-start:          Yes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generated Files
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Configuration:       ~/.config/mycelium/mycelium.yaml
  Docker Compose:      docker-compose.yml
  Environment:         .env

? What would you like to do?
  > Confirm and generate configuration
    Edit services
    Edit deployment
    Cancel and exit
```

## User Inputs

### Action Selection

- **Field**: `action`
- **Type**: Single selection (radio)
- **Options**:
  - `confirm`: Confirm and generate configuration
  - `edit_services`: Jump back to SERVICES screen
  - `edit_deployment`: Jump back to DEPLOYMENT screen
  - `edit_advanced`: Jump back to ADVANCED screen (if custom mode)
  - `cancel`: Cancel and exit wizard
- **Default**: `confirm`
- **Required**: Yes

## Display Sections

### Project Configuration

- Project name
- Setup mode (Quick/Custom)
- Started timestamp

### Enabled Services

For each service (Redis, PostgreSQL, Temporal):

- Status icon (✓ enabled, ✗ disabled)
- Service name
- Key configuration values (only if enabled):
  - Ports
  - Database names
  - Persistence settings
  - Memory limits
  - Namespaces
  - Max connections

### Deployment Configuration

- Deployment method
- Auto-start setting
- Prerequisites status

### Generated Files

- List of files that will be created
- Full paths where available
- Brief description of each file

## Validation

No user input validation required (summary display).

## Help Text

### Review Help

```
Configuration Review
═══════════════════════════════════════════════════════════

This screen shows your complete configuration.

You can:
• Confirm to generate configuration files
• Edit specific sections by jumping back
• Cancel to exit without saving

All changes can be modified later by:
• Re-running the wizard
• Manually editing configuration files
• Using mycelium-onboard config commands
```

## Confirmation Dialog

When user selects "Confirm and generate configuration":

```
? Are you ready to generate configuration?
  This will create the following files:

  • ~/.config/mycelium/mycelium.yaml
  • docker-compose.yml
  • .env

  Existing files will be backed up with .backup extension.

  > Yes, generate configuration
    No, go back to review
```

## Cancel Confirmation

When user selects "Cancel and exit":

```
? Are you sure you want to cancel?

  Your progress will be lost.

  You can save your progress by selecting "Save and exit"
  to resume this wizard later.

  > Go back to review
    Save and exit (resume later)
    Cancel and exit (discard progress)
```

## State Updates

On completion of this screen:

- If `confirm`: Mark wizard as ready for completion
- If `edit_*`: Jump to specified screen
- If `cancel`: Exit wizard

## Next Step Logic

- **Confirm** → Proceed to COMPLETE screen (generate configuration)
- **Edit Services** → Jump to SERVICES screen
- **Edit Deployment** → Jump to DEPLOYMENT screen
- **Edit Advanced** → Jump to ADVANCED screen (if custom mode)
- **Cancel** → Exit wizard with confirmation

## InquirerPy Implementation

```python
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from pathlib import Path

def review_screen(state: WizardState) -> str:
    """Display configuration review screen.

    Args:
        state: Current wizard state

    Returns:
        Action: "confirm", "edit_services", "edit_deployment", "edit_advanced", or "cancel"
    """
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                  Configuration Review                        ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║                                                              ║")
    print("║  Please review your configuration before finalizing.        ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Project Configuration
    print("━" * 64)
    print("Project Configuration")
    print("━" * 64)
    print()
    print(f"  Project Name:        {state.project_name}")
    print(f"  Setup Mode:          {'Quick Setup' if state.setup_mode == 'quick' else 'Custom Setup'}")
    print()

    # Enabled Services
    print("━" * 64)
    print("Enabled Services")
    print("━" * 64)
    print()

    # Redis
    if state.services_enabled.get("redis"):
        print("  ✓ Redis")
        print(f"    Port:              {state.redis_port}")
        print(f"    Persistence:       {'Enabled' if state.enable_persistence else 'Disabled'}")
        if hasattr(state, 'redis_max_memory'):
            print(f"    Max Memory:        {state.redis_max_memory}")
        print()
    else:
        print("  ✗ Redis")
        print("    (Not enabled)")
        print()

    # PostgreSQL
    if state.services_enabled.get("postgres"):
        print("  ✓ PostgreSQL")
        print(f"    Port:              {state.postgres_port}")
        print(f"    Database:          {state.postgres_database}")
        if hasattr(state, 'postgres_max_connections'):
            print(f"    Max Connections:   {state.postgres_max_connections}")
        print()
    else:
        print("  ✗ PostgreSQL")
        print("    (Not enabled)")
        print()

    # Temporal
    if state.services_enabled.get("temporal"):
        print("  ✓ Temporal")
        print(f"    Frontend Port:     {state.temporal_frontend_port}")
        print(f"    UI Port:           {state.temporal_ui_port}")
        print(f"    Namespace:         {state.temporal_namespace}")
        if hasattr(state, 'temporal_history_retention_days'):
            print(f"    Retention:         {state.temporal_history_retention_days} days")
        print()
    else:
        print("  ✗ Temporal")
        print("    (Not enabled)")
        print()

    # Deployment Configuration
    print("━" * 64)
    print("Deployment Configuration")
    print("━" * 64)
    print()
    print(f"  Method:              {state.deployment_method.replace('-', ' ').title()}")
    print(f"  Auto-start:          {'Yes' if state.auto_start else 'No'}")
    print()

    # Generated Files
    print("━" * 64)
    print("Generated Files")
    print("━" * 64)
    print()

    config_dir = Path.home() / ".config" / "mycelium"
    print(f"  Configuration:       {config_dir / 'mycelium.yaml'}")

    if state.deployment_method == "docker-compose":
        print("  Docker Compose:      docker-compose.yml")
        print("  Environment:         .env")
    elif state.deployment_method == "kubernetes":
        print("  Kubernetes:          k8s/*.yaml")
    elif state.deployment_method == "systemd":
        print("  systemd Units:       systemd/*.service")
    elif state.deployment_method == "manual":
        print("  Scripts:             scripts/start.sh, scripts/stop.sh")

    print()

    # Build action choices
    choices = [
        Choice(value="confirm", name="Confirm and generate configuration"),
    ]

    # Add edit options
    choices.append(Choice(value="edit_services", name="Edit services"))
    choices.append(Choice(value="edit_deployment", name="Edit deployment"))

    if state.setup_mode == "custom":
        choices.append(Choice(value="edit_advanced", name="Edit advanced settings"))

    choices.append(Choice(value="cancel", name="Cancel and exit"))

    # Get user action
    action = inquirer.select(
        message="What would you like to do?",
        choices=choices,
        default="confirm",
    ).execute()

    # Handle confirmation
    if action == "confirm":
        print()
        print("Generating configuration files...")
        return "confirm"

    # Handle cancel
    if action == "cancel":
        print()
        cancel_confirm = inquirer.select(
            message="Are you sure you want to cancel?",
            choices=[
                Choice(value="back", name="Go back to review"),
                Choice(value="save", name="Save and exit (resume later)"),
                Choice(value="exit", name="Cancel and exit (discard progress)"),
            ],
            default="back",
        ).execute()

        if cancel_confirm == "back":
            # Recursively call to show review again
            return review_screen(state)
        elif cancel_confirm == "save":
            return "save"
        else:
            return "cancel"

    return action


def display_review_summary(state: WizardState) -> None:
    """Display a formatted review summary.

    Helper function to show configuration summary.

    Args:
        state: Current wizard state
    """
    # This is a helper that can be called from other parts of the code
    # to show the summary without prompting for action
    pass
```

## Accessibility Notes

- Clear section headers with separators
- Hierarchical information display
- Status icons for enabled/disabled
- Full paths shown for generated files
- Keyboard navigation for all actions
- Multiple edit entry points
- Confirmation dialogs prevent accidents

## Design Rationale

This screen serves as a final checkpoint:

1. **Transparency**: Show complete configuration before committing
1. **Safety**: Multiple edit options prevent mistakes
1. **Clarity**: Organized sections for easy scanning
1. **Flexibility**: Jump back to any section for edits
1. **Confirmation**: Explicit confirmation before generation
1. **Recovery**: Save and exit option preserves progress
1. **Visibility**: Shows generated file paths upfront

## Example Output

### Quick Setup with Redis + PostgreSQL

```
Project Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Project Name:        mycelium
  Setup Mode:          Quick Setup

Enabled Services
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✓ Redis
    Port:              6379
    Persistence:       Enabled
    Max Memory:        256mb

  ✓ PostgreSQL
    Port:              5432
    Database:          mycelium
    Max Connections:   100

  ✗ Temporal
    (Not enabled)

Deployment Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Method:              Docker Compose
  Auto-start:          Yes
```

### Custom Setup with All Services

```
Project Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Project Name:        production-agents
  Setup Mode:          Custom Setup

Enabled Services
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✓ Redis
    Port:              6379
    Persistence:       Enabled
    Max Memory:        1gb

  ✓ PostgreSQL
    Port:              5432
    Database:          production_agents
    Max Connections:   200

  ✓ Temporal
    Frontend Port:     7233
    UI Port:           8080
    Namespace:         production
    Retention:         30 days

Deployment Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Method:              Kubernetes
  Auto-start:          N/A
```
