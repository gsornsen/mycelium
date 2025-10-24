# M02 Configuration System - Coordination Plan

## Executive Summary

**Milestone**: M02 Configuration System
**Status**: ACTIVE
**Lead Coordinator**: multi-agent-coordinator
**Lead Agent**: python-pro
**Support Agents**: platform-engineer, technical-writer
**Duration**: 2 days (estimated 28 hours total)
**Dependencies**: M01 Environment Isolation (COMPLETE)

## Available Infrastructure

Building on M01 foundation:
- XDG directory management: `/home/gerald/git/mycelium/mycelium_onboarding/xdg_dirs.py`
- Hierarchical config loading: `/home/gerald/git/mycelium/mycelium_onboarding/config_loader.py`
- Environment validation: `/home/gerald/git/mycelium/mycelium_onboarding/env_validator.py`
- Test coverage: 80%+ on all M01 components

## Task Dependency Analysis

```
Task Graph:
┌──────────┐
│ Task 2.1 │  Design Configuration Schema (6h)
│ Schema   │  Agent: python-pro
│ Design   │  Blocks: 2.2, 2.3
└────┬─────┘
     │
     ├───────────────────┐
     │                   │
     ▼                   ▼
┌──────────┐      ┌──────────┐
│ Task 2.2 │      │ Task 2.4 │  Configuration CLI Commands (4h)
│ Config   │      │ CLI      │  Agent: python-pro
│ Manager  │      │ Commands │  Parallel with 2.2 after 2.1
└────┬─────┘      └──────────┘
     │
     ▼
┌──────────┐
│ Task 2.3 │  Schema Migration Framework (8h)
│ Schema   │  Agent: python-pro
│ Migration│  Depends on: 2.1, 2.2
└────┬─────┘
     │
     ▼
┌──────────┐
│ Task 2.5 │  Documentation & Examples (4h)
│ Docs     │  Agent: platform-engineer + technical-writer
│          │  Depends on: All tasks complete
└──────────┘

Critical Path: 2.1 → 2.2 → 2.3 → 2.5 (22 hours)
Parallel Opportunity: 2.4 can run alongside 2.2 (saves 4 hours)
```

## Coordination Strategy

### Phase 1: Design & Schema (Hours 0-6)
**Duration**: 6 hours
**Agent**: python-pro
**Focus**: Complete schema design

**Tasks**:
- Task 2.1: Design Configuration Schema
  - Define Pydantic models for all config options
  - Implement field validators
  - Set sensible defaults
  - Document schema structure

**Deliverables**:
- `/home/gerald/git/mycelium/mycelium_onboarding/config/schema.py`
- Schema design document
- Unit tests for schema validation

**Exit Criteria**:
- All schema fields documented
- Validators ensure data integrity
- Tests cover edge cases (≥85% coverage)

### Phase 2: Parallel Implementation (Hours 6-16)
**Duration**: 10 hours (6 + 4 parallel)
**Agents**: python-pro (lead)
**Focus**: Configuration manager + CLI commands

**Tasks (Sequential)**:
- Task 2.2: Configuration Loading & Saving (6h)
  - Implement ConfigManager class
  - Load/save with validation
  - Integration with xdg_dirs and config_loader
  - YAML serialization

**Tasks (Parallel)**:
- Task 2.4: Configuration CLI Commands (4h)
  - Can start after Task 2.1 completes
  - Implement show, validate, location, init commands
  - Integration with Click framework

**Deliverables**:
- `/home/gerald/git/mycelium/mycelium_onboarding/config/manager.py`
- `/home/gerald/git/mycelium/mycelium_onboarding/cli/config_commands.py`
- Unit tests for both modules

**Exit Criteria**:
- ConfigManager loads/saves correctly
- CLI commands work end-to-end
- Error handling comprehensive
- Tests achieve ≥85% coverage

### Phase 3: Schema Migration (Hours 16-24)
**Duration**: 8 hours
**Agent**: python-pro
**Focus**: Migration framework implementation

**Tasks**:
- Task 2.3: Schema Migration Framework
  - Migration decorator pattern
  - Version detection
  - Migration path finding
  - Integration with ConfigManager
  - Example 0.9 → 1.0 migration

**Deliverables**:
- `/home/gerald/git/mycelium/mycelium_onboarding/config/migrations.py`
- Updated ConfigManager with migration support
- Migration tests

**Exit Criteria**:
- Migrations apply automatically on load
- Migration actions logged
- User customizations preserved
- Tests verify all migrations

### Phase 4: Documentation & Integration (Hours 24-28)
**Duration**: 4 hours
**Agents**: platform-engineer (lead), technical-writer (support)
**Focus**: Comprehensive documentation

**Tasks**:
- Task 2.5: Configuration Documentation & Examples
  - Configuration reference guide
  - Usage examples (minimal, docker-compose, justfile)
  - CLI command documentation
  - Migration guide
  - Troubleshooting guide

