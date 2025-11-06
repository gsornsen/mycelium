# M04 Interactive Onboarding - Coordination Plan

**Coordinator**: multi-agent-coordinator **Start Date**: 2025-10-14 **Target Completion**: 3 days (28-32 hours)
**Status**: INITIATED

## Executive Summary

M04 Interactive Onboarding implements the user-facing wizard that transforms Mycelium from a technical framework into an
accessible, guided setup experience. This milestone bridges technical detection (M03) with automated deployment (M05),
providing an intuitive CLI wizard that guides users through service selection, deployment method choice, and
configuration generation.

The wizard reduces cognitive load through progressive disclosure, validates inputs before proceeding, and generates
type-safe configuration ready for deployment generation.

## Coordination Strategy

### Dependencies Validated

- **M01 Environment Isolation**: ✓ Complete (xdg_dirs, env_validator, config_loader)
- **M02 Configuration System**: ✓ Complete (schema, manager, migrations)
- **M03 Service Detection**: ✓ Complete (orchestrator, detectors, caching)

### Integration Points

- Uses M03 `detect_all_services()` to pre-fill wizard defaults
- Uses M02 `ConfigManager` to save/load configuration
- Uses M02 `MyceliumConfig` schema for validation
- Uses M01 XDG directories for config storage
- Will provide configuration to M05 (Deployment Generation)

## Task Breakdown & Agent Assignment

### Phase 1: Design & Foundation (8 hours)

#### Task 4.1: Design Wizard Flow and UX

- **Agent**: frontend-developer (lead), python-pro (review)
- **Duration**: 4 hours
- **Status**: READY
- **Dependencies**: None (M01-M03 complete)
- **Parallel Group**: A
- **Deliverables**:
  - `mycelium_onboarding/wizard/flow.py` - Wizard state machine
  - Flow diagram documenting all user paths
  - UX design document with mockups
- **Acceptance Criteria**:
  - Flow diagram covers happy path + error paths
  - Each step has clear entry/exit conditions
  - State management handles interruption and resume
  - UX reviewed for clarity and accessibility
  - State transitions validated

#### Task 4.2A: Design InquirerPy Screen Specifications

- **Agent**: frontend-developer
- **Duration**: 4 hours
- **Status**: READY
- **Dependencies**: None (can run parallel with 4.1)
- **Parallel Group**: A
- **Deliverables**:
  - Screen specifications document
  - Validation rules document
  - Help text and prompt design
- **Acceptance Criteria**:
  - All 7 wizard screens specified
  - Validation rules defined for each input
  - Help text provides clear guidance
  - Color scheme and formatting consistent
  - Accessibility requirements documented

### Phase 2: Core Implementation (12 hours)

#### Task 4.2B: Implement InquirerPy Wizard Screens

- **Agent**: python-pro
- **Duration**: 8 hours
- **Status**: BLOCKED (awaits Task 4.2A)
- **Dependencies**: Task 4.2A (screen specifications)
- **Parallel Group**: B
- **Deliverables**:
  - `mycelium_onboarding/wizard/screens.py` - All wizard screens
  - `tests/unit/test_wizard_screens.py` - Unit tests
- **Acceptance Criteria**:
  - All 7 screens implemented with rich formatting
  - Input validation prevents invalid configurations
  - Help text provides clear guidance
  - Color scheme consistent and accessible
  - Non-interactive mode supported
  - Test coverage ≥85%

#### Task 4.3: Integrate Detection Results

- **Agent**: backend-developer
- **Duration**: 3 hours
- **Status**: READY (can start after 4.1)
- **Dependencies**: Task 4.1 (wizard flow)
- **Parallel Group**: B
- **Deliverables**:
  - `mycelium_onboarding/wizard/integration.py` - Detection integration
  - `tests/unit/test_wizard_integration.py` - Unit tests
- **Acceptance Criteria**:
  - Detection results populate wizard defaults
  - Unavailable services disabled in prompts
  - Detected ports/hosts used as defaults
  - Configuration builder creates valid MyceliumConfig
  - Test coverage ≥85%

