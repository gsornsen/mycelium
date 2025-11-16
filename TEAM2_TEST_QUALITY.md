# Team 2: Test & Quality Team

**Priority**: 🟡 HIGH (Need for PR merge) **Branch**: `fix/test-quality-errors` (create from current branch) **Lead
Agent**: `qa-expert` **Support Agents**: `python-pro`, `code-reviewer` **Status**: READY TO START **Estimated Time**:
1.5-2 hours

## Mission

Fix all manual ruff errors, resolve 5 unit test failures, address Pydantic deprecation warnings, and fix pytest
collection warnings. Your team owns test quality and code cleanliness.

## File Ownership (No Conflicts with Team 1)

**Your Territory**:

- `tests/*.py` - ALL test files (for manual fixes)
- `tests/test_cli_config.py` - Test failures (5 tests)
- Pydantic deprecation fixes in source files
- Pytest collection warning fixes

**Team 1 Territory (DO NOT TOUCH)**:

- `mycelium_onboarding/*.py` - Type fixes only
- `plugins/*.py` - Type fixes only
- Auto-fixable ruff errors (already handled by Team 1)

## Setup Commands

```bash
# 1. Create your branch
cd /home/gerald/git/mycelium
git checkout feat/phase2-smart-onboarding-unified
git pull origin feat/phase2-smart-onboarding-unified
git checkout -b fix/test-quality-errors

# 2. Verify environment
uv sync --frozen --all-extras --group dev

# 3. Baseline assessment
echo "=== BASELINE: MANUAL RUFF ERRORS ===" > team2-progress.log
uv run ruff check tests/ 2>&1 | grep -v "\[\*\]" | tee -a team2-progress.log

echo "\n=== BASELINE: TEST FAILURES ===" >> team2-progress.log
uv run pytest tests/test_cli_config.py -v 2>&1 | grep "FAILED" | tee -a team2-progress.log

echo "\n=== BASELINE: DEPRECATION WARNINGS ===" >> team2-progress.log
uv run pytest tests/unit/ --tb=no -q 2>&1 | grep "PydanticDeprecatedSince20" | tee -a team2-progress.log
```

## Task 1: Fix Manual Ruff Errors (36 errors) - 45 minutes

### Category 1: PTH123 - Replace open() with Path.open() (1 error)

**Location**: `tests/deployment/postgres/test_compatibility.py:48`

**Error**: `PTH123 open() should be replaced by Path.open()`

**Fix**:

```python
# Before:
def matrix_data(matrix_path: Path) -> dict[str, Any]:
    """Load raw matrix data from YAML."""
    with open(matrix_path, encoding="utf-8") as f:
        return yaml.safe_load(f)

# After:
def matrix_data(matrix_path: Path) -> dict[str, Any]:
    """Load raw matrix data from YAML."""
    with matrix_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)
```

### Category 2: SIM105 - Use contextlib.suppress() (2 errors)

**Locations**:

- `tests/integration/deployment/workflows/test_workflow_integration.py:156`
- `tests/integration/test_state_manager.py:20`

**Fix**:

```python
import contextlib

# Before (test_workflow_integration.py:156):
try:
    await worker_task
except asyncio.CancelledError:
    pass

# After:
with contextlib.suppress(asyncio.CancelledError):
    await worker_task

# Before (test_state_manager.py:20):
try:
    from coordination.state_manager import (
        StateManager,
        StateNotFoundError,
        TaskState,
        TaskStatus,
        WorkflowStatus,
    )
except ImportError:
    pass

# After:
with contextlib.suppress(ImportError):
    from coordination.state_manager import (
        StateManager,
        StateNotFoundError,
        TaskState,
        TaskStatus,
        WorkflowStatus,
    )
```

### Category 3: SIM117 - Combine nested with statements (5 errors)

**Locations**:

- `tests/unit/deployment/commands/test_deploy_validation.py:117`
- `tests/unit/deployment/commands/test_deploy_validation.py:146`
- `tests/unit/deployment/commands/test_deploy_validation.py:309`
- `tests/unit/deployment/commands/test_deploy_validation.py:318`
- `tests/unit/deployment/workflows/test_test_workflow.py:276`

