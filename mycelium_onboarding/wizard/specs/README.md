# Wizard Screen Specifications

This directory contains detailed specifications for all screens in the Mycelium interactive onboarding wizard.

## Overview

The wizard guides users through a 7-screen flow to configure their Mycelium environment. Each screen is designed to be friendly, accessible, and informative.

## Screen Flow

```
WELCOME → DETECTION → SERVICES → DEPLOYMENT → ADVANCED* → REVIEW → COMPLETE
                                                   ↓
                                            (Quick Setup skips)
```

\* The ADVANCED screen is only shown in Custom Setup mode.

## Screens

### 1. [Welcome](screen_welcome.md)
**Purpose**: Introduction and setup mode selection

**Key Features**:
- Project overview
- Quick vs Custom setup choice
- Exit confirmation

**Duration**: 30 seconds

---

### 2. [Detection](screen_detection.md)
**Purpose**: Automatic service detection

**Key Features**:
- Real-time progress indicators
- Detection results with versions
- Re-run capability
- Pre-populates configuration

**Duration**: 2-5 seconds (detection time)

---

### 3. [Services](screen_services.md)
**Purpose**: Service selection and basic configuration

**Key Features**:
- Project name input
- Service enable/disable checkboxes
- Port configuration
- Database name setup
- Smart defaults from detection

**Duration**: 1-2 minutes

---

### 4. [Deployment](screen_deployment.md)
**Purpose**: Deployment method selection

**Key Features**:
- Docker Compose (recommended)
- Kubernetes
- systemd
- Manual
- Prerequisite checking
- Auto-start option

**Duration**: 30-60 seconds

---

### 5. [Advanced](screen_advanced.md) *(Custom Setup only)*
**Purpose**: Advanced service-specific settings

**Key Features**:
- Redis: Persistence, memory limits
- PostgreSQL: Max connections
- Temporal: Namespace, retention
- Optional skip with defaults

**Duration**: 1-2 minutes

---

### 6. [Review](screen_review.md)
**Purpose**: Configuration summary and confirmation

**Key Features**:
- Complete configuration display
- Jump back to edit any section
- Save and exit option
- Generated files preview

**Duration**: 1-2 minutes

---

### 7. [Complete](screen_complete.md)
**Purpose**: Success message and next steps

**Key Features**:
- Success confirmation
- Generated files list
- Deployment-specific next steps
- Service URLs
- Useful commands
- Support links

**Duration**: Read-only, exit when ready

---

## Design Principles

### 1. Accessibility First
- Keyboard-only navigation
- Screen reader friendly
- Clear visual hierarchy
- No color-only indicators

### 2. Progressive Disclosure
- Show only relevant options
- Quick Setup hides complexity
- Custom Setup reveals all options
- Help text available but not intrusive

### 3. Smart Defaults
- Detection results pre-populate settings
- Industry-standard ports
- Sensible configuration values
- Minimal required input

### 4. Error Prevention
- Validation on all inputs
- Clear error messages
- Confirmation dialogs
- Easy error recovery

### 5. Flexibility
- Back navigation (except Welcome/Complete)
- Jump to edit from Review
- Save and resume capability
- Re-run detection option

### 6. Transparency
- Show what's happening
- Explain prerequisites
- Display generated files
- Provide clear next steps

## User Flows

### Quick Setup Flow (2-3 minutes)
```
WELCOME (Quick)
  ↓
DETECTION (automatic)
  ↓
SERVICES (enable Redis + PostgreSQL)
  ↓
DEPLOYMENT (Docker Compose)
  ↓
REVIEW (confirm)
  ↓
COMPLETE
```

### Custom Setup Flow (4-5 minutes)
```
WELCOME (Custom)
  ↓
DETECTION (automatic)
  ↓
SERVICES (configure all)
  ↓
DEPLOYMENT (choose method)
  ↓
ADVANCED (fine-tune settings)
  ↓
REVIEW (confirm, maybe edit)
  ↓
COMPLETE
```

### Edit Flow (from Review)
```
REVIEW
  ↓ (Edit Services)
SERVICES (modify)
  ↓ (Continue)
REVIEW (updated)
  ↓
COMPLETE
```

## Implementation Guidelines

### Screen Components

Each screen should implement:

1. **Header**: Title and description
2. **Content**: Inputs, displays, or results
3. **Help**: Context-sensitive help text
4. **Validation**: Input validation with clear errors
5. **Navigation**: Next/Back/Cancel options
6. **State**: Update WizardState on completion