#### Task 4.4: Implement Configuration Persistence

- **Agent**: python-pro
- **Duration**: 2 hours
- **Status**: READY (can run parallel)
- **Dependencies**: None (M02 integration)
- **Parallel Group**: B
- **Deliverables**:
  - `mycelium_onboarding/wizard/persistence.py` - Config saving/loading
  - `tests/unit/test_wizard_persistence.py` - Unit tests
- **Acceptance Criteria**:
  - Configuration saved to correct location
  - Success message includes next steps
  - Error messages are actionable
  - Resume functionality works correctly
  - Test coverage ≥85%

### Phase 3: CLI Integration & Polish (8 hours)

#### Task 4.5: Create /mycelium-onboarding Command

- **Agent**: backend-developer (lead), python-pro (support)
- **Duration**: 4 hours
- **Status**: BLOCKED (awaits Phase 2)
- **Dependencies**: Tasks 4.2B, 4.3, 4.4
- **Parallel Group**: C
- **Deliverables**:
  - `mycelium_onboarding/cli.py` - CLI entry point
  - `~/.claude/plugins/mycelium-core/commands/mycelium-onboarding.md` - Command definition
  - `tests/e2e/test_onboarding_command.py` - End-to-end tests
- **Acceptance Criteria**:
  - Command registered and discoverable
  - All flags work correctly (--project-local, --force, --no-cache, --non-interactive)
  - Help text comprehensive
  - Errors handled gracefully
  - Test coverage ≥85%

#### Task 4.6: Testing and Documentation

- **Agent**: platform-engineer (lead), python-pro (support)
- **Duration**: 4 hours
- **Status**: BLOCKED (awaits Phase 3)
- **Dependencies**: Task 4.5
- **Parallel Group**: C (can overlap with 4.5)
- **Deliverables**:
  - `tests/integration/test_wizard_flow.py` - Integration tests
  - `docs/guides/interactive-onboarding.md` - User guide
  - `docs/api/wizard-api.md` - API reference
  - Screenshots of wizard screens
- **Acceptance Criteria**:
  - Integration tests cover happy path and error cases
  - Unit tests for each wizard screen
  - Documentation includes screenshots and examples
  - Troubleshooting guide addresses common issues
  - Test coverage ≥85% overall

## Coordination Mechanisms

### Parallel Execution Strategy

**Phase 1: Design & Foundation (Tasks 4.1, 4.2A)**

- Both tasks can execute in parallel
- frontend-developer handles UX design
- python-pro reviews flow design
- Expected completion: 4 hours

**Phase 2: Core Implementation (Tasks 4.2B, 4.3, 4.4)**

- Task 4.2B depends on 4.2A completion
- Tasks 4.3 and 4.4 can start immediately after Phase 1
- All three can run in parallel once dependencies met
- Expected completion: 8 hours after dependencies met

**Phase 3: CLI Integration & Polish (Tasks 4.5, 4.6)**

- Task 4.5 depends on Phase 2 completion
- Task 4.6 can overlap with 4.5 (documentation starts early)
- Expected completion: 4 hours after Phase 2

### Inter-Agent Communication

**Message Protocol**:

```json
{
  "type": "task_status",
  "agent": "agent-id",
  "task": "4.x",
  "status": "in_progress|completed|blocked",
  "progress": 0-100,
  "deliverables": ["file1.py", "file2.py"],
  "blockers": [],
  "integration_points": {
    "screen_specs": "ready|pending",
    "flow_state": "ready|pending",
    "detection_integration": "ready|pending"
  }
}
```

**Synchronization Points**:

1. **Phase 1 Completion Gate**: Flow and screen specs complete before implementation
1. **Phase 2 Completion Gate**: All core implementation complete before CLI integration
1. **Test Coverage Gate**: Each module achieves ≥85% coverage before proceeding
1. **Quality Gate**: Zero linting issues, 100% type safety
1. **Integration Gate**: End-to-end wizard flow validated

### Progress Tracking

