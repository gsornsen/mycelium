# Mycelium Onboarding System - Dependencies Map

## Critical Path Analysis

The critical path determines the minimum project duration, assuming unlimited parallelization of independent tasks.

### Critical Path: 18 Days

```
M01 (3d) → M02 (2d) → M03 (3d) → M04 (3d) → M05 (2d) → M06 (3d) → M10 (2d)
```

**Explanation**: Each milestone on the critical path must complete before the next can begin. Any delay in these milestones directly delays project completion.

### Parallel Opportunities

Phase 3 milestones can execute concurrently:
- **M07**: Configuration Management (2 days)
- **M08**: Documentation (3 days)
- **M09**: Testing Suite (2 days)

**Time Savings**: 4 days (reducing 7 sequential days to 3 parallel days)
**Optimal Timeline**: 18 days (critical path) + 3 days (Phase 3 parallel) = **21 days total**

## Full Dependency Graph

### Phase 1: Foundation (Days 1-8)

```
M01: Environment Isolation (3 days)
  ├─ No dependencies (project start)
  └─ Blocks: M02, M03, M04

M02: Configuration System (2 days)
  ├─ Depends: M01 (XDG directories)
  └─ Blocks: M04, M05

M03: Service Detection (3 days)
  ├─ Depends: M01 (environment validation)
  ├─ Parallel with: M02
  └─ Blocks: M04, M05
```

**Phase 1 Timeline**: 8 days total
- Days 1-3: M01 (sequential)
- Days 4-8: M02 (days 4-5) + M03 (days 4-6, parallel)

### Phase 2: Core Features (Days 9-16)

```
M04: Interactive Onboarding (3 days)
  ├─ Depends: M01 (environment), M02 (config schema), M03 (service detection)
  └─ Blocks: M05

M05: Deployment Generation (2 days)
  ├─ Depends: M02 (config), M03 (service info), M04 (user selections)
  └─ Blocks: M06

M06: Coordination Testing (3 days)
  ├─ Depends: M05 (deployment configs to test)
  └─ Blocks: M10
```

**Phase 2 Timeline**: 8 days total
- Days 9-11: M04 (sequential)
- Days 12-13: M05 (sequential)
- Days 14-16: M06 (sequential)

### Phase 3: Polish (Days 17-24)

```
M07: Configuration Management (2 days)
  ├─ Depends: M02 (config system)
  ├─ Parallel with: M08, M09
  └─ Blocks: M10

M08: Documentation (3 days)
  ├─ Depends: M04, M05, M06 (features to document)
  ├─ Parallel with: M07, M09
  └─ Blocks: M10

M09: Testing Suite (2 days)
  ├─ Depends: M06 (testing patterns established)
  ├─ Parallel with: M07, M08
  └─ Blocks: M10

M10: Polish & Release (2 days)
  ├─ Depends: M06, M07, M08, M09 (all features complete)
  └─ Project end
```

**Phase 3 Timeline**: 5 days total
- Days 17-19: M07 + M08 + M09 (parallel, longest is 3 days)
- Days 20-21: M10 (sequential)

## Detailed Dependency Matrix

| Milestone | Duration | Depends On | Blocks | Can Parallelize With |
|-----------|----------|------------|--------|---------------------|
| M01 | 3d | None | M02, M03, M04 | None (project start) |
| M02 | 2d | M01 | M04, M05 | M03 |
| M03 | 3d | M01 | M04, M05 | M02 |
| M04 | 3d | M01, M02, M03 | M05 | None |
| M05 | 2d | M02, M03, M04 | M06 | None |
| M06 | 3d | M05 | M07, M08, M09, M10 | None |
| M07 | 2d | M02 | M10 | M08, M09 |
| M08 | 3d | M04, M05, M06 | M10 | M07, M09 |
| M09 | 2d | M06 | M10 | M07, M08 |
| M10 | 2d | M06, M07, M08, M09 | None (project end) | None |

## Resource Allocation by Phase

### Phase 1 (Days 1-8): Environment & Detection

**Active Agents**:
- platform-engineer (100% - M01 lead, M02 support)
- python-pro (80% - M01, M02 shared)
- devops-engineer (60% - M03 lead)

**Key Deliverables**:
- XDG directory structure
- Configuration schema
- Service detection utilities

**Risk**: Platform-specific issues could delay M01, cascading to all subsequent work

### Phase 2 (Days 9-16): Core Features

**Active Agents**:
- python-pro (100% - M04 lead)
- devops-engineer (80% - M05 lead)
- multi-agent-coordinator (100% - M06 lead)
- test-automator (60% - M06 support)

**Key Deliverables**:
- Interactive onboarding wizard
- Deployment generation (Docker Compose + Justfile)
- Coordination testing framework

**Risk**: M06 complexity could extend timeline; functional tests require real MCP servers

### Phase 3 (Days 17-24): Polish & Documentation

**Active Agents**:
- python-pro (40% - M07 lead)
- technical-writer (100% - M08 lead)
- test-automator (100% - M09 lead)
- multi-agent-coordinator (60% - M10 lead)

**Key Deliverables**:
- Configuration management commands
- Comprehensive documentation
- Full test suite
- Release candidate

**Risk**: Documentation completeness may require extending M08; parallel work requires good coordination

## Inter-Milestone Data Flow

### Configuration Flow

```
M01: XDG Dirs → M02: Config Schema → M04: User Input → M05: Deployment Config
                                                            ↓
                                                      M06: Test Config
                                                            ↓
                                                      M07: Config Management
```

### Service Detection Flow

```
M03: Service Info → M04: Service Selection → M05: Deployment Generation
                                                       ↓
                                                  M06: Service Testing
```

### Testing & Documentation Flow

```
M06: Test Patterns → M08: Test Documentation
                  ↘
                   M09: Full Test Suite
```

