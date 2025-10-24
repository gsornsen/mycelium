# Task 4.2A: Design InquirerPy Screen Specifications

**Agent**: frontend-developer
**Duration**: 4 hours
**Status**: READY TO START
**Parallel**: Can run alongside Task 4.1

## Mission

Design detailed specifications for all 7 wizard screens using InquirerPy components. Create comprehensive validation rules, help text, and interaction patterns that guide users through Mycelium setup with clarity and confidence.

## Context

### Dependencies Complete
- ✅ M01 Environment Isolation
- ✅ M02 Configuration System
- ✅ M03 Service Detection

### Your Role
You are specifying the user interface for each wizard screen. Your specifications will be implemented by python-pro in Task 4.2B. Focus on UX, not implementation details.

### Target Library
InquirerPy - Modern, beautiful CLI prompts for Python
- Components: select, checkbox, text, confirm, number
- Features: Validation, help text, colors, keyboard shortcuts
- Rich integration for formatting

## Screen Specifications

### Screen 1: Welcome Screen

**Purpose**: Orient user and show detection results

**Component**: Informational display + confirm

**Layout**:
```
╔═══════════════════════════════════════════════════════════╗
║        🔍 System Detection Results                        ║
╠═══════════════════════════════════════════════════════════╣
║ Service    │ Status              │ Details               ║
║────────────┼─────────────────────┼───────────────────────║
║ Docker     │ ✓ Available         │ 24.0.6 (Compose 2.x) ║
║ Redis      │ ✓ Running           │ localhost:6379 (7.0) ║
║ PostgreSQL │ ○ Available         │ localhost:5432       ║
║ Temporal   │ ✗ Not found         │ Not installed        ║
║ GPU        │ ✓ Available         │ NVIDIA RTX 3090      ║
╚═══════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════╗
║  Welcome to Mycelium Onboarding!                          ║
║                                                            ║
║  This wizard will guide you through setting up your       ║
║  multi-agent coordination infrastructure. We've detected  ║
║  your system and will recommend the best configuration.   ║
║                                                            ║
║  ⏱️  Estimated time: 5 minutes                            ║
║  📁 Config location: ~/.config/mycelium/mycelium.yaml    ║
╚═══════════════════════════════════════════════════════════╝

? Ready to begin? (Y/n)
```

**Interaction**:
- Display detection summary table
- Show welcome panel with expectations
- Confirm prompt (default: Yes)
- Enter → proceed, Ctrl+C → exit

**Help Text**: None needed (informational)

**Validation**: None (confirm only)

**Defaults**: Yes

---

### Screen 2: Service Selection

**Purpose**: Choose which coordination services to enable

**Component**: checkbox (multi-select)

**Layout**:
```
╔═══════════════════════════════════════════════════════════╗
║  Service Selection                                         ║
║                                                            ║
║  Select which coordination services to enable:            ║
║  (Space to toggle, Enter to confirm, ↑/↓ to navigate)    ║
╚═══════════════════════════════════════════════════════════╝

  ❯ ◉ Redis - Pub/Sub messaging and state management
      ⓘ Detected and running on localhost:6379
    ◯ PostgreSQL - Persistent data storage
      ⓘ Detected but not running on localhost:5432
    ◯ Temporal - Workflow orchestration
      ⓘ Not detected - will be deployed if selected
    ◉ TaskQueue - Task distribution (MCP)
      ⓘ Always available via MCP

───────────────────────────────────────────────────────────
💡 Tip: Start with Redis + TaskQueue for basic coordination

? Select services (Space to toggle, Enter to confirm):
```

**Interaction**:
- Checkbox list with InquirerPy
- Space bar toggles selection
- Up/Down arrows navigate
- Enter confirms selection
- Each option shows status from detection

**Help Text**:
- Redis: "Fast pub/sub messaging and state management. Recommended for real-time coordination."
- PostgreSQL: "Persistent data storage for agent state, workflows, and history."
- Temporal: "Workflow orchestration for complex multi-step agent tasks."
- TaskQueue: "Task distribution system built on MCP. Always available, no deployment needed."

**Validation**:
```python
def validate_service_selection(selected: list[str]) -> bool:
    if len(selected) == 0:
        return False  # Error: "You must select at least one service"
    return True
```