**Metrics Collection**:

- Task completion percentage per phase
- Test coverage per module
- Code quality metrics (mypy, ruff)
- User experience validation
- Integration test success rate

**Status Updates**:

- Agents report status every 2 hours
- Coordinator checks progress every hour
- Blockers escalated immediately
- Design decisions require coordination approval

## Quality Standards

### Code Quality

- **Test Coverage**: ≥85% per module, ≥85% overall
- **Type Safety**: 100% (mypy --strict)
- **Linting**: 0 issues (ruff check)
- **UX Quality**: Clear prompts, helpful errors, consistent formatting

### Testing Requirements

- **Unit Tests**: Each wizard screen and module
- **Integration Tests**: Complete wizard flows
- **Mock Tests**: Simulate various detection scenarios
- **E2E Tests**: Full command execution
- **Accessibility Tests**: Keyboard navigation, screen reader friendly

### Documentation Requirements

- **User Documentation**: Step-by-step wizard guide with screenshots
- **API Documentation**: All public functions documented
- **Integration Examples**: How to use wizard programmatically
- **Troubleshooting Guide**: Common issues and solutions

## Risk Management

### High Risk: UX Confusion with Complex Flows

- **Impact**: Users may get lost or make incorrect choices
- **Detection**: User testing, feedback from early adopters
- **Mitigation**: Progressive disclosure, clear help text, review/confirm step
- **Contingency**: Add more intermediate confirmation steps

### Medium Risk: InquirerPy Compatibility Issues

- **Impact**: Terminal rendering issues on different platforms
- **Detection**: Cross-platform testing
- **Mitigation**: Pin InquirerPy version, test on multiple terminals
- **Contingency**: Fallback to simple input() prompts

### Medium Risk: Resume State Corruption

- **Impact**: Interrupted sessions can't resume
- **Detection**: Integration tests with simulated interruptions
- **Mitigation**: Atomic writes, validation before save, backup previous config
- **Contingency**: Force fresh start flag (--force)

### Low Risk: Terminal Rendering Issues

- **Impact**: Colors/Unicode not displaying correctly
- **Detection**: Platform compatibility testing
- **Mitigation**: Detect terminal capabilities, fallback to plain text
- **Contingency**: --no-color flag, text-only mode

## Acceptance Criteria (Exit Gate)

### Wizard Implementation

- [ ] InquirerPy wizard implemented with 7 screens
- [ ] Service detection integration working
- [ ] Configuration saved using M02 ConfigManager
- [ ] Resume functionality working
- [ ] Non-interactive mode supported

### CLI Integration

- [ ] `/mycelium-onboarding` command functional
- [ ] All flags working (--project-local, --force, --no-cache, --non-interactive)
- [ ] Command discoverable via help
- [ ] Error handling comprehensive

### Testing

- [ ] Unit tests for all wizard screens (≥85% coverage)
- [ ] Integration tests for complete flows
- [ ] E2E tests for CLI command
- [ ] Mock tests for various detection scenarios

### Documentation

- [ ] User guide complete with screenshots
- [ ] API reference documented
- [ ] Troubleshooting guide comprehensive
- [ ] Integration examples provided

### Quality Gates

- [ ] All tests passing: `uv run pytest tests/ --cov=mycelium_onboarding`
- [ ] Type checking passing: `uv run mypy mycelium_onboarding --strict`
- [ ] Linting passing: `uv run ruff check mycelium_onboarding`
- [ ] Test coverage ≥85%
- [ ] Manual testing on Linux, macOS (if available), WSL2

## Agent Prompts

### For frontend-developer (Tasks 4.1, 4.2A)