**Fix Pattern**:

```python
# Before:
with patch("some.path") as mock1:
    with patch("other.path") as mock2:
        # code

# After:
with (
    patch("some.path") as mock1,
    patch("other.path") as mock2,
):
    # code

# Or:
with patch("some.path") as mock1, patch("other.path") as mock2:
    # code
```

**Specific Fixes**:

```python
# test_deploy_validation.py:117
# Before:
with patch("mycelium_onboarding.deployment.commands.deploy.WarningFormatter") as mock_fmt:
    with patch("mycelium_onboarding.deployment.commands.deploy.Confirm.ask", return_value=False):
        result = deploy_command._validate_postgres_compatibility(detected_services_with_postgres)

# After:
with (
    patch("mycelium_onboarding.deployment.commands.deploy.WarningFormatter") as mock_fmt,
    patch("mycelium_onboarding.deployment.commands.deploy.Confirm.ask", return_value=False),
):
    result = deploy_command._validate_postgres_compatibility(detected_services_with_postgres)

# test_test_workflow.py:276
# Before:
async with await WorkflowEnvironment.start_time_skipping() as env:
    async with Worker(
        env.client,
        task_queue="test-queue",
        workflows=[TestWorkflow],
        activities=[...],
    ):
        # code

# After:
async with (
    await WorkflowEnvironment.start_time_skipping() as env,
    Worker(
        env.client,
        task_queue="test-queue",
        workflows=[TestWorkflow],
        activities=[...],
    ),
):
    # code
```

### Category 4: RET504 - Remove unnecessary assignments (1 error)

**Location**: `tests/integration/deployment/workflows/test_workflow_integration.py:56`

**Fix**:

```python
# Before:
def temporal_worker(temporal_client):
    worker = Worker(
        temporal_client,
        task_queue=TEMPORAL_TASK_QUEUE,
        workflows=[TestWorkflow],
        activities=[...],
    )
    return worker

# After:
def temporal_worker(temporal_client):
    return Worker(
        temporal_client,
        task_queue=TEMPORAL_TASK_QUEUE,
        workflows=[TestWorkflow],
        activities=[...],
    )
```

### Category 5: F841 - Remove unused variables (15 errors - manual review)

**Strategy**: For each, determine if:

1. Variable is actually used but ruff can't see it (keep it)
1. Variable is test assertion that's commented out (uncomment or remove)
1. Variable is truly unused (remove it)

**Locations**:

```
tests/integration/test_smart_deployment.py:151 (result)
tests/integration/test_smart_deployment.py:215 (result)
tests/integration/test_smart_deployment.py:249 (result)
tests/integration/test_smart_deployment.py:281 (result)
tests/integration/test_smart_deployment.py:382 (planner)
tests/unit/cli_commands/test_config_commands.py:337 (result)
tests/unit/cli_commands/test_config_commands.py:474 (config_path)
tests/unit/cli_commands/test_config_commands.py:491 (config_path)
tests/unit/config/migration/test_detector.py:173 (configs1)
tests/unit/config/migration/test_detector.py:259 (has_conflict)
tests/unit/config/migration/test_executor.py:262 (result)
tests/unit/config/migration/test_integration.py:168 (merge_steps)
tests/unit/config/migration/test_planner.py:167 (create_steps)
tests/unit/config/migration/test_planner.py:182 (plan)
tests/unit/config/migration/test_planner.py:363 (skip_steps)
tests/unit/config/test_platform.py:142 (sep)
tests/unit/config/test_platform.py:151 (sep)
tests/unit/deployment/commands/test_deploy_validation.py:88 (mock_fmt) - 6 instances
tests/unit/deployment/commands/test_deploy_validation.py:412 (result)
tests/unit/deployment/commands/test_deploy_validation.py:430 (result)
tests/unit/deployment/commands/test_deploy_validation.py:449 (result)
```

