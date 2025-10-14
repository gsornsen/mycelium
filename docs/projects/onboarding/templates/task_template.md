# Task Template

Use this template to document individual tasks within milestones. Each task should be actionable, measurable, and have clear deliverables.

---

## Task [Milestone].[Number]: [Task Title]

**Effort**: [Hours] hours
**Agent**: [Lead agent name], [Support agent name(s)]
**Dependencies**: [Required tasks or milestones to complete first]
**Priority**: [P0 (Critical) | P1 (High) | P2 (Medium) | P3 (Low)]

### Overview

[2-3 sentences describing what this task accomplishes and why it's important to the milestone]

### Requirements

- **[Req-ID]**: [Specific requirement this task fulfills]
- **[Req-ID]**: [Another requirement]

### Implementation Details

[Detailed description of how this task should be implemented, including:]

- Architecture decisions
- Key components to build
- Integration points
- Technical constraints

### Code Examples

```python
# Example implementation demonstrating key concepts
# Include type hints, docstrings, and error handling

def example_function(param: str) -> dict:
    """Clear docstring explaining purpose and usage.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        Exception: When this error occurs
    """
    # Implementation here
    pass
```

### Testing Strategy

[How this task will be tested:]

- Unit tests for individual functions
- Integration tests for component interactions
- Manual testing scenarios (if applicable)

**Test Coverage Target**: [Percentage or specific test cases]

### Exit Criteria

- [ ] All code implemented and reviewed
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Integration points validated
- [ ] [Custom criterion specific to this task]

### Deliverables

1. **[Deliverable 1]**: [Description]
   - File path: `path/to/file.py`
   - Purpose: [What this file does]

2. **[Deliverable 2]**: [Description]
   - File path: `path/to/other_file.py`
   - Purpose: [What this file does]

### Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|-----------|--------|---------------------|
| [Risk description] | [Low\|Med\|High] | [Low\|Med\|High] | [How to mitigate] |

### Dependencies

**Blocks**:
- [Task or milestone that depends on this completing]

**Blocked By**:
- [Task or milestone that must complete first]

### Notes

[Any additional context, alternative approaches considered, or implementation notes]

---

## Example Usage

Below is a completed example of this template:

---

## Task 5.2: Justfile Generator Implementation

**Effort**: 4 hours
**Agent**: python-pro, devops-engineer
**Dependencies**: M05.1 (Docker Compose Generator)
**Priority**: P1 (High)

### Overview

Implement Justfile generator that creates task runner configuration for native service deployments. This enables users to manage locally-installed services (systemd, Homebrew) using a consistent interface similar to Docker Compose.

### Requirements

- **FR-5.3**: Generate valid Justfile for native deployment method
- **TR-5.2**: Use Jinja2 templating engine for generation
- **IR-5.2**: Accept MyceliumConfig as input

### Implementation Details

Create JustfileGenerator class following same pattern as DockerComposeGenerator:

- Template location: `templates/justfile.j2`
- Generator class in: `mycelium/generators/justfile.py`
- Supports service management commands: start, stop, status, logs
- Platform-aware (systemd on Linux, Homebrew on macOS)

### Code Examples

```python
# mycelium/generators/justfile.py
"""Justfile generator for native service deployment."""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from mycelium.config import MyceliumConfig


class JustfileGenerator:
    """Generates Justfile configuration from MyceliumConfig."""

    TEMPLATE_NAME = "justfile.j2"

    def __init__(self):
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate(self, config: MyceliumConfig) -> str:
        """Generate Justfile from configuration.

        Args:
            config: Configuration specifying enabled services

        Returns:
            Rendered Justfile content as string

        Raises:
            ValueError: If configuration is invalid for native deployment
        """
        if config.deployment.method != "justfile":
            raise ValueError(
                f"Config deployment method is {config.deployment.method}, "
                "expected 'justfile'"
            )

        template = self.env.get_template(self.TEMPLATE_NAME)

        context = {
            'config': config,
            'services': self._get_enabled_services(config),
        }

        return template.render(**context)

    def _get_enabled_services(self, config: MyceliumConfig) -> list[str]:
        """Extract list of enabled service names."""
        services = []
        if config.services.redis.enabled:
            services.append('redis')
        if config.services.postgres.enabled:
            services.append('postgres')
        return services
```

### Testing Strategy

Unit tests validate:
- Correct Justfile syntax generation
- Service commands (start, stop, status) included
- Platform detection (systemd vs Homebrew)
- Error handling for invalid configs

**Test Coverage Target**: 100% for JustfileGenerator class

### Exit Criteria

- [x] JustfileGenerator class implemented
- [x] Jinja2 template created (justfile.j2)
- [x] Unit tests written and passing (100% coverage)
- [x] Integration test with MyceliumConfig
- [x] Documentation added to API reference

### Deliverables

1. **JustfileGenerator Class**: Implementation
   - File path: `mycelium/generators/justfile.py`
   - Purpose: Generate Justfile from configuration

2. **Jinja2 Template**: Justfile template
   - File path: `mycelium/templates/justfile.j2`
   - Purpose: Template for Justfile generation

3. **Unit Tests**: Test suite
   - File path: `tests/unit/test_justfile_generator.py`
   - Purpose: Validate generator functionality

### Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|-----------|--------|---------------------|
| Platform differences (systemd vs Homebrew) | High | Medium | Template conditionals for platform-specific commands |
| Invalid Justfile syntax | Low | High | Syntax validation after generation |

### Dependencies

**Blocks**:
- Task 5.5: Slash command integration (/mycelium-generate)

**Blocked By**:
- Task 5.1: Docker Compose generator (pattern established)

### Notes

Consider adding support for other service managers (OpenRC, runit) in future versions. Current focus on systemd (Linux) and Homebrew (macOS) covers 90% of use cases.

---

*This template ensures consistent task documentation across all milestones.*