```
You are designing the user experience for the Mycelium onboarding wizard (M04).

CONTEXT:
- M01 (Environment Isolation), M02 (Configuration System), M03 (Service Detection) complete
- This wizard is the primary user touchpoint for Mycelium setup
- Must transform technical detection into user-friendly choices
- Target audience: Developers of all skill levels

YOUR TASKS:
1. Design wizard flow and state machine (mycelium_onboarding/wizard/flow.py)
2. Design InquirerPy screen specifications (all 7 screens)

WIZARD FLOW SEQUENCE:
1. Welcome screen with system detection summary
2. Service selection (Redis, Postgres, Temporal, TaskQueue)
3. Service configuration (ports, persistence, memory limits)
4. Deployment method selection (Docker Compose, Justfile)
5. Project metadata (name, description)
6. Configuration review and confirmation
7. Write configuration and show next steps

DESIGN REQUIREMENTS:
- Progressive disclosure (don't overwhelm users)
- Intelligent defaults based on detection results
- Clear explanations for each decision point
- Input validation before proceeding
- Review step before finalizing
- Graceful exit at any point
- Resume support for interrupted sessions

UX PRINCIPLES:
- Accessibility: keyboard-only navigation, screen reader friendly
- Clarity: consistent terminology, clear error messages
- Guidance: contextual help, examples, recommendations
- Safety: confirm before writing, show what will happen

IMPLEMENTATION GUIDELINES:
Follow patterns in docs/projects/onboarding/milestones/M04_INTERACTIVE_ONBOARDING.md

State Machine (flow.py):
- WizardStep enum for all steps
- WizardState dataclass for state management
- can_proceed() validation method
- next_step() navigation logic
- create_wizard_state() initialization

Screen Specifications (design doc):
- InquirerPy component selection (select, checkbox, text, confirm)
- Validation rules for each input
- Help text for complex choices
- Default values from detection
- Error messages for validation failures
- Color scheme (rich library)

DELIVERABLES:
- mycelium_onboarding/wizard/flow.py
- Flow diagram (Mermaid or ASCII art)
- Screen specifications document
- Validation rules document
- UX review checklist

QUALITY STANDARDS:
- All user paths documented
- Validation prevents invalid states
- Help text clear and actionable
- Accessibility requirements met
```

### For python-pro (Tasks 4.2B, 4.4)

```
You are implementing the core wizard screens and persistence for Mycelium onboarding (M04).

CONTEXT:
- M01 (Environment Isolation), M02 (Configuration System), M03 (Service Detection) complete
- Screen specifications from frontend-developer (Task 4.2A)
- Wizard flow design from Task 4.1

YOUR TASKS:
1. Implement InquirerPy wizard screens (mycelium_onboarding/wizard/screens.py)
2. Implement configuration persistence (mycelium_onboarding/wizard/persistence.py)

WIZARD SCREENS (screens.py):
Implement 7 screens using InquirerPy and rich:

1. show_welcome_screen(detection_results)
   - Display detection summary table
   - Show welcome message
   - Confirm to begin

2. prompt_service_selection(detection_results)
   - Checkbox for services (Redis, Postgres, Temporal, TaskQueue)
   - Pre-check based on detection
   - Validate at least one selected

3. prompt_service_config(selected_services, detection_results)
   - Configure ports, memory, persistence per service
   - Use detected values as defaults

4. prompt_deployment_method(has_docker)
   - Select Docker Compose or Justfile
   - Recommend Docker Compose if available
   - Auto-select Justfile if Docker unavailable

5. prompt_project_metadata()
   - Text input for project name (validate identifier)
   - Text input for description (optional)

6. show_configuration_review(config)
   - Display final configuration table
   - Confirm to save

7. show_finalization(config_path)
   - Success message
   - Next steps (generate, start services)

PERSISTENCE (persistence.py):

save_configuration(config, project_local):
- Use ConfigManager.save() from M02
- Return (success, config_path) tuple
- Show rich Panel with success/error message
- Include next steps in success message

resume_from_previous():
- Load previous config using ConfigManager.load()
- Prompt to resume, start fresh, or cancel
- Return previous config or None

REQUIREMENTS:
- All screens use rich Console for formatting
- InquirerPy for all user inputs
- Validation on all inputs (port ranges, names, etc.)
- Non-interactive mode support (env vars or defaults)
- Comprehensive error messages
- Type-safe with type hints
- Comprehensive unit tests (≥85% coverage)

IMPLEMENTATION GUIDE:
Follow patterns in docs/projects/onboarding/milestones/M04_INTERACTIVE_ONBOARDING.md (Tasks 4.2, 4.4)

Key points:
- Import InquirerPy: inquirer.select(), inquirer.checkbox(), inquirer.text(), inquirer.confirm()
- Import rich: Console(), Table(), Panel()
- Use detection results to pre-fill defaults
- Validate all inputs before proceeding
- Handle Ctrl+C gracefully (exit without writing)

QUALITY STANDARDS:
- mypy --strict must pass
- ruff check must pass
- pytest coverage ≥85%
- All validation rules enforced

DELIVERABLES:
- mycelium_onboarding/wizard/screens.py
- mycelium_onboarding/wizard/persistence.py
- tests/unit/test_wizard_screens.py
- tests/unit/test_wizard_persistence.py

Run tests with: uv run pytest tests/unit/test_wizard_*.py -v --cov
```