**Defaults**:
- Redis: Pre-checked if detected and running
- PostgreSQL: Pre-checked if detected and running
- Temporal: Pre-checked if detected and running
- TaskQueue: Always pre-checked (always available)

**Error Messages**:
- "⚠️  You must select at least one service"

---

### Screen 3: Service Configuration

**Purpose**: Configure each selected service's parameters

**Component**: Multiple prompts (dynamic based on selection)

**Layout** (example for Redis):
```
╔═══════════════════════════════════════════════════════════╗
║  Redis Configuration                                       ║
║                                                            ║
║  Configure Redis pub/sub and state management service     ║
╚═══════════════════════════════════════════════════════════╝

? Redis port: (6379) ▌
  ⓘ Port number for Redis server (1-65535)
  Current: localhost:6379 detected

? Enable persistence (RDB snapshots): (Y/n)
  ⓘ Save data to disk for durability

? Max memory limit: (256mb) ▌
  ⓘ Maximum memory Redis can use (e.g., 256mb, 1gb, 2gb)

───────────────────────────────────────────────────────────
✓ Redis configured: port 6379, persistence enabled, 256mb max
```

**For PostgreSQL**:
```
╔═══════════════════════════════════════════════════════════╗
║  PostgreSQL Configuration                                  ║
╚═══════════════════════════════════════════════════════════╝

? PostgreSQL port: (5432) ▌
? Database name: (mycelium) ▌
? Max connections: (100) ▌
```

**For Temporal**:
```
╔═══════════════════════════════════════════════════════════╗
║  Temporal Configuration                                    ║
╚═══════════════════════════════════════════════════════════╝

? Frontend port (gRPC): (7233) ▌
? UI port (HTTP): (8080) ▌
? Namespace: (default) ▌
```

**Interaction**:
- Text input for ports (with validation)
- Confirm for yes/no options
- Text input for names and limits
- Show detected values as defaults
- Validate immediately on input

**Help Text**:
- Port: "Port number between 1 and 65535. Uses standard default if not changed."
- Persistence: "Recommended for production. Saves state to disk."
- Max memory: "Prevents Redis from consuming all system memory."
- Database name: "PostgreSQL database name. Will be created if doesn't exist."
- Connections: "Maximum simultaneous connections to PostgreSQL."

**Validation**:
```python
def validate_port(port: str) -> bool:
    try:
        p = int(port)
        if 1 <= p <= 65535:
            return True
    except ValueError:
        pass
    return False  # Error: "Port must be a number between 1 and 65535"

def validate_memory(mem: str) -> bool:
    import re
    if re.match(r'^\d+(mb|gb|MB|GB)$', mem):
        return True
    return False  # Error: "Format: 256mb, 1gb, 2gb, etc."

def validate_identifier(name: str) -> bool:
    if name.replace('_', '').replace('-', '').isalnum():
        return True
    return False  # Error: "Only letters, numbers, hyphens, underscores allowed"
```

**Defaults**:
- Use detected values from M03
- Fall back to standard defaults if not detected
- Redis: port=6379, persistence=true, max_memory="256mb"
- PostgreSQL: port=5432, database="mycelium", max_connections=100
- Temporal: frontend_port=7233, ui_port=8080, namespace="default"

---

### Screen 4: Deployment Method

**Purpose**: Choose how to deploy services

**Component**: select (single choice)

**Layout** (Docker available):
```
╔═══════════════════════════════════════════════════════════╗
║  Deployment Method                                         ║
║                                                            ║
║  Choose how to deploy and manage your services:          ║
╚═══════════════════════════════════════════════════════════╝

  ❯ Docker Compose (Recommended)
      Containerized services with automatic dependency management
      ✓ Easy to start/stop
      ✓ Isolated environments
      ✓ Automatic networking
      Requires: Docker 20.10+ and Docker Compose 2.x

    Justfile (Bare-metal)
      Direct deployment on your system
      ✓ No container overhead
      ✓ Direct system access
      ⚠️  Manual service management required

? Choose deployment method:
```

**Layout** (Docker NOT available):
```
╔═══════════════════════════════════════════════════════════╗
║  Deployment Method                                         ║
╚═══════════════════════════════════════════════════════════╝

⚠️  Docker not detected - defaulting to Justfile deployment

Justfile will manage services directly on your system.
You'll need to install and start services manually.

✓ Selected: Justfile deployment

Press Enter to continue...
```

