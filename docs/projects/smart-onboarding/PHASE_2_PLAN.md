# Phase 2 Implementation Plan: Smart Onboarding Enhancements

**Status**: Planning **Branch**: `feat/smart-onboarding-phase2` **Dependencies**: Phase 1 (Complete - PR #10)

## Executive Summary

Phase 2 fixes critical Redis coordination issues, validates Temporal integration, enhances configuration management, and
adds interactive service management through a TUI dashboard.

### Key Objectives

1. **Redis MCP Coordination Fixes** - Fix JSON errors in meta-agent coordination
1. **Global Configuration Migration** - XDG-compliant config with project override
1. **PostgreSQL Version Compatibility** - Auto-detect Temporal requirements (warn only, no auto-upgrade)
1. **Temporal Workflow Testing** - Validate Temporal + PostgreSQL integration
1. **TUI Dashboard** - Real-time interactive service management

______________________________________________________________________

## Feature Prioritization

### Priority 1: Redis MCP Coordination Fixes (Week 1)

**Status**: User Confirmed - Redis JSON errors occur with meta-agent coordination ✅

**Problem**: When meta subagents (coordinators like agent-organizer, multi-agent-coordinator) use Redis MCP for
coordination, JSON serialization/deserialization errors occur.

**Root Cause**: Unknown - needs investigation with actual coordination workflows

**Impact**: High - Blocks multi-agent coordination features

**Success Criteria**:

- ✅ `/team-status` slash command works correctly with Redis MCP
- ✅ Meta-agents can store/retrieve coordination data without JSON errors
- ✅ Agent workload, active tasks, and heartbeats persist correctly
- ✅ No serialization errors when storing agent state
- ✅ Comprehensive error handling and fallback to markdown

**Investigation Tasks**:

1. Run `/team-status` command to reproduce Redis JSON errors
1. Identify which Redis MCP operations fail (hset, hgetall, json_set, json_get)
1. Check data types being serialized (datetime, complex objects, etc.)
1. Review agent coordination patterns in `.mycelium/modules/coordination.md`
1. Test with actual meta-agent workflows (agent-organizer, multi-agent-coordinator)

**Fix Tasks**:

1. Implement proper JSON serialization for agent state
1. Handle datetime serialization (isoformat, fromisoformat)
1. Add validation before storing to Redis
1. Implement robust deserialization with error handling
1. Add fallback to markdown coordination if Redis fails
1. Update coordination patterns documentation

**Testing**:

1. Run `/team-status` with Redis MCP
1. Launch multi-agent coordination workflow
1. Verify agent status persists correctly
1. Test circuit breaker status storage
1. Validate heartbeat mechanism

**Effort**: 8-12 hours

______________________________________________________________________

### Priority 2: Global Configuration Migration (Weeks 2-3)

**Complexity**: Medium **Impact**: High (Foundation for all features)

#### Current State

- Config: Project-local `mycelium-config.yaml`
- Data: `~/.local/share/mycelium/`
- State: `~/.local/state/mycelium/`
- Secrets: `~/.local/state/mycelium/secrets/`

#### Target State

- **Global Config**: `~/.config/mycelium/config.yaml`
- **Project Config**: `<project>/.mycelium/config.yaml`
- **Precedence**: Project > Global > Defaults
- **Migration**: Automatic with backup

#### Success Criteria

- ✅ XDG-compliant paths on Linux/macOS
- ✅ Windows compatibility (AppData)
- ✅ Automatic migration script
- ✅ Clear precedence rules
- ✅ No breaking changes
- ✅ >95% successful migrations

#### Implementation Tasks

1. Create `config/global.py` module
1. Implement XDG path resolution
1. Build config precedence resolver
1. Create migration command: `mycelium config migrate`
1. Add `mycelium config where` (show active config)
1. Update all config loading to check precedence
1. Write migration guide
1. Test on Linux/macOS/Windows

#### Risks & Mitigation

- **Risk**: Breaking existing deployments

  - **Mitigation**: Automatic backup before migration
  - **Fallback**: Keep project-local as backup

- **Risk**: Config precedence confusion

  - **Mitigation**: Clear messaging in `config where`
  - **Validation**: Show which config file is active

- **Risk**: Cross-platform path issues

  - **Mitigation**: Use `platformdirs` library
  - **Testing**: CI on all platforms

______________________________________________________________________

### Priority 3: PostgreSQL Version Compatibility (Weeks 4-5)

**Complexity**: Medium **Impact**: Medium (Prevents deployment failures)

#### Problem Statement

Temporal requires specific PostgreSQL versions. Currently users manually verify compatibility.

#### Solution Design

**Auto-Detection Flow**:

```
1. Detect Temporal version from project
   - Check pyproject.toml
   - Check requirements.txt
   - Check poetry.lock
   - Check uv.lock

2. Lookup required PostgreSQL version
   - Maintain compatibility matrix
   - Temporal <=1.4.0 → PostgreSQL 12-16
   - Temporal 1.5.0+ → PostgreSQL 13-17

3. Validate deployed PostgreSQL
   - Check version from smart detection
   - Compare against requirements
   - Warn if incompatible

4. User Decision
   - Continue anyway (expert mode)
   - Upgrade PostgreSQL (if possible)
   - Cancel deployment
```

#### Success Criteria

- ✅ Detects Temporal version >90% of projects
- ✅ Validates PostgreSQL compatibility
- ✅ Clear warnings before deployment
- ✅ Optional auto-upgrade (docker-compose only)
- ✅ Manual override available
- ✅ Documented version matrix

#### Implementation Tasks

1. Extend `deployment/postgres/version_manager.py`
1. Create `deployment/temporal/version_detector.py`
1. Build compatibility matrix (JSON config)
1. Add validation to `SmartDeploymentPlanner`
1. Create warning UI in deployment flow
1. Add `--force-version` override flag
1. Document compatibility matrix
1. Test with Temporal 1.4, 1.5, 1.6

#### Version Compatibility Matrix

```yaml
temporal:
  "1.3.x":
    postgresql:
      min: "12.0"
      max: "15.0"
      recommended: "14.0"
  "1.4.x":
    postgresql:
      min: "12.0"
      max: "16.0"
      recommended: "15.0"
  "1.5.x":
    postgresql:
      min: "13.0"
      max: "17.0"
      recommended: "16.0"
  "1.6.x":
    postgresql:
      min: "13.0"
      max: "17.0"
      recommended: "16.0"
```

#### Risks & Mitigation

- **Risk**: Version detection fails

  - **Mitigation**: Manual override flag
  - **Fallback**: Prompt user for version

- **Risk**: Compatibility matrix becomes outdated

  - **Mitigation**: CI job to check Temporal releases
  - **Update**: Quarterly matrix review

- **Risk**: Upgrade breaks existing data

  - **Mitigation**: Backup recommendation before upgrade
  - **Warning**: Clear migration path documentation

**User Decision (Confirmed)**: ✅ **Never auto-upgrade PostgreSQL** - Only warn users about incompatibilities

______________________________________________________________________

### Priority 4: Temporal Workflow Testing (Week 6)

**Status**: New requirement - Test Temporal with PostgreSQL storage ✅

**Objective**: Validate Temporal deployment and run test workflows to identify and fix any integration issues.

**Success Criteria**:

- ✅ Temporal deploys successfully with PostgreSQL backend
- ✅ Test workflow executes without errors
- ✅ Workflow state persists correctly in PostgreSQL
- ✅ Temporal UI accessible and shows workflow history
- ✅ Worker connects and processes activities
- ✅ All deployment issues identified and fixed

**Test Workflow Design**:

```python
# Simple test workflow to validate Temporal + PostgreSQL integration
@workflow.defn
class DeploymentValidationWorkflow:
    @workflow.run
    async def run(self, test_data: dict) -> dict:
        # Test 1: Activity execution
        result1 = await workflow.execute_activity(
            test_activity,
            args=["test_input"],
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Test 2: State persistence (sleep and continue)
        await asyncio.sleep(5)

        # Test 3: Child workflow
        child_result = await workflow.execute_child_workflow(
            ChildTestWorkflow.run,
            args=["child_test"],
        )

        # Test 4: Signal handling
        signal_received = await workflow.wait_condition(
            lambda: self.signal_received,
            timeout=timedelta(seconds=10)
        )

        return {
            "activity_result": result1,
            "child_result": child_result,
            "signal_test": signal_received,
            "status": "success"
        }

@activity.defn
async def test_activity(input: str) -> str:
    """Test activity that validates worker connectivity."""
    return f"Processed: {input}"
```

**Test Execution Plan**:

1. Deploy Temporal + PostgreSQL using `mycelium deploy start`
1. Verify services running with `mycelium deploy status`
1. Create simple test workflow project
1. Start Temporal worker
1. Execute test workflow
1. Verify workflow completion in Temporal UI
1. Check workflow state in PostgreSQL
1. Stop and restart services to test persistence
1. Re-run workflow to validate state recovery

**Issues to Test For**:

1. **Connection Issues**:

   - Temporal can't connect to PostgreSQL
   - Worker can't connect to Temporal server
   - UI can't access Temporal frontend

1. **Storage Issues**:

   - Workflow state not persisting
   - Activity results lost
   - History truncated or corrupted

1. **Version Compatibility**:

   - PostgreSQL version too old/new for Temporal
   - Schema migration failures
   - SQL compatibility issues

1. **Configuration Issues**:

   - Wrong connection strings
   - Missing environment variables
   - Incorrect port mappings

1. **Performance Issues**:

   - Slow workflow execution
   - Query timeouts
   - Connection pool exhaustion

**Fix Strategy**:

1. Document all errors encountered
1. Update deployment templates if needed
1. Add validation checks to deployment planner
1. Improve connection string generation
1. Add health checks for Temporal + PostgreSQL
1. Update PostgreSQL compatibility matrix based on findings

**Integration with Priority 3**:

- Feeds version compatibility data to PostgreSQL validator
- Identifies actual version issues in real deployments
- Validates that warnings are accurate and helpful

**Deliverables**:

1. Test workflow implementation
1. Deployment validation script
1. Issue report with fixes
1. Updated deployment documentation
1. Health check improvements

**Effort**: 8-12 hours

______________________________________________________________________

### Priority 5: TUI Dashboard (Weeks 7-10)

**Complexity**: Large **Impact**: High (Major UX improvement)

#### Technology Choice: Textual

**Why Textual?**

- Modern, async-native framework
- Rich integration (already using Rich)
- Active development and community
- Cross-platform (Linux/macOS/Windows)
- Hot reload for development
- Built-in widgets and layouts

**Alternatives Considered**:

- ❌ `rich.Live` - Limited interactivity
- ❌ `prompt_toolkit` - Lower level, more complex
- ❌ `blessed` - Less maintained
- ✅ **Textual** - Best fit for our needs

#### Feature Breakdown

**Phase 4.1: Core Layout (Week 6)**

- Application shell with header/footer
- Service status panel (read-only)
- Keyboard navigation (j/k, arrows)
- Help screen (F1)
- Exit handling (q, Ctrl+C)

**Phase 4.2: Real-time Updates (Week 7)**

- Poll deployment status every 2s
- Update service cards in real-time
- Connection status indicator
- Error state display
- Loading states

**Phase 4.3: Interactive Controls (Week 8)**

- Start/stop/restart buttons per service
- Confirmation dialogs
- Progress indicators
- Success/error notifications
- Undo capability (restart if stop fails)

**Phase 4.4: Log Viewer (Week 9)**

- Service log panel (docker logs)
- Filtering by log level
- Search functionality
- Follow mode (tail -f)
- Export logs to file

**Phase 4.5: Resource Monitoring (Optional)**

- CPU/Memory usage per container
- Network traffic stats
- Disk usage
- Platform-specific (docker stats)

#### UI Mockup

```
┌─ Mycelium Dashboard ─────────────────────────────────────────┐
│ Project: test-project                    Last Update: 14:23:45 │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  Services                                                      │
│  ┌────────────────────┐  ┌────────────────────┐               │
│  │ Redis              │  │ PostgreSQL         │               │
│  │ Status: ●Running   │  │ Status: ●Reused    │               │
│  │ Port: 6379         │  │ Port: 5432         │               │
│  │ Version: 8.2.3     │  │ Version: 16.1      │               │
│  │                    │  │                    │               │
│  │ [Stop] [Restart]   │  │ [External]         │               │
│  └────────────────────┘  └────────────────────┘               │
│                                                                │
│  ┌────────────────────┐                                       │
│  │ Temporal           │                                       │
│  │ Status: ●Running   │                                       │
│  │ Port: 7233         │                                       │
│  │ Version: 1.24.2    │                                       │
│  │                    │                                       │
│  │ [Stop] [Restart]   │                                       │
│  └────────────────────┘                                       │
│                                                                │
├──────────────────────────────────────────────────────────────┤
│ Logs (Temporal)                                        [Clear] │
│  2025-11-07 14:23:42 INFO  Worker started                     │
│  2025-11-07 14:23:43 INFO  Polling for tasks                  │
│  2025-11-07 14:23:44 WARN  Connection retrying...             │
│                                                                │
├──────────────────────────────────────────────────────────────┤
│ ↑/↓: Navigate  Enter: Action  l: Logs  r: Refresh  q: Quit    │
└──────────────────────────────────────────────────────────────┘
```

#### Success Criteria

- ✅ Dashboard starts in \<1s
- ✅ Updates every 2s without flicker
- ✅ All controls work reliably
- ✅ Logs display correctly
- ✅ >80% user satisfaction (survey)
- ✅ Works on Linux/macOS/Windows terminals
- ✅ Graceful degradation if Docker unavailable

#### Implementation Tasks

1. Add `textual` dependency to pyproject.toml
1. Create `tui/` module structure
1. Build `DashboardApp` with Textual
1. Create `ServiceCard` widget
1. Implement status polling loop
1. Add interactive control handlers
1. Create log viewer panel
1. Add keyboard shortcuts
1. Write user guide
1. Beta testing with real users

#### Risks & Mitigation

- **Risk**: TUI framework bugs

  - **Mitigation**: Pin Textual version, test extensively
  - **Fallback**: CLI commands still work

- **Risk**: Terminal compatibility

  - **Mitigation**: Test on tmux, screen, iTerm, Windows Terminal
  - **Detection**: Warn if terminal too small

- **Risk**: Performance issues

  - **Mitigation**: Efficient polling, caching, lazy rendering
  - **Config**: Adjustable refresh rate

______________________________________________________________________

## Cross-Feature Dependencies

```
Redis Coordination Fix (P1) ────→ Temporal Testing (P4)
    ↓                                      ↓
    ↓                            (Tests Redis + Temporal)
    ↓                                      ↓
Global Config (P2) ────→ PostgreSQL Compat (P3) ────→ TUI Dashboard (P5)
    ↓                           ↓                             ↓
 (Config storage)      (Version warnings)            (Dashboard prefs)
```

**Critical Path**:

1. Redis fixes enable meta-agent coordination
1. Global config provides foundation for version matrix storage
1. PostgreSQL compat validates versions (warn only, no auto-upgrade)
1. Temporal testing validates full stack integration
1. TUI dashboard provides interactive management

______________________________________________________________________

## Implementation Timeline

| Week | Sprint     | Deliverable                      | Status     |
| ---- | ---------- | -------------------------------- | ---------- |
| 1    | Sprint 1   | Redis MCP coordination fixes     | 📋 NEXT    |
| 2-3  | Sprint 2   | Global config migration          | 📋 PLANNED |
| 4-5  | Sprint 3   | PostgreSQL version compatibility | 📋 PLANNED |
| 6    | Sprint 4   | Temporal workflow testing        | 📋 PLANNED |
| 7    | Sprint 5.1 | TUI core layout                  | 📋 PLANNED |
| 8    | Sprint 5.2 | Real-time updates                | 📋 PLANNED |
| 9    | Sprint 5.3 | Interactive controls             | 📋 PLANNED |
| 10   | Sprint 5.4 | Log viewer                       | 📋 PLANNED |
| 11   | Sprint 5.5 | Polish & beta testing            | 📋 PLANNED |

**Total Duration**: 11 weeks (2.75 months)

**Sprint 1 Details** (Week 1):

1. Run `/team-status` to reproduce Redis JSON errors
1. Fix JSON serialization for meta-agent coordination
1. Test with actual coordination workflows
1. Update coordination documentation

______________________________________________________________________

## Success Metrics

### Phase 2 Complete When:

- ✅ Redis MCP coordination works without JSON errors
- ✅ `/team-status` command displays agent workload correctly
- ✅ Meta-agents (organizer, coordinator) can store/retrieve state
- ✅ 95%+ users successfully migrate to global config
- ✅ PostgreSQL version warnings prevent 90%+ incompatibility issues (warn only, no auto-upgrade)
- ✅ Temporal + PostgreSQL integration validated with test workflows
- ✅ Test workflow executes successfully and persists state
- ✅ TUI dashboard achieves >80% user satisfaction
- ✅ All features have >90% test coverage
- ✅ Documentation complete
- ✅ Zero critical bugs

______________________________________________________________________

## Testing Strategy

### Unit Tests

- Config precedence resolver
- Version detection logic
- TUI widget behaviors
- Compatibility matrix validation

### Integration Tests

- Config migration end-to-end
- PostgreSQL version checking in deployment flow
- TUI interactions with real Docker containers

### Manual Testing

- All platforms: Ubuntu, macOS, Windows
- All terminals: GNOME Terminal, iTerm2, Windows Terminal, tmux
- All deployment methods: docker-compose, kubernetes, systemd

### Beta Program

- 5-10 users for TUI dashboard
- Weekly feedback sessions
- Bug tracking in GitHub issues

______________________________________________________________________

## Documentation Requirements

### User Documentation

- [ ] Global config migration guide
- [ ] Config precedence explanation
- [ ] PostgreSQL compatibility matrix
- [ ] TUI dashboard user guide
- [ ] Keyboard shortcuts reference
- [ ] Troubleshooting guide

### Developer Documentation

- [ ] Architecture decision records (ADRs)
- [ ] TUI widget development guide
- [ ] Config system design
- [ ] Version detection algorithms
- [ ] Testing guidelines

______________________________________________________________________

## Risk Management

### High Risk Items

1. **TUI Terminal Compatibility** - Extensive testing required
1. **Config Migration Data Loss** - Automatic backups mandatory
1. **Version Matrix Accuracy** - CI validation needed

### Mitigation Strategies

- Feature flags for gradual rollout
- Comprehensive error handling
- Automatic rollback on failure
- Clear user messaging
- Beta testing program

______________________________________________________________________

## Next Steps

1. **User Clarification Needed**: Ask about Redis JSON storage issue
1. **Start Sprint 2**: Global configuration migration
1. **Technical Spike**: Evaluate Textual framework (1-2 days)
1. **Setup Testing**: Beta user recruitment

______________________________________________________________________

## Questions for User

1. **Redis Storage**: What specific issue did you encounter with Redis JSON?

   - Error message?
   - Feature request for distributed storage?
   - Misunderstanding about current implementation?

1. **TUI Dashboard**: Must-have features vs nice-to-have?

   - Resource monitoring critical?
   - Log export important?
   - Specific keyboard shortcuts?

1. **Global Config**: Migration timeline preference?

   - Automatic migration acceptable?
   - Manual migration preferred?
   - Gradual rollout needed?

1. **PostgreSQL**: Auto-upgrade acceptable?

   - Only warn and let user upgrade manually?
   - Automatic upgrade with confirmation?
   - Never auto-upgrade?

______________________________________________________________________

**Document Version**: 1.0 **Last Updated**: 2025-11-07 **Next Review**: Start of Sprint 2