### For backend-developer (Tasks 4.3, 4.5)

```
You are implementing detection integration and CLI commands for Mycelium onboarding (M04).

CONTEXT:
- M01 (Environment Isolation), M02 (Configuration System), M03 (Service Detection) complete
- Wizard screens and persistence from python-pro
- Wizard flow from frontend-developer

YOUR TASKS:
1. Integrate detection results into wizard (mycelium_onboarding/wizard/integration.py)
2. Create /mycelium-onboarding CLI command (mycelium_onboarding/cli.py)

DETECTION INTEGRATION (integration.py):

run_wizard_with_detection(use_cache):
- Run detect_all_services() from M03
- Initialize WizardState with detection results
- Execute wizard flow step by step
- Build MyceliumConfig from selections
- Return configuration or None (cancelled)

build_config_from_selections(...):
- Create RedisConfig, PostgresConfig, etc. based on selections
- Use detected ports/hosts as defaults
- Validate with Pydantic schema
- Return valid MyceliumConfig

Key integrations:
- Import from M03: detect_all_services, DetectionResults
- Import from M02: MyceliumConfig, ConfigManager
- Import wizard screens: show_welcome_screen, prompt_service_selection, etc.
- Import flow: WizardState, create_wizard_state

CLI COMMAND (cli.py):

@click.command()
@click.option('--project-local', is_flag=True)
@click.option('--force', is_flag=True)
@click.option('--no-cache', is_flag=True)
@click.option('--non-interactive', is_flag=True)
def onboard(...):
    # Check for resume unless --force
    # Run wizard with detection
    # Save configuration
    # Show success/next steps

Command registration:
- Create ~/.claude/plugins/mycelium-core/commands/mycelium-onboarding.md
- Document all options and examples
- Include troubleshooting section

REQUIREMENTS:
- Seamless integration with M03 detection
- Type-safe configuration building
- Graceful error handling
- Clear user feedback
- Comprehensive CLI help
- Non-interactive mode for CI/CD
- Test coverage ≥85%

IMPLEMENTATION GUIDE:
Follow patterns in docs/projects/onboarding/milestones/M04_INTERACTIVE_ONBOARDING.md (Tasks 4.3, 4.5)

Key points:
- Use asyncio.run() for async detection
- Build config incrementally from user selections
- Validate before saving
- Handle cancellation gracefully (user presses Ctrl+C)
- Non-interactive mode uses all defaults

QUALITY STANDARDS:
- mypy --strict must pass
- ruff check must pass
- pytest coverage ≥85%
- All error paths tested

DELIVERABLES:
- mycelium_onboarding/wizard/integration.py
- mycelium_onboarding/cli.py
- ~/.claude/plugins/mycelium-core/commands/mycelium-onboarding.md
- tests/unit/test_wizard_integration.py
- tests/e2e/test_onboarding_command.py

INTEGRATION IMPORTS:
from mycelium_onboarding.detection.orchestrator import detect_all_services
from mycelium_onboarding.config.manager import ConfigManager
from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.wizard.flow import WizardState, create_wizard_state
from mycelium_onboarding.wizard.screens import (
    show_welcome_screen,
    prompt_service_selection,
    prompt_deployment_method,
    prompt_project_metadata,
    show_configuration_review,
)
from mycelium_onboarding.wizard.persistence import save_configuration, resume_from_previous

Run tests with: uv run pytest tests/ -v --cov=mycelium_onboarding.wizard
```