**Deliverables**:
- `/home/gerald/git/mycelium/docs/configuration-reference.md`
- `/home/gerald/git/mycelium/docs/examples/` directory
- Integration tests validating end-to-end flows

**Exit Criteria**:
- All configuration options documented
- Examples cover common scenarios
- CLI usage clear
- Troubleshooting addresses common issues

## Quality Standards

### Test Coverage Requirements
- Schema validation: ≥85% coverage
- ConfigManager: ≥85% coverage
- CLI commands: ≥80% coverage
- Migrations: ≥90% coverage (critical path)
- Overall milestone: ≥85% coverage

### Documentation Requirements
- All public APIs documented with docstrings
- Type hints on all functions
- Usage examples in docstrings
- User-facing documentation for all features
- Troubleshooting guides for common issues

### Code Quality Requirements
- Pass all type checks (mypy)
- Pass all linting (ruff)
- Follow existing codebase patterns
- Comprehensive error messages
- Logging at appropriate levels

## Risk Management

### Risk 1: Schema Evolution Breaking Existing Configs
**Probability**: High
**Impact**: High
**Mitigation**:
- Implement migration framework from day 1
- Test migrations thoroughly
- Provide manual migration instructions
**Contingency**:
- Document manual migration steps
- Provide validation tools to check old configs

### Risk 2: YAML Parsing Edge Cases
**Probability**: Medium
**Impact**: Medium
**Mitigation**:
- Use yaml.safe_load exclusively
- Comprehensive test cases
- Clear error messages
**Contingency**:
- Support JSON format as alternative
- Provide YAML validation tools

### Risk 3: Validation Too Strict
**Probability**: Medium
**Impact**: Medium
**Mitigation**:
- Reasonable validators
- Allow customization where appropriate
- Clear validation error messages
**Contingency**:
- Make validators optional via flags
- Document how to bypass validation

## Communication Protocol

### Progress Updates
Agents report progress every 2 hours or at task completion:
```json
{
  "agent": "python-pro",
  "task": "2.2",
  "status": "in_progress",
  "completion": "65%",
  "next_milestone": "Implementing save() method",
  "blockers": []
}
```

### Blocker Escalation
Report blockers immediately:
```json
{
  "agent": "python-pro",
  "task": "2.3",
  "blocker": "Unclear migration path algorithm",
  "impact": "4 hours delay",
  "assistance_needed": "platform-engineer review of migration strategy"
}
```

### Task Completion
Notify on completion with deliverables:
```json
{
  "agent": "python-pro",
  "task": "2.1",
  "status": "complete",
  "deliverables": [
    "/home/gerald/git/mycelium/mycelium_onboarding/config/schema.py",
    "/home/gerald/git/mycelium/tests/test_config_schema.py"
  ],
  "test_coverage": "87%",
  "ready_for_review": true
}
```

## Integration Points with M01

### Using xdg_dirs.py
```python
from mycelium_onboarding.xdg_dirs import get_config_dir

# ConfigManager uses this for user-global config
config_dir = get_config_dir()
config_path = config_dir / "config.yaml"
```

### Using config_loader.py
```python
from mycelium_onboarding.config_loader import find_config_file, get_config_path

# ConfigManager uses this for hierarchical loading
config_file = find_config_file("config.yaml")
save_path = get_config_path("config.yaml", prefer_project=True)
```

### Using env_validator.py
```python
from mycelium_onboarding.env_validator import validate_environment

# CLI commands validate environment before running
validate_environment()
```

## Success Metrics

### Quantitative
- [ ] All 5 tasks completed
- [ ] Test coverage ≥85% across all modules
- [ ] 0 critical bugs
- [ ] Documentation completeness 100%
- [ ] All exit criteria met

### Qualitative
- [ ] Schema intuitive and extensible
- [ ] Error messages actionable
- [ ] CLI commands user-friendly
- [ ] Migrations preserve user data
- [ ] Documentation clear and comprehensive

## Next Milestone Dependencies

### M04: Interactive Onboarding
Will use:
- `MyceliumConfig` schema for type-safe storage
- `ConfigManager.save()` to persist wizard results
- Field validators to check user input

### M05: Deployment Generation
Will use:
- `config.deployment.method` to choose deployment strategy
- `config.services` to determine which services to deploy
- Port numbers and service-specific configuration

## Coordination Timeline

```
Hour 0  ████ Phase 1: Schema Design (python-pro)
Hour 6  ████████ Phase 2: Config Manager (python-pro)
        ████ Phase 2: CLI Commands (python-pro - parallel)
Hour 16 ████████████ Phase 3: Migrations (python-pro)
Hour 24 ████ Phase 4: Documentation (platform-engineer + technical-writer)
Hour 28 ✓ M02 COMPLETE
```

## Approval & Sign-off

**Coordination Plan Approved**: 2025-10-13
**Coordinator**: multi-agent-coordinator
**Ready to Execute**: YES

---

**Document Version**: 1.0
**Last Updated**: 2025-10-13 (Initial creation)
**Status**: ACTIVE - Ready for agent deployment
