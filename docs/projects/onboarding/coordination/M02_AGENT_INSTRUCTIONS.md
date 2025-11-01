# M02 Configuration System - Agent Instructions

## Mission Brief

You are working on **M02 Configuration System**, a critical milestone that builds the type-safe configuration layer for
the Mycelium onboarding system. This milestone enables future interactive onboarding (M04) and deployment generation
(M05).

## Context

### What We've Built (M01 - COMPLETE)

- XDG directory management: `/home/gerald/git/mycelium/mycelium_onboarding/xdg_dirs.py`
- Hierarchical config loading: `/home/gerald/git/mycelium/mycelium_onboarding/config_loader.py`
- Environment validation: `/home/gerald/git/mycelium/mycelium_onboarding/env_validator.py`
- Test coverage: 80%+ with comprehensive examples

### What We're Building (M02 - THIS MILESTONE)

- Pydantic configuration schema with validation
- Configuration manager for loading/saving
- Schema migration framework for evolution
- CLI commands for config management
- Comprehensive documentation and examples

## Available Resources

### Existing Infrastructure

```python
# XDG directories (from M01)
from mycelium_onboarding.xdg_dirs import get_config_dir, get_data_dir

# Config loading (from M01)
from mycelium_onboarding.config_loader import find_config_file, get_config_path

# Environment validation (from M01)
from mycelium_onboarding.env_validator import validate_environment
```

### File Locations

- Project root: `/home/gerald/git/mycelium/`
- Source: `/home/gerald/git/mycelium/mycelium_onboarding/`
- Tests: `/home/gerald/git/mycelium/tests/`
- Docs: `/home/gerald/git/mycelium/docs/`

## Quality Standards

### Test Coverage

- Schema validation: ≥85%
- ConfigManager: ≥85%
- CLI commands: ≥80%
- Migrations: ≥90% (critical path)

### Code Quality

- Type hints on all functions
- Docstrings on all public APIs
- Follow existing patterns from M01
- Comprehensive error messages
- Appropriate logging levels

### Documentation

- Usage examples in docstrings
- User-facing documentation for all features
- Troubleshooting guides
- Migration instructions

## Communication Protocol

### Progress Updates

Report every 2 hours or at major checkpoints:

```markdown
## Progress Update - [Task Number]
**Time**: [Current time]
**Status**: [in_progress/blocked/complete]
**Completion**: [X%]
**Completed**:
- Item 1
- Item 2

**In Progress**:
- Current work item

**Next Steps**:
- Upcoming work

**Blockers**: [None or describe]
```

### Blocker Escalation

Report immediately if blocked:

```markdown
## BLOCKER - [Task Number]
**Issue**: [Description]
**Impact**: [Time impact]
**Assistance Needed**: [What help is needed]
```

### Task Completion

Notify with deliverables:

```markdown
## Task Complete - [Task Number]
**Deliverables**:
- [File path 1]
- [File path 2]

**Test Coverage**: [X%]
**Tests Pass**: [Yes/No]
**Ready for Review**: [Yes/No]

**Notes**: [Any important notes]
```

## Agent-Specific Instructions

### For python-pro

You will handle Tasks 2.1, 2.2, 2.3, and 2.4 (all implementation tasks).

#### Task 2.1: Design Configuration Schema (6 hours)

**Start**: Immediately **File**: `/home/gerald/git/mycelium/mycelium_onboarding/config/schema.py`

**Implementation Guide**:

1. Create `config/` directory in `mycelium_onboarding/`
1. Implement Pydantic models as specified in milestone doc
1. Use Pydantic v2 features (BaseModel, Field, field_validator)
1. Create comprehensive unit tests
1. Ensure ≥85% test coverage

**Key Classes to Implement**:

- `MyceliumConfig` (top-level)
- `DeploymentConfig`
- `ServicesConfig`
- `RedisConfig`, `PostgresConfig`, `TemporalConfig`
- `DeploymentMethod` enum

**Testing Focus**:

- Field validation (port ranges, project name format)
- Default values
- Serialization/deserialization
- Invalid input handling

#### Task 2.2: Configuration Loading & Saving (6 hours)

**Start**: After Task 2.1 complete **File**: `/home/gerald/git/mycelium/mycelium_onboarding/config/manager.py`

**Implementation Guide**:

1. Create `ConfigManager` class with class methods
1. Integrate with existing `config_loader.py` functions
1. Use YAML for serialization (yaml.safe_load/yaml.dump)
1. Comprehensive error handling
1. Test coverage ≥85%

**Key Methods to Implement**:

- `load(prefer_project=True)` - Load with hierarchical fallback
- `load_from_path(path)` - Load from specific path
- `save(config, project_local=False)` - Save with validation
- `exists(prefer_project=True)` - Check if config exists
- `get_config_location(prefer_project=True)` - Get save location

**Integration Points**:

- Use `find_config_file()` from config_loader
- Use `get_config_path()` from config_loader
- Import schema from `schema.py`

