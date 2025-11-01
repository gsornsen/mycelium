# M03 Service Detection - Coordination Plan

**Coordinator**: multi-agent-coordinator **Start Date**: 2025-10-13 **Target Completion**: 3 days **Status**: INITIATED

## Executive Summary

M03 Service Detection implements intelligent infrastructure detection to enable adaptive onboarding. This milestone
detects Docker, Redis, PostgreSQL, Temporal, and GPU availability, enabling the system to recommend optimal deployment
strategies and avoid duplicate service deployments.

## Coordination Strategy

### Dependencies Validated

- **M01 Environment Isolation**: ✓ Complete (xdg_dirs, env_validator, config_loader)
- **M02 Configuration System**: ✓ Complete (schema, manager, migrations)

### Integration Points

- Uses M01 `get_cache_dir()` for caching detection results
- Uses M01 `validate_environment()` for runtime safety
- Will provide detection results to M04 (Interactive Onboarding)
- Will guide M05 (Deployment Generation) deployment choices

## Task Breakdown & Agent Assignment

### Phase 1: Service Detection (Parallel Execution)

#### Task 3.1: Docker Detection

- **Agent**: devops-engineer
- **Duration**: 6 hours
- **Status**: READY
- **Dependencies**: None (M01 complete)
- **Parallel Group**: A
- **Deliverables**:
  - `mycelium_onboarding/detection/docker.py`
  - `tests/test_docker_detection.py`
- **Acceptance Criteria**:
  - Detects Docker CLI presence
  - Gets Docker version correctly
  - Checks if Docker daemon is running
  - Detects Docker Compose (v1 and v2)
  - Handles timeouts gracefully (\<2s)
  - Returns clear error messages
  - Works on Linux, macOS, Windows (WSL2)

#### Task 3.2: Redis Detection

- **Agent**: devops-engineer
- **Duration**: 4 hours
- **Status**: READY
- **Dependencies**: None (pattern can be established independently)
- **Parallel Group**: A
- **Deliverables**:
  - `mycelium_onboarding/detection/redis.py`
  - `tests/test_redis_detection.py`
- **Acceptance Criteria**:
  - Detects Redis on standard port (6379)
  - Supports custom host and port
  - Gets Redis version via INFO command
  - Handles connection timeouts (\<2s)
  - Handles connection refused gracefully
  - Can scan multiple ports
  - No dependency on redis-py library

#### Task 3.3: PostgreSQL & Temporal Detection

- **Agent**: devops-engineer
- **Duration**: 6 hours
- **Status**: READY
- **Dependencies**: None (pattern can be established independently)
- **Parallel Group**: A
- **Deliverables**:
  - `mycelium_onboarding/detection/postgres.py`
  - `mycelium_onboarding/detection/temporal.py`
  - `tests/test_postgres_detection.py`
  - `tests/test_temporal_detection.py`
- **Acceptance Criteria**:
  - PostgreSQL detection via socket connection
  - Temporal frontend (gRPC) and UI (HTTP) detection
  - Version detection where possible
  - Timeout handling (\<2s per service)
  - Clear error messages

#### Task 3.4: GPU Detection

- **Agent**: platform-engineer
- **Duration**: 6 hours
- **Status**: READY
- **Dependencies**: None (independent implementation)
- **Parallel Group**: B
- **Deliverables**:
  - `mycelium_onboarding/detection/gpu.py`
  - `tests/test_gpu_detection.py`
- **Acceptance Criteria**:
  - Detects NVIDIA GPUs via nvidia-smi
  - Detects AMD GPUs via rocm-smi
  - Counts multiple GPUs
  - Gets driver and CUDA/ROCm versions
  - Handles missing drivers gracefully
  - Fast detection (\<2s)

### Phase 2: Orchestration & Integration

#### Task 3.5: Detection Orchestrator & Caching

- **Agent**: python-pro
- **Duration**: 6 hours
- **Status**: BLOCKED (awaiting Phase 1)
- **Dependencies**: Tasks 3.1, 3.2, 3.3, 3.4
- **Parallel Group**: N/A (sequential after Phase 1)
- **Deliverables**:
  - `mycelium_onboarding/detection/orchestrator.py`
  - `mycelium_onboarding/cli/detect_commands.py`
  - `tests/test_detection_orchestrator.py`