**Fix Pattern**:

```python
# Option 1: Variable used in assertion (keep it, add assertion)
result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)
assert result is not None  # Add this

# Option 2: Variable truly unused (remove it)
# Before:
result = runner.invoke(cli, ["deploy", "start"])
# After:
runner.invoke(cli, ["deploy", "start"])

# Option 3: Variable needed for test but not asserted (keep with _ prefix)
_result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)
```

### Commit After Task 1

```bash
git add tests/

git commit -m "fix(tests): resolve 36 manual ruff errors

- PTH123: Replace open() with Path.open() (1 fix)
- SIM105: Use contextlib.suppress() (2 fixes)
- SIM117: Combine nested with statements (5 fixes)
- RET504: Remove unnecessary assignment (1 fix)
- F841: Remove unused variables (27 fixes)

All manual ruff errors resolved by Team 2"

# Verify
uv run ruff check tests/ 2>&1 | tail -5 | tee -a team2-progress.log
```

## Task 2: Fix Unit Test Failures (5 failures) - 30 minutes

### All 5 Failures in tests/test_cli_config.py

**Pattern**: All tests exit with code 2 instead of expected 0

**Test Names**:

1. `test_config_get_top_level`
1. `test_config_get_nested`
1. `test_config_get_deployment_method`
1. `test_config_get_nonexistent_key`
1. `test_config_get_invalid_nested_key`

### Investigation

```bash
# Run tests to see detailed failures
uv run pytest tests/test_cli_config.py::test_config_get_top_level -vv

# Expected pattern: exit_code is 2 but should be 0
# This usually means:
# 1. Command not found (CLI not properly installed)
# 2. Import error in CLI code
# 3. Configuration error
```

### Likely Root Cause

Based on pattern (all config get commands failing with exit code 2):

**Hypothesis 1: CLI entry point issue**

```python
# Check if mycelium CLI is properly installed
# Run: uv run mycelium config get deployment.method
# If it fails, the CLI isn't installed in the test environment
```

**Hypothesis 2: Import path issue**

```python
# The tests use CliRunner which invokes the CLI
# Exit code 2 typically means import failure or bad arguments
```

**Fix Strategy**:

```python
# Check tests/test_cli_config.py structure
# Look for:
# 1. CliRunner invocation
# 2. CLI command import
# 3. Mock setup

# Likely fix needed in tests/test_cli_config.py:

# Before (if using direct command):
from mycelium_onboarding.cli import cli
result = runner.invoke(cli, ["config", "get", "deployment.method"])

# After (ensure proper imports):
from mycelium_onboarding.cli_commands.cli import cli
from click.testing import CliRunner

def test_config_get_top_level(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Setup config file
        config_path = Path.cwd() / ".mycelium" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("deployment:\n  method: docker\n")

        # Run command with proper environment
        result = runner.invoke(cli, ["config", "get", "deployment.method"])

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "docker" in result.output
```

### Detailed Investigation Commands

```bash
# 1. Look at test implementation
cat tests/test_cli_config.py | grep -A 20 "def test_config_get_top_level"

# 2. Check CLI entry point
grep -r "def cli(" mycelium_onboarding/cli_commands/

# 3. Run single test with full output
uv run pytest tests/test_cli_config.py::test_config_get_top_level -vvs --tb=short

# 4. Check if it's an import issue
python -c "from mycelium_onboarding.cli_commands.cli import cli; print('OK')"
```

### Fix Based on Investigation

Once you identify the root cause, apply the appropriate fix:

**Fix Type A: Missing config file in test**

```python
@pytest.fixture
def setup_test_config(tmp_path):
    config_path = tmp_path / ".mycelium" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("deployment:\n  method: docker\n")
    return config_path

def test_config_get_top_level(setup_test_config):
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "get", "deployment.method"],
                          env={"MYCELIUM_CONFIG_DIR": str(setup_test_config.parent)})
    assert result.exit_code == 0
```

**Fix Type B: Mock missing**