#### Task 2.3: Schema Migration Framework (8 hours)

**Start**: After Tasks 2.1 and 2.2 complete **File**:
`/home/gerald/git/mycelium/mycelium_onboarding/config/migrations.py`

**Implementation Guide**:

1. Create migration registry using decorator pattern
1. Implement version detection
1. Implement migration path finding (start with linear)
1. Integrate with ConfigManager.load_from_path()
1. Test coverage ≥90% (critical path)

**Key Functions to Implement**:

- `register_migration(from_version, to_version)` - Decorator
- `migrate_config(config_dict)` - Apply migrations
- `_find_migration_path(from_version, to_version)` - Path finding
- `migrate_0_9_to_1_0(config)` - Example migration

**Testing Focus**:

- Migration registration
- Version detection
- Migration application
- User data preservation
- Error handling

#### Task 2.4: Configuration CLI Commands (4 hours)

**Start**: Can start after Task 2.1 (parallel with 2.2) **File**:
`/home/gerald/git/mycelium/mycelium_onboarding/cli/config_commands.py`

**Implementation Guide**:

1. Create Click command group: `@click.group(name="config")`
1. Implement 4 commands: show, validate, location, init
1. Integrate with ConfigManager
1. Test coverage ≥80%

**Commands to Implement**:

- `show` - Display current config (YAML/JSON format)
- `validate` - Validate config file
- `location` - Show config file location
- `init` - Initialize default config

**CLI Integration**:

- Commands should be added to main CLI group
- Follow existing CLI patterns
- Use Click options for flags

### For platform-engineer

You will handle Task 2.5 (documentation).

#### Task 2.5: Configuration Documentation & Examples (4 hours)

**Start**: After all implementation tasks complete **Files**:

- `/home/gerald/git/mycelium/docs/configuration-reference.md`
- `/home/gerald/git/mycelium/docs/examples/` directory

**Documentation Structure**:

1. **Configuration Reference**:

   - File locations (XDG compliance)
   - Complete schema reference
   - All configuration options with examples
   - Precedence rules

1. **Usage Examples**:

   - Minimal configuration
   - Docker Compose deployment
   - Justfile deployment
   - Custom ports configuration
   - Service-specific configs

1. **CLI Documentation**:

   - All commands with examples
   - Flag descriptions
   - Common workflows

1. **Migration Guide**:

   - How migrations work
   - Manual migration steps
   - Version history

1. **Troubleshooting**:

   - Common validation errors
   - File not found issues
   - YAML syntax problems
   - Permission issues

**Example Files to Create**:

- `docs/examples/minimal-config.yaml`
- `docs/examples/docker-compose-config.yaml`
- `docs/examples/justfile-config.yaml`
- `docs/examples/custom-ports-config.yaml`

## Success Criteria

### Task Completion Checklist

- [ ] All deliverable files created
- [ ] All tests passing
- [ ] Test coverage meets targets
- [ ] Type checking passes (mypy)
- [ ] Linting passes (ruff)
- [ ] Documentation complete
- [ ] Examples validated
- [ ] Integration tests pass

### Milestone Exit Criteria (from M02 milestone doc)

- [ ] Configuration Schema: Complete with validation
- [ ] Configuration Manager: Load/save working
- [ ] Schema Migrations: Framework implemented
- [ ] CLI Commands: All 4 commands working
- [ ] Testing: ≥85% coverage overall
- [ ] Documentation: Complete reference + examples

## Getting Started

### For python-pro (Task 2.1 - STARTS NOW)

1. **Read the full milestone document**:

   - `/home/gerald/git/mycelium/docs/projects/onboarding/milestones/M02_CONFIGURATION_SYSTEM.md`

1. **Review existing infrastructure**:

   - Read `xdg_dirs.py` to understand directory management
   - Read `config_loader.py` to understand hierarchical loading
   - Review existing test patterns

1. **Create directory structure**:

   ```bash
   mkdir -p /home/gerald/git/mycelium/mycelium_onboarding/config
   mkdir -p /home/gerald/git/mycelium/tests/config
   ```

1. **Implement schema.py**:

   - Follow the detailed implementation in milestone doc (lines 94-181)
   - Start with enums and base classes
   - Add validators
   - Write tests as you go

1. **Report progress**:

   - Initial progress update after 2 hours
   - Completion notification when done

### For Other Agents

Wait for python-pro to complete prerequisites:

- **Task 2.2**: Needs Task 2.1 complete
- **Task 2.3**: Needs Tasks 2.1 and 2.2 complete
- **Task 2.4**: Can start after Task 2.1 (will be notified)
- **Task 2.5**: Needs all tasks complete (will be notified)

## Questions?

If you have questions or need clarification:

1. Check the milestone document first
1. Review existing M01 code for patterns
1. Ask multi-agent-coordinator for guidance

______________________________________________________________________

**Ready to Execute**: YES **First Agent**: python-pro (Task 2.1) **Coordination Active**: multi-agent-coordinator
monitoring

Let's build an excellent configuration system!