## Risk Analysis by Dependency

### High-Risk Dependencies

1. **M01 → All**: If environment isolation fails, entire project blocked
   - **Mitigation**: Start M01 immediately, extensive platform testing
   - **Fallback**: Simplified isolation if XDG proves problematic

2. **M06 → M10**: If coordination tests fail, release blocked
   - **Mitigation**: Early prototyping of test patterns in M06
   - **Fallback**: Manual validation if automated tests incomplete

3. **M02 + M03 → M04**: If either config or detection incomplete, onboarding blocked
   - **Mitigation**: M02 and M03 parallel execution with clear interfaces
   - **Fallback**: Hardcoded defaults if detection unreliable

### Medium-Risk Dependencies

4. **M04 → M05**: User selections drive deployment generation
   - **Mitigation**: Default configurations allow M05 development before M04 complete
   - **Fallback**: Skip interactive mode, use config file directly

5. **M08 depends on M04, M05, M06**: Documentation requires complete features
   - **Mitigation**: Start high-level docs early, update with implementation details
   - **Fallback**: Iterate on docs post-release if needed

## Optimization Opportunities

### Early Starts

1. **M02 Prototyping**: Begin config schema design during M01
2. **M03 Detection Logic**: Start Docker detection during M01 (minimal dependencies)
3. **M08 Documentation Structure**: Create outline and examples before M04-M06 complete

### Parallel Execution

1. **Phase 1**: M02 and M03 can run simultaneously after M01
   - **Savings**: 1 day (M03 duration exceeds M02)

2. **Phase 3**: M07, M08, M09 fully parallel
   - **Savings**: 4 days (from 7 sequential to 3 parallel)

**Total Optimization**: 5 days savings

### Resource Smoothing

- **Days 1-3**: Single focus (M01) allows concentrated effort
- **Days 4-8**: Two parallel streams need coordination but manageable
- **Days 9-16**: Sequential execution simplifies coordination
- **Days 17-24**: Three parallel streams require strong coordination

## Timeline Scenarios

### Optimistic (15 days)

Assumes:
- No platform-specific issues in M01
- M03 service detection works first try
- M06 coordination tests minimal iteration
- Phase 3 parallel work perfect coordination

**Critical Path**: 15 days (3% risk, aggressive)

### Realistic (21 days)

Assumes:
- Minor platform tweaks in M01
- M03 requires iteration on detection logic
- M06 coordination tests need refinement
- Phase 3 minimal coordination overhead

**Critical Path**: 21 days (70% confidence, recommended planning baseline)

### Conservative (24 days)

Assumes:
- M01 platform issues require rework
- M03 detection edge cases
- M06 significant test refinement
- Phase 3 sequential fallback if coordination fails

**Critical Path**: 24 days (95% confidence, includes buffers)

## Milestone Interdependencies Summary

### Tier 1 (Foundation): M01

- **No dependencies**: Can start immediately
- **Critical blocker**: Blocks everything else
- **Duration**: 3 days
- **Risk**: High impact if delayed

### Tier 2 (Infrastructure): M02, M03

- **Depends on**: M01
- **Blocks**: M04, M05
- **Duration**: 2-3 days (parallel)
- **Risk**: Medium impact if delayed

### Tier 3 (Features): M04, M05, M06

- **Depends on**: M01, M02, M03
- **Blocks**: M07, M08, M09, M10
- **Duration**: 8 days (sequential)
- **Risk**: High impact if delayed

### Tier 4 (Polish): M07, M08, M09

- **Depends on**: Various (M02, M04, M05, M06)
- **Blocks**: M10
- **Duration**: 3 days (parallel)
- **Risk**: Low impact if delayed (can release with partial docs)

### Tier 5 (Release): M10

- **Depends on**: M06, M07, M08, M09
- **Blocks**: Nothing (project end)
- **Duration**: 2 days
- **Risk**: Low impact if delayed (quality gate)

## Resource Contention Analysis

### Potential Bottlenecks

1. **python-pro**: Needed for M01, M02, M04, M07
   - **Peak Load**: Days 1-8 (M01 + M02) and Days 9-11 (M04)
   - **Mitigation**: Clear task handoffs, code-reviewer can assist

2. **devops-engineer**: Needed for M03, M05
   - **Peak Load**: Days 4-8 (M03) and Days 12-13 (M05)
   - **Mitigation**: Well-distributed load

3. **multi-agent-coordinator**: Needed for M06, M10
   - **Peak Load**: Days 14-16 (M06)
   - **Mitigation**: test-automator assists in M06

### Load Balancing Strategies

- **Phase 1**: platform-engineer and python-pro share M01 tasks
- **Phase 2**: Dedicated agent per milestone (no sharing)
- **Phase 3**: Each agent owns one parallel track

## Implementation Recommendations

### Week 1 (Days 1-7)

**Focus**: Foundation milestones
- Days 1-3: All hands on M01 (environment isolation)
- Days 4-7: Split team M02 (python-pro) + M03 (devops-engineer)
- **Deliverable**: Working environment with service detection

### Week 2 (Days 8-14)

**Focus**: Core features
- Days 8-11: M04 interactive onboarding (python-pro lead)
- Days 12-13: M05 deployment generation (devops-engineer lead)
- Days 14: Start M06 coordination testing
- **Deliverable**: Working onboarding wizard generating deployments

### Week 3 (Days 15-21)

**Focus**: Testing and polish
- Days 15-16: Complete M06 coordination testing
- Days 17-19: M07 + M08 + M09 parallel execution
- Days 20-21: M10 final QA and release
- **Deliverable**: Production-ready release

---

**Document Version**: 1.0
**Last Updated**: 2025-10-13
**Status**: Approved - Ready for Implementation