```python
def test_config_get_top_level(tmp_path):
    runner = CliRunner()

    with patch("mycelium_onboarding.cli_commands.commands.config.ConfigManager") as mock:
        mock_instance = MagicMock()
        mock_instance.get.return_value = "docker"
        mock.return_value = mock_instance

        result = runner.invoke(cli, ["config", "get", "deployment.method"])
        assert result.exit_code == 0
```

### Commit After Task 2

```bash
git add tests/test_cli_config.py

git commit -m "fix(tests): resolve 5 unit test failures in test_cli_config.py

- Fix config get command exit code issues
- Ensure proper test environment setup
- Add missing mocks/fixtures for config access
- All config get tests now passing

Tests fixed:
- test_config_get_top_level
- test_config_get_nested
- test_config_get_deployment_method
- test_config_get_nonexistent_key
- test_config_get_invalid_nested_key

Fixes exit code 2 -> 0 errors"

# Verify all pass
uv run pytest tests/test_cli_config.py -v | tee -a team2-progress.log
```

## Task 3: Fix Pydantic Deprecation Warnings (4 warnings) - 20 minutes

### Locations

1. `mycelium_onboarding/deployment/strategy/detector.py:80`
1. `mycelium_onboarding/deployment/postgres/version_manager.py:92`
1. `mycelium_onboarding/deployment/commands/deploy.py:124`

All warnings: `PydanticDeprecatedSince20: Support for class-based config is deprecated, use ConfigDict instead.`

### Fix Pattern

```python
# Before (deprecated):
from pydantic import BaseModel

class MyModel(BaseModel):
    field: str

    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True

# After (Pydantic V2):
from pydantic import BaseModel, ConfigDict

class MyModel(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    field: str
```

### Specific Fixes

**File 1: detector.py:80**

```python
# Location: mycelium_onboarding/deployment/strategy/detector.py

# Before:
class DetectedService(BaseModel):
    service_name: str
    version: str | None = None

    class Config:
        arbitrary_types_allowed = True

# After:
from pydantic import ConfigDict

class DetectedService(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    service_name: str
    version: str | None = None
```

**File 2: version_manager.py:92**

```python
# Location: mycelium_onboarding/deployment/postgres/version_manager.py

# Before:
class CompatibilityMatrix(BaseModel):
    postgres_versions: dict[str, Any]
    temporal_versions: dict[str, Any]

    class Config:
        arbitrary_types_allowed = True

# After:
from pydantic import ConfigDict

class CompatibilityMatrix(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    postgres_versions: dict[str, Any]
    temporal_versions: dict[str, Any]
```

**File 3: deploy.py:124**

```python
# Location: mycelium_onboarding/deployment/commands/deploy.py

# Before:
class DeploymentPlan(BaseModel):
    services: list[str]
    method: DeploymentMethod

    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True

# After:
from pydantic import ConfigDict

class DeploymentPlan(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        arbitrary_types_allowed=True,
    )

    services: list[str]
    method: DeploymentMethod
```

### Commit After Task 3

```bash
git add mycelium_onboarding/deployment/strategy/detector.py \
        mycelium_onboarding/deployment/postgres/version_manager.py \
        mycelium_onboarding/deployment/commands/deploy.py

git commit -m "fix(pydantic): migrate from class Config to ConfigDict

- Update DetectedService model in detector.py
- Update CompatibilityMatrix model in version_manager.py
- Update DeploymentPlan model in deploy.py
- Resolve all PydanticDeprecatedSince20 warnings

Pydantic V2 migration complete (4 models updated)"

# Verify warnings gone
uv run pytest tests/unit/ -q --tb=no 2>&1 | grep "PydanticDeprecatedSince20" | wc -l
# Expected: 0
```

## Task 4: Fix Pytest Collection Warnings (2 warnings) - 15 minutes

### Warning 1: TestRunner class

**Location**: `mycelium_onboarding/deployment/workflows/test_runner.py:103`

**Warning**: `PytestCollectionWarning: cannot collect test class 'TestRunner' because it has a __init__ constructor`