**Interaction**:
- If Docker available: select between options
- If Docker NOT available: auto-select Justfile, show info, confirm
- Up/Down arrows navigate
- Enter confirms
- Show implications of each choice

**Help Text**:
- Docker Compose: "Best for most users. Containers provide isolation and easy management."
- Justfile: "For advanced users or when Docker unavailable. Requires manual setup."

**Validation**: None (always valid selection)

**Defaults**:
- If Docker available and running: "docker-compose"
- If Docker not available: "justfile" (auto-selected)

---

### Screen 5: Project Metadata

**Purpose**: Gather project identification information

**Component**: text inputs

**Layout**:
```
╔═══════════════════════════════════════════════════════════╗
║  Project Metadata                                          ║
║                                                            ║
║  Provide information about your Mycelium project          ║
╚═══════════════════════════════════════════════════════════╝

? Project name: (mycelium) ▌
  ⓘ Used for configuration and deployment files
  Must be alphanumeric with hyphens/underscores only

? Project description: (Multi-agent coordination system) ▌
  ⓘ Optional description for documentation (press Enter to skip)

───────────────────────────────────────────────────────────
✓ Project: mycelium
✓ Description: Multi-agent coordination system
```

**Interaction**:
- Text input for project name (required, validated)
- Text input for description (optional)
- Enter on empty description → use default
- Validate project name immediately

**Help Text**:
- Project name: "Identifies your Mycelium instance. Used in config files and deployments."
- Description: "Optional. Helps document your setup for team members."

**Validation**:
```python
def validate_project_name(name: str) -> bool:
    import re
    if re.match(r'^[a-zA-Z0-9_-]+$', name) and len(name) > 0:
        return True
    return False  # Error: "Must contain only letters, numbers, hyphens, and underscores"
```

**Defaults**:
- Project name: "mycelium"
- Description: "Multi-agent coordination system"

**Error Messages**:
- "⚠️  Project name cannot be empty"
- "⚠️  Must contain only alphanumeric characters, hyphens, and underscores"
- "⚠️  Invalid characters: space, special symbols not allowed"

---

### Screen 6: Configuration Review

**Purpose**: Show final configuration and confirm before saving

**Component**: Informational display + confirm

**Layout**:
```
╔═══════════════════════════════════════════════════════════╗
║  Configuration Review                                      ║
║                                                            ║
║  Please review your configuration before saving           ║
╚═══════════════════════════════════════════════════════════╝

┌───────────────────────────────────────────────────────────┐
│ Final Configuration                                        │
├───────────────────────────────────────────────────────────┤
│ Setting              │ Value                               │
├──────────────────────┼─────────────────────────────────────┤
│ Project Name         │ mycelium                            │
│ Deployment Method    │ Docker Compose                      │
│ Services Enabled     │ Redis, Temporal, TaskQueue          │
│                      │                                     │
│ Redis Configuration  │                                     │
│   Port               │ 6379                                │
│   Persistence        │ Enabled                             │
│   Max Memory         │ 256mb                               │
│                      │                                     │
│ Temporal Config      │                                     │
│   Frontend Port      │ 7233                                │
│   UI Port            │ 8080                                │
│   Namespace          │ default                             │
└───────────────────────────────────────────────────────────┘

Configuration will be saved to:
  📁 ~/.config/mycelium/mycelium.yaml

? Save this configuration? (Y/n)
  ⓘ Press 'n' to go back and make changes
```

**Interaction**:
- Display complete configuration table
- Show save location
- Confirm to save
- 'n' → option to select which step to edit
- Enter/Y → proceed to save
- Ctrl+C → cancel and exit

**Help Text**:
- "Review all settings carefully. You can edit the config file later if needed."

**Validation**: None (review only)

**Defaults**: Yes (confirm)

**Navigation** (if user selects 'n'):
```
╔═══════════════════════════════════════════════════════════╗
║  Go back to edit?                                          ║
╚═══════════════════════════════════════════════════════════╝

  ❯ Service Selection
    Service Configuration
    Deployment Method
    Project Metadata
    Cancel (exit without saving)

? Which step would you like to edit?
```

---

### Screen 7: Finalization

**Purpose**: Show success and next steps

**Component**: Informational display