- **Acceptance Criteria**:
  - Runs all detections in parallel (\<5s total)
  - Caches results to avoid repeated detection
  - Respects cache TTL (default 5 minutes)
  - CLI command outputs text and JSON formats
  - --no-cache flag forces fresh detection
  - Integration with XDG cache directory

## Coordination Mechanisms

### Parallel Execution Strategy

**Group A: Service Detection (Tasks 3.1, 3.2, 3.3)**

- All tasks can execute in parallel
- Independent implementations following established patterns
- Agent: devops-engineer handles all three
- Expected completion: 6 hours (longest task is 3.3)

**Group B: GPU Detection (Task 3.4)**

- Independent from Group A
- Can execute in parallel
- Agent: platform-engineer
- Expected completion: 6 hours

**Sequential: Orchestration (Task 3.5)**

- Depends on completion of all Phase 1 tasks
- Agent: python-pro
- Expected completion: 6 hours after Phase 1

### Inter-Agent Communication

**Message Protocol**:

```json
{
  "type": "task_status",
  "agent": "agent-id",
  "task": "3.x",
  "status": "in_progress|completed|blocked",
  "progress": 0-100,
  "deliverables": ["file1.py", "file2.py"],
  "blockers": []
}
```

**Synchronization Points**:

1. **Phase 1 Completion Gate**: All Phase 1 tasks must complete before Phase 2
1. **Test Coverage Gate**: Each task must achieve ≥85% coverage before completion
1. **Quality Gate**: Zero linting issues, 100% type safety

### Progress Tracking

**Metrics Collection**:

- Task completion percentage
- Test coverage per module
- Code quality metrics (mypy, ruff)
- Performance benchmarks (detection speed)

**Status Updates**:

- Agents report status every 2 hours
- Coordinator checks progress every hour
- Blockers escalated immediately

## Quality Standards

### Code Quality

- **Test Coverage**: ≥85% per module
- **Type Safety**: 100% (mypy --strict)
- **Linting**: 0 issues (ruff check)
- **Performance**: \<5s total detection time

### Testing Requirements

- **Unit Tests**: Each detector module
- **Integration Tests**: Orchestrator with all detectors
- **Mock Tests**: Simulate service availability/unavailability
- **Platform Tests**: Linux primary, macOS/WSL2 compatibility

### Documentation Requirements

- **API Documentation**: All public functions documented
- **Usage Examples**: CLI commands with examples
- **Troubleshooting Guide**: Common detection failures
- **Integration Guide**: How M04 and M05 will use detection

## Risk Management

### High Risk: Docker Daemon Not Running

- **Impact**: Most common failure case, blocks containerized deployment
- **Detection**: Task 3.1 must clearly identify running vs installed
- **Mitigation**: Clear error message with instructions to start Docker
- **Contingency**: Offer Justfile deployment as fallback

### Medium Risk: Firewall Blocking Service Connections

- **Impact**: Services may appear unavailable when just firewalled
- **Detection**: Socket connection failures
- **Mitigation**: Document common firewall issues
- **Contingency**: Allow manual override in wizard (M04)

### Medium Risk: GPU Detection Inconsistency

- **Impact**: GPU present but drivers not installed
- **Detection**: nvidia-smi/rocm-smi not found
- **Mitigation**: Document GPU detection requirements
- **Contingency**: GPU is optional, gracefully handle absence

### Low Risk: Cache Corruption

- **Impact**: Cached JSON becomes corrupted
- **Detection**: JSON parse errors in orchestrator
- **Mitigation**: Validate cache on load, discard if invalid
- **Contingency**: Fall back to fresh detection

## Acceptance Criteria (Exit Gate)

### Service Detection

- [ ] Docker detection working (CLI, version, Compose)
- [ ] Redis detection working (socket connection, version)
- [ ] PostgreSQL detection working
- [ ] Temporal detection working (frontend + UI)
- [ ] GPU detection working (NVIDIA + AMD)