### For platform-engineer (Task 4.6)

````
You are creating comprehensive documentation and integration tests for Mycelium onboarding (M04).

CONTEXT:
- M01 (Environment Isolation), M02 (Configuration System), M03 (Service Detection) complete
- All wizard implementation complete (Tasks 4.1-4.5)
- Need comprehensive testing and user-facing documentation

YOUR TASKS:
1. Create integration tests for wizard flows
2. Write comprehensive user documentation
3. Create API reference documentation
4. Capture wizard screenshots

INTEGRATION TESTS (tests/integration/test_wizard_flow.py):

Test scenarios:
1. test_complete_wizard_flow_docker_compose()
   - Mock detection with Docker available
   - Mock user inputs selecting Redis + Temporal
   - Verify config generated correctly

2. test_wizard_flow_no_docker()
   - Mock detection without Docker
   - Verify Justfile auto-selected
   - Verify config valid

3. test_wizard_handles_interruption()
   - Simulate wizard interruption
   - Verify resume functionality
   - Verify state preserved

4. test_wizard_validation_errors()
   - Test invalid project names
   - Test invalid port ranges
   - Test no services selected
   - Verify error messages clear

5. test_non_interactive_mode()
   - Run with --non-interactive
   - Verify defaults used
   - Verify config generated

USER DOCUMENTATION (docs/guides/interactive-onboarding.md):

Sections:
1. Overview - What the wizard does
2. Prerequisites - Requirements before running
3. Running the Wizard - Step-by-step guide
4. Wizard Screens - Detailed explanation of each screen
5. After Onboarding - Next steps
6. Troubleshooting - Common issues and solutions
7. Advanced Options - CLI flags and customization

Include:
- Screenshots of each wizard screen
- Example configurations
- Common workflows
- Troubleshooting table
- FAQ section

API REFERENCE (docs/api/wizard-api.md):

Document:
- run_wizard_with_detection() - Main entry point
- build_config_from_selections() - Config builder
- save_configuration() - Persistence
- resume_from_previous() - Resume logic
- All wizard screens - Parameters and returns

REQUIREMENTS:
- Integration tests cover happy path and error cases
- Tests use mocks for detection and user input
- Documentation includes visual examples
- Troubleshooting addresses real user issues
- API reference complete and accurate
- Test coverage ≥85%

IMPLEMENTATION GUIDE:
Follow patterns in docs/projects/onboarding/milestones/M04_INTERACTIVE_ONBOARDING.md (Task 4.6)

Testing approach:
- Use pytest with AsyncMock for detect_all_services()
- Mock InquirerPy prompts with predefined responses
- Use tmp_path fixture for file operations
- Verify MyceliumConfig output valid

Documentation approach:
- Start with user perspective (not technical)
- Include visual examples and screenshots
- Provide copy-paste commands
- Address common errors
- Link to related docs

QUALITY STANDARDS:
- All integration tests passing
- Coverage ≥85% overall
- Documentation complete and accurate
- Screenshots clear and helpful

DELIVERABLES:
- tests/integration/test_wizard_flow.py
- docs/guides/interactive-onboarding.md
- docs/api/wizard-api.md
- docs/screenshots/ (wizard screen captures)