**Layout**:
```
╔═══════════════════════════════════════════════════════════╗
║  ✓ Configuration Saved Successfully!                       ║
╚═══════════════════════════════════════════════════════════╝

Configuration saved to:
  📁 /home/user/.config/mycelium/mycelium.yaml

┌───────────────────────────────────────────────────────────┐
│ Next Steps                                                 │
├───────────────────────────────────────────────────────────┤
│ 1. Review configuration                                    │
│    $ cat ~/.config/mycelium/mycelium.yaml                │
│                                                            │
│ 2. Generate deployment files                              │
│    $ /mycelium-generate                                   │
│                                                            │
│ 3. Start services                                         │
│    $ docker-compose up -d       # Docker Compose          │
│    $ just up                    # Justfile                │
│                                                            │
│ 4. Verify services                                        │
│    $ /mycelium-status                                     │
└───────────────────────────────────────────────────────────┘

📚 Documentation: docs/guides/interactive-onboarding.md
🐛 Issues: https://github.com/gsornsen/mycelium/issues

Press Enter to exit...
```

**Interaction**:
- Display success panel
- Show config location
- List numbered next steps with commands
- Provide documentation links
- Wait for Enter to exit
- No validation or interaction needed

**Help Text**: None (informational only)

---

## Validation Rules Summary

Create comprehensive validation specification document:

**File**: `docs/projects/onboarding/M04_validation_rules.md`

```markdown
# Validation Rules for M04 Wizard

## Service Selection
- **Rule**: At least one service must be selected
- **Message**: "⚠️  You must select at least one service"
- **Type**: List length validation
- **When**: On attempt to proceed from service selection

## Port Numbers
- **Rule**: Must be integer between 1 and 65535
- **Message**: "⚠️  Port must be a number between 1 and 65535"
- **Type**: Range validation
- **When**: On Redis port, PostgreSQL port, Temporal ports

## Memory Limits
- **Rule**: Must match pattern `\d+(mb|gb|MB|GB)`
- **Message**: "⚠️  Format: 256mb, 1gb, 2gb, etc."
- **Type**: Pattern validation
- **When**: On Redis max_memory field

## Project Name
- **Rule**: Must match pattern `^[a-zA-Z0-9_-]+$` and non-empty
- **Message**: "⚠️  Must contain only letters, numbers, hyphens, and underscores"
- **Type**: Pattern validation
- **When**: On project name field

## Database Name
- **Rule**: Must be valid identifier (alphanumeric with underscores)
- **Message**: "⚠️  Invalid database name. Use letters, numbers, underscores only"
- **Type**: Identifier validation
- **When**: On PostgreSQL database field

## Connection Count
- **Rule**: Must be positive integer, typically 10-1000
- **Message**: "⚠️  Must be a positive number (typically 10-1000)"
- **Type**: Range validation
- **When**: On PostgreSQL max_connections
```

## Color Scheme & Formatting

**File**: `docs/projects/onboarding/M04_style_guide.md`

```markdown
# M04 Wizard Style Guide

## Colors (Rich Library)

### Status Indicators
- ✓ Available/Success: `[green]`
- ○ Available (not running): `[yellow]`
- ✗ Not found: `[dim]`
- ⚠️  Warning: `[yellow]`
- ⚠️  Error: `[red]`

### UI Elements
- Headers: `[bold cyan]`
- Help text: `[dim]`
- Examples: `[green]`
- Commands: `[bold]`
- Paths: `[cyan]`

### Panels and Boxes
- Information panels: `border_style="blue"`
- Success panels: `border_style="green"`
- Error panels: `border_style="red"`
- Warning panels: `border_style="yellow"`

## Typography

### Headers
- Main headers: Bold, cyan
- Sub-headers: Bold, white
- Section titles: Cyan, not bold

### Body Text
- Normal text: White (default)
- Help text: Dim
- Emphasis: Bold
- Code: Bold

## Icons & Symbols
- ✓ : Success, available, enabled
- ✗ : Not found, disabled
- ○ : Available but not active
- ⚠️  : Warning
- 📁 : File path
- ⏱️  : Time estimate
- 💡 : Tip
- 📚 : Documentation
- 🐛 : Issues/bugs
- ⓘ : Information

## Layout Principles

### Spacing
- One blank line between sections
- Two blank lines before major sections
- Consistent indentation (2 spaces)

### Alignment
- Left-align all text
- Table columns aligned
- Lists with hanging indent

### Width
- Maximum line width: 60 characters for readability
- Panels: 63 characters (including borders)
- Wrap long text appropriately
```