### Detection Orchestrator

- [ ] Parallel execution (\<5s total)
- [ ] Caching implemented with configurable TTL
- [ ] Cache invalidation working

### CLI Integration

- [ ] `mycelium detect` command working
- [ ] Text and JSON output formats
- [ ] --no-cache flag working

### Testing

- [ ] Unit tests for each detector (≥85% coverage)
- [ ] Integration tests with mock services
- [ ] Platform compatibility tests (Linux primarily)

### Documentation

- [ ] Detection logic documented
- [ ] Cache behavior explained
- [ ] Troubleshooting guide for detection failures

### Quality Gates

- [ ] All tests passing: `uv run pytest tests/ --cov=mycelium_onboarding`
- [ ] Type checking passing: `uv run mypy mycelium_onboarding --strict`
- [ ] Linting passing: `uv run ruff check mycelium_onboarding`
- [ ] Test coverage ≥85%

## Agent Prompts

### For devops-engineer (Tasks 3.1, 3.2, 3.3)

```
You are implementing service detection for the Mycelium onboarding system (M03).

CONTEXT:
- M01 (Environment Isolation) and M02 (Configuration System) are complete
- Detection results will guide M04 (Interactive Onboarding) and M05 (Deployment Generation)
- Use XDG cache directory from mycelium_onboarding.xdg_dirs.get_cache_dir()

YOUR TASKS:
1. Implement Docker detection (mycelium_onboarding/detection/docker.py)
2. Implement Redis detection (mycelium_onboarding/detection/redis.py)
3. Implement PostgreSQL & Temporal detection (mycelium_onboarding/detection/postgres.py, temporal.py)

REQUIREMENTS:
- Detection timeout: 2s per service
- No external service dependencies (use socket/subprocess only)
- Graceful error handling (not found is not an error)
- Cross-platform compatibility (Linux, macOS, WSL2)
- Type-safe with dataclasses
- Comprehensive unit tests (≥85% coverage)

IMPLEMENTATION GUIDE:
Follow the patterns in docs/projects/onboarding/milestones/M03_SERVICE_DETECTION.md

Key points:
- Use shutil.which() for command detection
- Use subprocess.run() with timeout parameter
- Use socket.create_connection() for network checks
- Return dataclass Info objects (DockerInfo, RedisInfo, etc.)
- Handle timeouts and connection failures gracefully

QUALITY STANDARDS:
- mypy --strict must pass
- ruff check must pass
- pytest coverage ≥85%
- All timeouts <2s per check

DELIVERABLES:
- mycelium_onboarding/detection/docker.py
- mycelium_onboarding/detection/redis.py
- mycelium_onboarding/detection/postgres.py
- mycelium_onboarding/detection/temporal.py
- tests/test_docker_detection.py
- tests/test_redis_detection.py
- tests/test_postgres_detection.py
- tests/test_temporal_detection.py

Run tests with: uv run pytest tests/test_*_detection.py -v --cov
```

### For platform-engineer (Task 3.4)

```
You are implementing GPU detection for the Mycelium onboarding system (M03).

CONTEXT:
- M01 (Environment Isolation) and M02 (Configuration System) are complete
- GPU detection enables acceleration recommendations in deployment
- This runs in parallel with service detection (Tasks 3.1-3.3)

YOUR TASK:
Implement GPU detection (mycelium_onboarding/detection/gpu.py)

REQUIREMENTS:
- Detect NVIDIA GPUs via nvidia-smi
- Detect AMD GPUs via rocm-smi
- Report GPU count, type, driver version, CUDA/ROCm version
- Detection timeout: 2s total
- Gracefully handle missing drivers (common case)
- Type-safe with dataclasses and Enum
- Comprehensive unit tests (≥85% coverage)

IMPLEMENTATION GUIDE:
Follow the pattern in docs/projects/onboarding/milestones/M03_SERVICE_DETECTION.md (Task 3.4)

Key points:
- Use shutil.which() to check for nvidia-smi/rocm-smi
- Use subprocess.run() with timeout=2.0
- Parse command output to extract device info
- Return GPUInfo dataclass with GPUType enum
- No GPU found is not an error - return available=False

QUALITY STANDARDS:
- mypy --strict must pass
- ruff check must pass
- pytest coverage ≥85%
- Detection <2s

DELIVERABLES:
- mycelium_onboarding/detection/gpu.py
- tests/test_gpu_detection.py

Run tests with: uv run pytest tests/test_gpu_detection.py -v --cov
```