TESTING PATTERNS:
```python
@pytest.mark.asyncio
async def test_complete_wizard_flow():
    # Mock detection
    mock_detection = AsyncMock(return_value=mock_detection_results())

    # Mock user inputs
    with patch('mycelium_onboarding.wizard.integration.detect_all_services', mock_detection):
        with patch_wizard_prompts({'service_selection': {'redis', 'temporal'}}):
            config = await run_wizard_with_detection()

    assert config.services.redis.enabled is True
    assert config.deployment.method == "docker-compose"
````

Run tests with: uv run pytest tests/integration/test_wizard_flow.py -v --cov

````

## Execution Timeline

### Day 1: Phase 1 - Design & Foundation (8 hours)

**Hours 0-4: Design Phase**
- frontend-developer: Design wizard flow (Task 4.1)
- frontend-developer: Design screen specifications (Task 4.2A)
- python-pro: Review flow design
- Deliverables: Flow diagram, state machine, screen specs

**Hour 4: Design Review Checkpoint**
- Validate flow covers all paths
- Verify screen specifications complete
- Check validation rules defined
- Approve UX design

**Hours 4-8: Early Implementation**
- python-pro: Begin wizard screens (Task 4.2B)
- backend-developer: Begin detection integration (Task 4.3)
- python-pro: Implement persistence (Task 4.4)

**Hour 8: Day 1 Checkpoint**
- 50% of Phase 2 implementation complete
- All design artifacts approved
- No blocking issues

### Day 2: Phase 2 - Core Implementation (12 hours)

**Hours 0-4: Complete Core**
- python-pro: Complete wizard screens (Task 4.2B)
- backend-developer: Complete detection integration (Task 4.3)
- python-pro: Complete persistence (Task 4.4)

**Hour 4: Phase 2 Checkpoint**
- All wizard screens implemented
- Detection integration working
- Persistence functional
- Unit tests passing (≥85% coverage)

**Hours 4-8: Phase 3 Start**
- backend-developer: Begin CLI command (Task 4.5)
- platform-engineer: Begin integration tests (Task 4.6)
- All agents: Fix any integration issues

**Hour 8: Integration Checkpoint**
- CLI command structure in place
- First integration test passing
- No critical blockers

**Hours 8-12: Continue Phase 3**
- backend-developer: Complete CLI command (Task 4.5)
- platform-engineer: Complete integration tests (Task 4.6)
- platform-engineer: Start documentation

**Hour 12: Day 2 Checkpoint**
- CLI command functional
- Integration tests passing
- Documentation in progress

### Day 3: Phase 3 - Polish & Documentation (8 hours)

**Hours 0-4: Final Implementation**
- backend-developer: Polish CLI, error handling
- platform-engineer: Complete integration tests
- platform-engineer: Complete user documentation
- All agents: Fix any failing tests

**Hour 4: Quality Gate Checkpoint**
- All tests passing
- Coverage ≥85%
- Type checking passing
- Linting clean

**Hours 4-6: End-to-End Testing**
- Manual testing on Linux
- Test all wizard paths
- Test all CLI flags
- Verify non-interactive mode
- Test resume functionality

**Hour 6: E2E Checkpoint**
- All manual tests passing
- Documentation complete
- Screenshots captured

**Hours 6-8: Final Polish**
- Address any final issues
- Update documentation
- Final validation against acceptance criteria
- Prepare handoff to M05

**Hour 8: Milestone Complete**
- All acceptance criteria met
- Documentation published
- Ready for M05 integration

## Success Metrics

### Performance Metrics
- Wizard completion time: <5 minutes (typical user)
- Detection integration: <5s
- Configuration save: <1s
- Resume from interruption: <2s

### Quality Metrics
- Test coverage: ≥85% per module, ≥85% overall
- Type safety: 100% (mypy --strict)
- Linting: 0 issues (ruff)
- User experience score: Positive feedback from testing

### Functional Metrics
- Wizard flow completion rate: 100%
- Configuration validation success: 100%
- Error message clarity: 100% actionable
- Platform compatibility: Linux (primary), macOS/WSL2 (tested)

### User Experience Metrics
- Steps to complete wizard: 7 screens
- Validation errors: Clear and actionable
- Help text availability: Every screen
- Resume functionality: Works reliably

## Handoff to Next Milestones

### M05: Deployment Generation

**Integration Points**:
- Import: `from mycelium_onboarding.cli import onboard`
- Usage: Run onboarding before deployment generation
- Logic: Use generated MyceliumConfig for deployment
- Workflow: `mycelium-onboarding` → `mycelium-generate` → `just up`

**Generated Artifacts**:
- `~/.config/mycelium/mycelium.yaml` or `.mycelium/mycelium.yaml`
- Contains all deployment parameters
- Type-safe MyceliumConfig object
- Ready for M05 template rendering

**Example Workflow**:
```bash
# 1. Run onboarding
/mycelium-onboarding