**Issue**: Pytest thinks this is a test class (starts with "Test") but it's not - it's production code.

**Fix Options**:

```python
# Option 1: Rename class (cleanest)
# Before:
class TestRunner:
    def __init__(self, ...):
        pass

# After:
class WorkflowTestRunner:  # or TemporalTestRunner
    def __init__(self, ...):
        pass

# Option 2: Add pytest marker to ignore
# Before:
class TestRunner:
    def __init__(self, ...):
        pass

# After:
class TestRunner:
    __test__ = False  # Tell pytest not to collect

    def __init__(self, ...):
        pass
```

**Recommendation**: Use Option 1 (rename) as it's clearer and follows naming conventions.

### Warning 2: TestWorkflow class

**Location**: `mycelium_onboarding/deployment/workflows/test_workflow.py:276`

**Warning**: `PytestCollectionWarning: cannot collect test class 'TestWorkflow' because it has a __init__ constructor`

**Issue**: This is a Temporal workflow definition, not a pytest test class.

**Fix Options**:

```python
# Option 1: Rename class
# Before:
@workflow.defn(name="TestWorkflow")
class TestWorkflow:
    def __init__(self):
        pass

# After:
@workflow.defn(name="TestWorkflow")
class ValidationWorkflow:  # or IntegrationTestWorkflow
    def __init__(self):
        pass

# Option 2: Add pytest marker
# Before:
@workflow.defn(name="TestWorkflow")
class TestWorkflow:
    def __init__(self):
        pass

# After:
@workflow.defn(name="TestWorkflow")
class TestWorkflow:
    __test__ = False

    def __init__(self):
        pass
```

**Recommendation**: Use Option 2 (`__test__ = False`) since the Temporal workflow name is "TestWorkflow" and changing
the class name could break Temporal registration.

### Implementation

```bash
# Fix 1: TestRunner rename
sed -i 's/class TestRunner:/class WorkflowTestRunner:/g' \
    mycelium_onboarding/deployment/workflows/test_runner.py

# Update all references
sed -i 's/TestRunner(/WorkflowTestRunner(/g' \
    mycelium_onboarding/deployment/workflows/*.py tests/**/*.py

# Fix 2: TestWorkflow marker
# Edit mycelium_onboarding/deployment/workflows/test_workflow.py
# Add __test__ = False after class definition
```

### Commit After Task 4

```bash
git add mycelium_onboarding/deployment/workflows/test_runner.py \
        mycelium_onboarding/deployment/workflows/test_workflow.py

git commit -m "fix(pytest): resolve collection warnings for non-test classes

- Rename TestRunner to WorkflowTestRunner for clarity
- Add __test__ = False to TestWorkflow Temporal class
- Prevent pytest from attempting to collect production classes

Resolves 2 PytestCollectionWarning issues"

# Verify warnings gone
uv run pytest tests/unit/ --collect-only 2>&1 | grep "PytestCollectionWarning" | wc -l
# Expected: 0
```

## Final Validation

```bash
# 1. All manual ruff errors fixed
uv run ruff check tests/
# Expected: Found 0 errors

# 2. All unit tests pass
uv run pytest tests/unit/ tests/test_*.py -v \
  -m "not integration and not benchmark and not slow" \
  --tb=short
# Expected: All passed, no failures

# 3. Specific test file passes
uv run pytest tests/test_cli_config.py -v
# Expected: All 5 tests pass

# 4. No Pydantic deprecation warnings
uv run pytest tests/unit/ -q --tb=no 2>&1 | grep "PydanticDeprecatedSince20"
# Expected: No output (0 warnings)

# 5. No pytest collection warnings
uv run pytest tests/unit/ --collect-only 2>&1 | grep "PytestCollectionWarning"
# Expected: No output (0 warnings)

# 6. Generate final report
echo "=== TEAM 2 FINAL REPORT ===" > team2-final-report.txt
echo "\nRuff Status:" >> team2-final-report.txt
uv run ruff check tests/ 2>&1 | tail -1 >> team2-final-report.txt

echo "\nUnit Test Status:" >> team2-final-report.txt
uv run pytest tests/test_cli_config.py -v 2>&1 | tail -5 >> team2-final-report.txt

echo "\nDeprecation Warnings:" >> team2-final-report.txt
echo "$(uv run pytest tests/unit/ -q --tb=no 2>&1 | grep -c 'PydanticDeprecatedSince20') warnings (expected: 0)" >> team2-final-report.txt

echo "\nCollection Warnings:" >> team2-final-report.txt
echo "$(uv run pytest tests/unit/ --collect-only 2>&1 | grep -c 'PytestCollectionWarning') warnings (expected: 0)" >> team2-final-report.txt

cat team2-final-report.txt
```