### For python-pro (Task 3.5)

```
You are implementing the detection orchestrator for Mycelium onboarding (M03).

CONTEXT:
- M01 (Environment Isolation) and M02 (Configuration System) are complete
- All individual detectors implemented (Tasks 3.1-3.4)
- This orchestrator coordinates parallel detection and caching

YOUR TASK:
Implement detection orchestrator and CLI integration

COMPONENTS:
1. Orchestrator (mycelium_onboarding/detection/orchestrator.py)
   - Parallel execution using asyncio.gather()
   - Caching with configurable TTL (default 5 minutes)
   - Integration with XDG cache directory
   - DetectionResults dataclass aggregating all results

2. CLI Commands (mycelium_onboarding/cli/detect_commands.py)
   - `mycelium detect` command
   - Text and JSON output formats
   - --no-cache flag for fresh detection
   - Human-readable status display

REQUIREMENTS:
- Total detection time <5s (parallel execution)
- Cache stored in XDG cache directory (get_cache_dir())
- Type-safe DetectionResults dataclass
- Comprehensive unit tests (≥85% coverage)

IMPLEMENTATION GUIDE:
Follow the patterns in docs/projects/onboarding/milestones/M03_SERVICE_DETECTION.md (Task 3.5)

Key points:
- Use asyncio.to_thread() for parallel detection
- Cache as JSON in get_cache_dir() / "service-detection.json"
- Check cache timestamp, respect TTL
- Serialize dataclasses using asdict()
- CLI uses click for commands

QUALITY STANDARDS:
- mypy --strict must pass
- ruff check must pass
- pytest coverage ≥85%
- Parallel execution <5s total

DELIVERABLES:
- mycelium_onboarding/detection/orchestrator.py
- mycelium_onboarding/cli/detect_commands.py
- tests/test_detection_orchestrator.py
- Integration tests with all detectors

INTEGRATION:
Import all detectors:
- from mycelium_onboarding.detection.docker import detect_docker
- from mycelium_onboarding.detection.redis import detect_redis
- from mycelium_onboarding.detection.postgres import detect_postgres
- from mycelium_onboarding.detection.temporal import detect_temporal
- from mycelium_onboarding.detection.gpu import detect_gpu

Run tests with: uv run pytest tests/test_detection_orchestrator.py -v --cov
```

## Execution Timeline

### Day 1: Phase 1 Parallel Execution (6 hours)

- **Hour 0-6**: Launch all Phase 1 agents in parallel
  - devops-engineer: Tasks 3.1, 3.2, 3.3
  - platform-engineer: Task 3.4
- **Hour 6**: Phase 1 completion check
  - Verify all deliverables present
  - Run test suites
  - Check quality gates

### Day 2: Phase 2 Orchestration (6 hours)

- **Hour 0-6**: python-pro implements orchestrator (Task 3.5)
  - Parallel execution framework
  - Caching mechanism
  - CLI integration
- **Hour 6**: Phase 2 completion check
  - Integration tests
  - End-to-end detection test
  - Performance benchmarks

### Day 3: Integration & Documentation (6 hours)

- **Hour 0-3**: Integration testing
  - Cross-platform validation
  - Performance optimization
  - Bug fixes
- **Hour 3-6**: Documentation
  - API documentation
  - Usage examples
  - Troubleshooting guide
- **Hour 6**: Final acceptance criteria validation

## Success Metrics

### Performance Metrics

- Total detection time: \<5s
- Individual detector timeout: \<2s
- Cache hit rate: >80% in typical usage
- Memory usage: \<50MB during detection

### Quality Metrics

- Test coverage: ≥85% per module
- Type safety: 100% (mypy --strict)
- Linting: 0 issues (ruff)
- Code complexity: \<10 per function