# 2. Generate deployment files (M05)
/mycelium-generate

# 3. Start services
just up
````

**Configuration Structure for M05**:

```python
# M05 will load this
config = ConfigManager.load()

# And use:
config.deployment.method  # "docker-compose" or "justfile"
config.services.redis.enabled  # True/False
config.services.redis.port  # 6379
config.services.postgres.port  # 5432
# etc.
```

## Monitoring & Status

### Real-Time Coordination Tracking

Stored in: `~/.local/state/mycelium/coordination/M04_status.json`

```json
{
  "milestone": "M04",
  "status": "in_progress",
  "start_time": "2025-10-14T10:00:00Z",
  "phases": {
    "phase1_design": {
      "status": "in_progress",
      "tasks": {
        "4.1": {"status": "in_progress", "agent": "frontend-developer", "progress": 0},
        "4.2A": {"status": "in_progress", "agent": "frontend-developer", "progress": 0}
      }
    },
    "phase2_implementation": {
      "status": "blocked",
      "tasks": {
        "4.2B": {"status": "blocked", "agent": "python-pro", "progress": 0},
        "4.3": {"status": "ready", "agent": "backend-developer", "progress": 0},
        "4.4": {"status": "ready", "agent": "python-pro", "progress": 0}
      }
    },
    "phase3_integration": {
      "status": "blocked",
      "tasks": {
        "4.5": {"status": "blocked", "agent": "backend-developer", "progress": 0},
        "4.6": {"status": "blocked", "agent": "platform-engineer", "progress": 0}
      }
    }
  },
  "metrics": {
    "test_coverage": 0,
    "type_safety": 0,
    "linting_issues": 0,
    "documentation_complete": 0
  }
}
```

### Escalation Criteria

- Any task blocked for >2 hours
- Test coverage falls below 85%
- Type safety issues detected
- UX concerns raised
- Agent unresponsive for >1 hour
- Integration issues between modules

## Final Deliverables Checklist

### Code Modules

- [ ] mycelium_onboarding/wizard/__init__.py
- [ ] mycelium_onboarding/wizard/flow.py
- [ ] mycelium_onboarding/wizard/screens.py
- [ ] mycelium_onboarding/wizard/integration.py
- [ ] mycelium_onboarding/wizard/persistence.py
- [ ] mycelium_onboarding/cli.py

### Command Integration

- [ ] ~/.claude/plugins/mycelium-core/commands/mycelium-onboarding.md

### Tests

- [ ] tests/unit/test_wizard_flow.py
- [ ] tests/unit/test_wizard_screens.py
- [ ] tests/unit/test_wizard_integration.py
- [ ] tests/unit/test_wizard_persistence.py
- [ ] tests/integration/test_wizard_flow.py
- [ ] tests/e2e/test_onboarding_command.py

### Documentation

- [ ] docs/guides/interactive-onboarding.md
- [ ] docs/api/wizard-api.md
- [ ] docs/screenshots/ (wizard screens)
- [ ] Flow diagram (Mermaid or ASCII)
- [ ] Screen specifications document

### Validation

- [ ] All tests passing
- [ ] Coverage ≥85%
- [ ] Type checking passing
- [ ] Linting passing
- [ ] Manual testing complete
- [ ] Documentation reviewed
- [ ] Screenshots captured
- [ ] E2E wizard flow validated

______________________________________________________________________

**Coordination Status**: ACTIVE **Next Review**: 2 hours from start **Escalation Contact**: multi-agent-coordinator

This coordination plan will be updated in real-time as tasks progress.