## Accessibility Checklist

**File**: `docs/projects/onboarding/M04_accessibility.md`

```markdown
# Accessibility Requirements

## Keyboard Navigation
- [ ] All interactions keyboard-only (no mouse required)
- [ ] Tab/Arrow keys for navigation
- [ ] Space for selection (checkboxes)
- [ ] Enter for confirmation
- [ ] Ctrl+C for cancellation

## Screen Reader Support
- [ ] All prompts have clear labels
- [ ] Help text available for all inputs
- [ ] Error messages descriptive
- [ ] Status indicators have text descriptions
- [ ] Table data properly structured

## Visual Clarity
- [ ] No reliance on color alone for information
- [ ] Icons paired with text
- [ ] High contrast text
- [ ] Clear visual hierarchy
- [ ] Consistent formatting

## Cognitive Load
- [ ] Progressive disclosure (not overwhelming)
- [ ] Clear instructions at each step
- [ ] Sensible defaults provided
- [ ] Validation immediate and clear
- [ ] Can navigate back to fix mistakes

## Error Handling
- [ ] Errors explain what's wrong
- [ ] Errors suggest how to fix
- [ ] No data loss on error
- [ ] Can retry or cancel
- [ ] Graceful degradation
```

## Deliverables

### 1. Screen Specifications Document
**File**: `docs/projects/onboarding/M04_screen_specifications.md`

All 7 screens with:
- Purpose
- Component type
- Layout (ASCII mockup)
- Interaction patterns
- Help text
- Validation rules
- Defaults
- Error messages

### 2. Validation Rules Document
**File**: `docs/projects/onboarding/M04_validation_rules.md`

Comprehensive validation specifications for all inputs

### 3. Style Guide
**File**: `docs/projects/onboarding/M04_style_guide.md`

Color scheme, typography, icons, layout principles

### 4. Accessibility Checklist
**File**: `docs/projects/onboarding/M04_accessibility.md`

Accessibility requirements and validation

### 5. Implementation Handoff
**File**: `docs/projects/onboarding/M04_implementation_notes.md`

Notes for python-pro (Task 4.2B):
- InquirerPy component mapping
- Rich formatting examples
- Validation function signatures
- Edge cases to handle
- Testing recommendations

## Quality Standards

### Specification Quality
- [ ] All 7 screens fully specified
- [ ] Validation rules comprehensive
- [ ] Help text clear and helpful
- [ ] Error messages actionable
- [ ] Defaults sensible

### Documentation Quality
- [ ] Clear and thorough
- [ ] Examples provided
- [ ] Edge cases considered
- [ ] Accessible to implementer
- [ ] Ready for review

### UX Quality
- [ ] Progressive disclosure
- [ ] Intelligent defaults
- [ ] Clear communication
- [ ] Safety & confidence
- [ ] Accessibility compliant

## Success Criteria

- [ ] All 7 screens specified in detail
- [ ] Validation rules documented
- [ ] Style guide complete
- [ ] Accessibility checklist done
- [ ] Implementation handoff notes ready
- [ ] python-pro can implement from specs
- [ ] No ambiguity in requirements
- [ ] All deliverables created

## Timeline

**Hour 0-1**: Study InquirerPy and Rich libraries
**Hour 1-2**: Design screens 1-4
**Hour 2-3**: Design screens 5-7
**Hour 3-4**: Create validation rules, style guide, documentation

## Next Steps After Completion

1. Submit all deliverables
2. Review with python-pro
3. Incorporate any feedback
4. Approve for Task 4.2B implementation
5. Support python-pro during implementation

## Reference Materials

### InquirerPy Documentation
- Components: https://inquirerpy.readthedocs.io/
- Examples: Check examples/ in InquirerPy repo
- Validation: Built-in validators and custom

### Rich Documentation
- Console: https://rich.readthedocs.io/en/stable/console.html
- Tables: https://rich.readthedocs.io/en/stable/tables.html
- Panels: https://rich.readthedocs.io/en/stable/panel.html
- Styling: https://rich.readthedocs.io/en/stable/style.html

---

**Status**: READY TO START
**Agent**: frontend-developer
**Estimated Completion**: +4 hours
**Parallel With**: Task 4.1
**Blocks**: Task 4.2B (implementation)