### Functional Metrics

- Docker detection accuracy: 100%
- Service reachability detection: 100%
- GPU detection accuracy: 100% (when present)
- Platform compatibility: Linux (primary), macOS/WSL2 (secondary)

## Handoff to Next Milestones

### M04: Interactive Onboarding

**Integration Points**:

- Import: `from mycelium_onboarding.detection.orchestrator import detect_all_services`
- Usage: Pre-fill wizard defaults with detected services
- Logic: Enable/disable service options based on detection
- Error handling: Show detection errors, allow manual override

**Example Integration**:

```python
# In M04 wizard
results = asyncio.run(detect_all_services())
if results.docker.available and results.docker.running:
    default_deployment = "docker-compose"
else:
    default_deployment = "justfile"
```

### M05: Deployment Generation

**Integration Points**:

- Import: `from mycelium_onboarding.detection.orchestrator import detect_all_services`
- Usage: Decide what services to deploy based on detection
- Logic: Skip deploying already-running services
- Port selection: Use detected ports to avoid conflicts

**Example Integration**:

```python
# In M05 deployment generator
results = asyncio.run(detect_all_services())
if results.redis.available and results.redis.reachable:
    # Skip Redis deployment, use existing
    config["redis"]["external"] = True
    config["redis"]["host"] = results.redis.host
    config["redis"]["port"] = results.redis.port
```

## Monitoring & Status

### Real-Time Coordination Tracking

Stored in: `~/.local/state/mycelium/coordination/M03_status.json`

```json
{
  "milestone": "M03",
  "status": "in_progress",
  "start_time": "2025-10-13T10:00:00Z",
  "phases": {
    "phase1": {
      "status": "in_progress",
      "tasks": {
        "3.1": {"status": "in_progress", "agent": "devops-engineer", "progress": 40},
        "3.2": {"status": "in_progress", "agent": "devops-engineer", "progress": 30},
        "3.3": {"status": "in_progress", "agent": "devops-engineer", "progress": 20},
        "3.4": {"status": "in_progress", "agent": "platform-engineer", "progress": 50}
      }
    },
    "phase2": {
      "status": "blocked",
      "tasks": {
        "3.5": {"status": "blocked", "agent": "python-pro", "progress": 0}
      }
    }
  },
  "metrics": {
    "test_coverage": 0,
    "type_safety": 0,
    "linting_issues": 0
  }
}
```

### Escalation Criteria

- Any task blocked for >2 hours
- Test coverage falls below 85%
- Type safety issues detected
- Performance requirements not met
- Agent unresponsive for >1 hour

## Final Deliverables Checklist

### Code Modules

- [ ] mycelium_onboarding/detection/__init__.py
- [ ] mycelium_onboarding/detection/docker.py
- [ ] mycelium_onboarding/detection/redis.py
- [ ] mycelium_onboarding/detection/postgres.py
- [ ] mycelium_onboarding/detection/temporal.py
- [ ] mycelium_onboarding/detection/gpu.py
- [ ] mycelium_onboarding/detection/orchestrator.py
- [ ] mycelium_onboarding/cli/detect_commands.py

### Tests

- [ ] tests/test_docker_detection.py
- [ ] tests/test_redis_detection.py
- [ ] tests/test_postgres_detection.py
- [ ] tests/test_temporal_detection.py
- [ ] tests/test_gpu_detection.py
- [ ] tests/test_detection_orchestrator.py
- [ ] tests/integration/test_detection_flow.py

### Documentation

- [ ] docs/service-detection.md
- [ ] docs/troubleshooting-detection.md
- [ ] API documentation in docstrings
- [ ] CLI help text

### Validation

- [ ] All tests passing
- [ ] Coverage ≥85%
- [ ] Type checking passing
- [ ] Linting passing
- [ ] Cross-platform tested
- [ ] Performance benchmarks met

______________________________________________________________________

**Coordination Status**: ACTIVE **Next Review**: 2 hours from start **Escalation Contact**: multi-agent-coordinator

This coordination plan will be updated in real-time as tasks progress.
