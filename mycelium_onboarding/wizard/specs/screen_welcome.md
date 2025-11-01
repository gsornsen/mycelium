# Welcome Screen Specification

## Purpose

Introduce Mycelium, explain what the wizard does, and offer quick/custom setup options.

## Layout

```
╔══════════════════════════════════════════════════════════════╗
║                   Welcome to Mycelium! 🍄                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Mycelium is a distributed multi-agent coordination system  ║
║  for AI-powered workflows. This wizard will help you:       ║
║                                                              ║
║  • Detect available services (Docker, Redis, PostgreSQL)    ║
║  • Configure your environment                               ║
║  • Generate deployment configurations                        ║
║  • Set up your first project                                ║
║                                                              ║
║  Estimated time: 2-5 minutes                                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

? How would you like to proceed?
  > Quick Setup (recommended for first-time users)
    Custom Setup (advanced configuration options)
    Exit wizard
```

## User Inputs

### Setup Mode Selection

- **Field**: `setup_mode`
- **Type**: Single selection (radio)
- **Options**:
  - `quick`: Quick Setup (recommended for first-time users)
  - `custom`: Custom Setup (advanced configuration options)
  - `exit`: Exit wizard
- **Default**: `quick`
- **Required**: Yes

## Validation

### Setup Mode

- Must select one option
- If `exit` is selected, confirm with user before exiting

## Help Text

### Quick Setup

```
Quick Setup uses smart defaults and skips advanced configuration.
Perfect for getting started quickly. You can always reconfigure later.
```

### Custom Setup

```
Custom Setup gives you full control over all configuration options,
including service-specific settings, ports, and advanced features.
```

## Error Messages

No validation errors expected on this screen.

## Exit Confirmation

If user selects "Exit wizard":

```
? Are you sure you want to exit the wizard?
  > No, go back
    Yes, exit
```

## State Updates

On completion of this screen, update `WizardState`:

- `setup_mode`: Set to "quick" or "custom" based on user selection
- `current_step`: Advance to DETECTION

## Next Step Logic

- **Quick Setup** → Proceed to DETECTION screen
- **Custom Setup** → Proceed to DETECTION screen
- **Exit** → Confirm, then exit wizard (return code 0)

## InquirerPy Implementation

```python
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

def welcome_screen(state: WizardState) -> str:
    """Display welcome screen and get setup mode.

    Args:
        state: Current wizard state

    Returns:
        Selected setup mode: "quick", "custom", or "exit"
    """
    # Display welcome banner
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                   Welcome to Mycelium! 🍄                    ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║                                                              ║")
    print("║  Mycelium is a distributed multi-agent coordination system  ║")
    print("║  for AI-powered workflows. This wizard will help you:       ║")
    print("║                                                              ║")
    print("║  • Detect available services (Docker, Redis, PostgreSQL)    ║")
    print("║  • Configure your environment                               ║")
    print("║  • Generate deployment configurations                        ║")
    print("║  • Set up your first project                                ║")
    print("║                                                              ║")
    print("║  Estimated time: 2-5 minutes                                ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Get setup mode selection
    setup_mode = inquirer.select(
        message="How would you like to proceed?",
        choices=[
            Choice(
                value="quick",
                name="Quick Setup (recommended for first-time users)",
            ),
            Choice(
                value="custom",
                name="Custom Setup (advanced configuration options)",
            ),
            Choice(value="exit", name="Exit wizard"),
        ],
        default="quick",
        long_instruction="Use arrow keys to navigate, Enter to select",
    ).execute()

    # Handle exit confirmation
    if setup_mode == "exit":
        confirm_exit = inquirer.confirm(
            message="Are you sure you want to exit the wizard?",
            default=False,
        ).execute()

        if not confirm_exit:
            # Recursively call to show menu again
            return welcome_screen(state)

        return "exit"

    return setup_mode
```

## Accessibility Notes

- Screen reader friendly: All text is plain ASCII
- Keyboard navigation: Arrow keys + Enter
- Clear visual hierarchy with borders
- Helpful long instructions provided
- Confirmation dialog prevents accidental exit

## Design Rationale

This screen serves as the entry point and sets user expectations:

1. **Clear Branding**: Mycelium name and mushroom emoji create memorable identity
1. **Value Proposition**: Bullet points explain what the wizard does
1. **Time Estimate**: Sets realistic expectations (2-5 minutes)
1. **Choice Architecture**: Quick Setup as default reduces cognitive load
1. **Safe Exit**: Confirmation prevents accidental exits
1. **Inclusive Design**: Accessible to screen readers and keyboard-only users