### InquirerPy Widgets

Use these InquirerPy widgets:

- `inquirer.select()`: Single choice (radio)
- `inquirer.checkbox()`: Multiple choice
- `inquirer.text()`: Text input
- `inquirer.number()`: Numeric input
- `inquirer.confirm()`: Yes/No questions

### Validation Patterns

```python
# Text validation
validate=lambda x: bool(re.match(pattern, x)) or "Error message"

# Number validation
min_allowed=1, max_allowed=65535

# Required field
validate=EmptyInputValidator("Field is required")

# Custom validator
validate=lambda x: len(x) > 0 or "Cannot be empty"
```

### State Management

Update `WizardState` at end of each screen:

```python
def screen_function(state: WizardState) -> str:
    # ... display and get input ...

    # Update state
    state.field = value
    state.current_step = WizardStep.NEXT

    return "continue"  # or "back"
```

## Testing Screens

Each screen should have tests for:

- ✓ Display rendering
- ✓ Input validation
- ✓ State updates
- ✓ Navigation options
- ✓ Error handling
- ✓ Help text display

## File Structure

```
specs/
├── README.md                  # This file
├── screen_welcome.md          # Screen 1 spec
├── screen_detection.md        # Screen 2 spec
├── screen_services.md         # Screen 3 spec
├── screen_deployment.md       # Screen 4 spec
├── screen_advanced.md         # Screen 5 spec
├── screen_review.md           # Screen 6 spec
└── screen_complete.md         # Screen 7 spec
```

## ASCII Art Guidelines

Use these box-drawing characters:

```
╔═══╗  Top borders
║   ║  Side borders
╠═══╣  Middle dividers
╚═══╝  Bottom borders
━━━   Section separators
```

Status indicators:
```
✓  Success / Enabled
✗  Failure / Disabled
⚠️  Warning
⏳  Loading / In Progress
🎉  Celebration
```

## Keyboard Navigation

Standard keys:
- `↑/↓`: Navigate options
- `Space`: Select/deselect (checkbox)
- `Enter`: Confirm selection
- `Esc`: Cancel (if supported)
- `?`: Show help (if supported)
- `Ctrl+C`: Exit wizard

## Responsive Design

Screens should work with:
- Minimum width: 64 characters
- Recommended width: 80 characters
- Maximum width: 120 characters

Use dynamic padding for centering:
```python
width = shutil.get_terminal_size().columns
padding = (width - 64) // 2
```

## Error Handling

All screens should handle:

1. **Keyboard Interrupt** (Ctrl+C):
   ```python
   try:
       result = inquirer.select(...).execute()
   except KeyboardInterrupt:
       print("\n\nWizard cancelled by user.")
       sys.exit(0)
   ```

2. **Validation Errors**:
   - Show inline with input
   - Provide correction guidance
   - Don't advance until valid

3. **System Errors**:
   - Graceful degradation
   - Clear error messages
   - Offer recovery options

## Localization Readiness

While not implemented yet, screens are designed for future localization:

- All text externalized in specs
- No hardcoded strings in logic
- Clear message keys
- Length-flexible layouts

## Accessibility Features

Implemented accessibility features:

- **Keyboard Only**: No mouse required
- **Screen Readers**: Plain text, clear labels
- **Color Blind**: No color-only indicators
- **Motor Impaired**: Large click targets, no precise timing
- **Cognitive**: Clear language, logical flow, help text

## Future Enhancements

Potential improvements:

- [ ] Theme support (light/dark)
- [ ] Custom color schemes
- [ ] Mouse support
- [ ] GUI mode (web-based)
- [ ] Voice input
- [ ] Localization (i18n)
- [ ] Progress saving checkpoints
- [ ] Undo/redo capability
- [ ] Configuration templates

## Contributing

When adding or modifying screens:

1. Update this README
2. Follow existing patterns
3. Include complete spec
4. Add help text
5. Write tests
6. Update flow diagram
7. Test with real users

## References

- [InquirerPy Documentation](https://inquirerpy.readthedocs.io/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [CLI UX Guidelines](https://clig.dev/)
- [Rich Terminal Formatting](https://rich.readthedocs.io/)

## Support

Questions about screen specifications?

- Check existing screen specs for examples
- Review the flow diagram
- Ask in GitHub discussions
- Open an issue for clarifications