## Deliverables Checklist

- [ ] All 36 manual ruff errors fixed
  - [ ] PTH123: 1 fix
  - [ ] SIM105: 2 fixes
  - [ ] SIM117: 5 fixes
  - [ ] RET504: 1 fix
  - [ ] F841: 27 fixes
- [ ] All 5 unit test failures resolved in test_cli_config.py
- [ ] 4 Pydantic deprecation warnings fixed
- [ ] 2 pytest collection warnings fixed
- [ ] `uv run ruff check tests/` returns 0 errors
- [ ] All unit tests passing
- [ ] All changes committed to `fix/test-quality-errors` branch
- [ ] Commit messages follow conventional commits format
- [ ] Final report generated (team2-final-report.txt)
- [ ] Ready for merge coordination with Team 1

## Communication Protocol

### Progress Updates (Every 30 minutes)

```bash
echo "\n=== CHECKPOINT $(date) ===" >> team2-progress.log
echo "Ruff errors remaining: $(uv run ruff check tests/ 2>&1 | grep -c 'error' || echo 0)" >> team2-progress.log
echo "Test failures remaining: $(uv run pytest tests/test_cli_config.py -q 2>&1 | grep -c 'FAILED' || echo 0)" >> team2-progress.log
echo "Commits: $(git log --oneline feat/phase2-smart-onboarding-unified..HEAD | wc -l)" >> team2-progress.log
```

### Blocker Reporting

If blocked:

1. Document in `team2-blockers.txt`
1. Note which task is blocked
1. Continue with other tasks
1. Report to coordinator

### Completion Signal

```bash
echo "TEAM 2 COMPLETE - $(date)" > TEAM2_COMPLETE.marker
echo "Manual ruff errors fixed: 36/36" >> TEAM2_COMPLETE.marker
echo "Unit test failures fixed: 5/5" >> TEAM2_COMPLETE.marker
echo "Deprecation warnings fixed: 4/4" >> TEAM2_COMPLETE.marker
echo "Collection warnings fixed: 2/2" >> TEAM2_COMPLETE.marker
echo "Branch: fix/test-quality-errors" >> TEAM2_COMPLETE.marker
echo "Ready for merge: YES" >> TEAM2_COMPLETE.marker

cat TEAM2_COMPLETE.marker
```

## Success Criteria

ALL must be true:

- [ ] `uv run ruff check tests/` → Found 0 errors
- [ ] `uv run pytest tests/test_cli_config.py -v` → 5/5 tests passed
- [ ] No PydanticDeprecatedSince20 warnings
- [ ] No PytestCollectionWarning warnings
- [ ] All unit tests passing with no failures
- [ ] Git history clean with meaningful commits
- [ ] No changes to Team 1's territory
- [ ] Branch `fix/test-quality-errors` up to date
- [ ] Final report generated and validated

## Time Estimates by Task

- Task 1 (Manual Ruff): 45 minutes
- Task 2 (Test Failures): 30 minutes
- Task 3 (Pydantic Warnings): 20 minutes
- Task 4 (Pytest Warnings): 15 minutes
- Final Validation: 15 minutes
- Buffer: 30 minutes

**Total**: 2 hours 35 minutes

______________________________________________________________________

**START NOW**: Execute the Setup Commands section and begin with Task 1!
