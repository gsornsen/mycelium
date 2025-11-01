# M06: Coordination Testing

## Overview

**Duration**: 3 days **Dependencies**: M05 (deployment generation), M02 (configuration), M03 (service detection)
**Blocks**: M07, M08, M09, M10 (all Phase 3 milestones) **Lead Agent**: multi-agent-coordinator **Support Agents**:
test-automator, python-pro, ai-engineer

## Why This Milestone

Coordination testing validates that multi-agent infrastructure works correctly under real-world conditions. Unlike unit
tests that isolate components, functional coordination tests verify complete patterns (pub/sub, task queues, barriers)
across actual or mock MCP servers. This milestone ensures reliability before production use and establishes patterns for
future test development.

Well-designed coordination tests:

- Validate complete communication flows
- Test failure scenarios and recovery
- Measure performance and latency
- Support both development (mock) and CI/CD (real) modes
- Provide clear metrics and error reporting
- Catch integration issues early

## Requirements

### Functional Requirements (FR)

- **FR-6.1**: Test orchestrator using asyncio TaskGroup for parallel test execution
- **FR-6.2**: Functional tests for all coordination patterns (pub/sub, task queue, request-reply, scatter-gather,
  barrier, circuit breaker)
- **FR-6.3**: Support both mock and real MCP server modes
- **FR-6.4**: Failure injection for testing error handling and recovery
- **FR-6.5**: Metrics collection (latency, throughput, success rate)
- **FR-6.6**: Clear test reports with pass/fail status and diagnostic info

### Technical Requirements (TR)

- **TR-6.1**: Use pytest-asyncio for async test execution
- **TR-6.2**: Implement test fixtures for MCP client setup/teardown
- **TR-6.3**: Support parametrized tests for multiple scenarios
- **TR-6.4**: Use deterministic test data (seeded random values)
- **TR-6.5**: Timeout protection (tests must complete within bounds)

### Integration Requirements (IR)

- **IR-6.1**: Integrate with M02 configuration for test settings
- **IR-6.2**: Use M05 deployment files to start test infrastructure
- **IR-6.3**: Connect to Redis, TaskQueue, Temporal MCP servers
- **IR-6.4**: Integrate as `/mycelium-test` slash command

### Compliance Requirements (CR)

- **CR-6.1**: Tests must be deterministic and repeatable
- **CR-6.2**: No test data pollution between runs
- **CR-6.3**: Clear separation between unit, integration, and functional tests
- **CR-6.4**: Comprehensive logging for debugging failures

## Tasks

### Task 6.1: Design Test Orchestrator Architecture

**Agent**: multi-agent-coordinator (lead), test-automator (support) **Effort**: 4 hours

**Description**: Design test orchestrator that manages parallel test execution, resource lifecycle, metrics collection,
and result aggregation using asyncio TaskGroup.

**Implementation**:

```python
# mycelium_testing/orchestrator.py
"""Test orchestration framework for coordination patterns."""

import asyncio
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)

class TestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TestResult:
    """Result of a single test execution."""
    test_name: str
    status: TestStatus
    duration_ms: float
    error: Optional[str] = None
    metrics: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)

@dataclass
class TestSuite:
    """Collection of coordination tests."""
    name: str
    tests: list[Callable]
    setup: Optional[Callable] = None
    teardown: Optional[Callable] = None

class TestOrchestrator:
    """
    Orchestrates parallel test execution with resource management.

    Features:
    - Parallel test execution using asyncio TaskGroup
    - Per-test timeout protection
    - Resource cleanup on failure
    - Metrics aggregation
    - Deterministic seeding
    """

    def __init__(
        self,
        parallel_limit: int = 5,
        default_timeout: float = 30.0,
        seed: int = 42,
    ):
        self.parallel_limit = parallel_limit
        self.default_timeout = default_timeout
        self.seed = seed
        self.results: list[TestResult] = []

    async def run_suite(
        self,
        suite: TestSuite,
        fail_fast: bool = False,
    ) -> list[TestResult]:
        """
        Execute test suite with setup/teardown.

        Args:
            suite: Test suite to execute
            fail_fast: Stop on first failure

        Returns:
            List of test results
        """
        logger.info(f"Running test suite: {suite.name}")

        # Setup
        if suite.setup:
            try:
                await suite.setup()
            except Exception as e:
                logger.error(f"Suite setup failed: {e}")
                return [TestResult(
                    test_name=f"{suite.name}::setup",
                    status=TestStatus.FAILED,
                    duration_ms=0,
                    error=str(e),
                )]

        # Run tests in parallel with limit
        try:
            async with asyncio.TaskGroup() as tg:
                semaphore = asyncio.Semaphore(self.parallel_limit)

                for test_func in suite.tests:
                    if fail_fast and any(r.status == TestStatus.FAILED for r in self.results):
                        break

                    tg.create_task(
                        self._run_single_test(test_func, semaphore)
                    )
        except Exception as e:
            logger.error(f"Test execution failed: {e}")

        # Teardown
        if suite.teardown:
            try:
                await suite.teardown()
            except Exception as e:
                logger.error(f"Suite teardown failed: {e}")

        return self.results

    async def _run_single_test(
        self,
        test_func: Callable,
        semaphore: asyncio.Semaphore,
    ) -> TestResult:
        """Execute single test with timeout and error handling."""
        test_name = test_func.__name__

        async with semaphore:
            logger.info(f"Starting test: {test_name}")
            start_time = time.perf_counter()

            try:
                # Run test with timeout
                async with asyncio.timeout(self.default_timeout):
                    result = await test_func()

                duration_ms = (time.perf_counter() - start_time) * 1000

                test_result = TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    duration_ms=duration_ms,
                    metrics=result.get('metrics', {}) if isinstance(result, dict) else {},
                )

                logger.info(f"✓ {test_name} passed ({duration_ms:.2f}ms)")

            except asyncio.TimeoutError:
                duration_ms = (time.perf_counter() - start_time) * 1000
                test_result = TestResult(
                    test_name=test_name,
                    status=TestStatus.FAILED,
                    duration_ms=duration_ms,
                    error=f"Test timeout after {self.default_timeout}s",
                )
                logger.error(f"✗ {test_name} timeout")

            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                test_result = TestResult(
                    test_name=test_name,
                    status=TestStatus.FAILED,
                    duration_ms=duration_ms,
                    error=str(e),
                )
                logger.error(f"✗ {test_name} failed: {e}")

            self.results.append(test_result)
            return test_result

    def generate_report(self) -> str:
        """Generate human-readable test report."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)

        lines = [
            "=" * 60,
            "COORDINATION TEST REPORT",
            "=" * 60,
            f"Total Tests: {total}",
            f"Passed: {passed}",
            f"Failed: {failed}",
            f"Success Rate: {(passed/total*100) if total > 0 else 0:.1f}%",
            "",
            "Test Details:",
            "-" * 60,
        ]

        for result in self.results:
            status_icon = "✓" if result.status == TestStatus.PASSED else "✗"
            lines.append(
                f"{status_icon} {result.test_name}: {result.status.value} "
                f"({result.duration_ms:.2f}ms)"
            )
            if result.error:
                lines.append(f"   Error: {result.error}")

        lines.append("=" * 60)
        return "\n".join(lines)
```

**Acceptance Criteria**:

- [ ] Orchestrator runs tests in parallel with configurable limit
- [ ] Per-test timeout protection implemented
- [ ] Metrics collection and aggregation working
- [ ] Report generation produces readable output
- [ ] Architecture reviewed by multi-agent-coordinator

### Task 6.2: Implement MCP Client Fixtures

**Agent**: python-pro, test-automator **Effort**: 4 hours

**Description**: Create pytest fixtures for MCP client lifecycle management, supporting both mock and real server modes
with environment variable control.

**Implementation**:

```python
# tests/fixtures/mcp_clients.py
"""Pytest fixtures for MCP client management."""

import pytest
import asyncio
import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock

# Real MCP client imports
try:
    from mcp_redis import RedisClient
    from mcp_taskqueue import TaskQueueClient
    from mcp_temporal import TemporalClient
    HAS_REAL_MCP = True
except ImportError:
    HAS_REAL_MCP = False

USE_MOCK_MCP = os.getenv('USE_MOCK_MCP', 'false').lower() == 'true'

@pytest.fixture
async def redis_client() -> AsyncGenerator:
    """
    Provide Redis MCP client (mock or real based on environment).

    Set USE_MOCK_MCP=true to use mocks during development.
    """
    if USE_MOCK_MCP or not HAS_REAL_MCP:
        # Mock Redis client for development
        mock_client = AsyncMock()
        mock_client.publish = AsyncMock(return_value=1)
        mock_client.subscribe = AsyncMock()
        mock_client.get = AsyncMock(return_value=None)
        mock_client.set = AsyncMock(return_value=True)

        yield mock_client
    else:
        # Real Redis client for CI/CD
        client = RedisClient(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
        )

        await client.connect()

        try:
            yield client
        finally:
            await client.disconnect()

@pytest.fixture
async def taskqueue_client() -> AsyncGenerator:
    """
    Provide TaskQueue MCP client (mock or real based on environment).
    """
    if USE_MOCK_MCP or not HAS_REAL_MCP:
        # Mock TaskQueue client
        mock_client = AsyncMock()
        mock_client.create_project = AsyncMock(return_value={'project_id': 'proj-test-1'})
        mock_client.add_task = AsyncMock(return_value={'task_id': 'task-test-1'})
        mock_client.get_next_task = AsyncMock(return_value=None)

        yield mock_client
    else:
        # Real TaskQueue client
        client = TaskQueueClient()

        await client.connect()

        try:
            yield client
        finally:
            await client.disconnect()

@pytest.fixture
async def temporal_client() -> AsyncGenerator:
    """
    Provide Temporal MCP client (mock or real based on environment).
    """
    if USE_MOCK_MCP or not HAS_REAL_MCP:
        # Mock Temporal client
        mock_client = AsyncMock()
        mock_client.start_workflow = AsyncMock(return_value={'workflow_id': 'wf-test-1'})
        mock_client.get_workflow_status = AsyncMock(return_value={'status': 'COMPLETED'})

        yield mock_client
    else:
        # Real Temporal client
        client = TemporalClient(
            host=os.getenv('TEMPORAL_HOST', 'localhost'),
            port=int(os.getenv('TEMPORAL_PORT', 7233)),
        )

        await client.connect()

        try:
            yield client
        finally:
            await client.disconnect()

@pytest.fixture
async def mcp_clients(
    redis_client,
    taskqueue_client,
    temporal_client,
) -> dict:
    """Provide all MCP clients as dictionary."""
    return {
        'redis': redis_client,
        'taskqueue': taskqueue_client,
        'temporal': temporal_client,
    }

@pytest.fixture(autouse=True)
async def cleanup_test_data(mcp_clients):
    """Automatically cleanup test data after each test."""
    yield

    # Cleanup Redis test keys
    if not USE_MOCK_MCP and HAS_REAL_MCP:
        redis = mcp_clients['redis']
        test_keys = await redis.keys('test:*')
        if test_keys:
            await redis.delete(*test_keys)
```

**Acceptance Criteria**:

- [ ] Fixtures support both mock and real MCP clients
- [ ] Environment variable controls mock/real mode
- [ ] Automatic cleanup after each test
- [ ] Connection lifecycle managed correctly

### Task 6.3: Create Functional Coordination Tests

**Agent**: multi-agent-coordinator (lead), test-automator, ai-engineer **Effort**: 10 hours

**Description**: Implement functional tests for all coordination patterns using pytest-asyncio, validating complete
message flows and agent interactions.

**Implementation**:

```python
# tests/functional/test_coordination_patterns.py
"""Functional tests for coordination patterns."""

import pytest
import asyncio
from typing import Any

pytestmark = pytest.mark.asyncio

# ==================== PUB/SUB PATTERN ====================

async def test_pubsub_basic_message_delivery(redis_client):
    """Test basic pub/sub message delivery."""
    channel = "test:coordination:pubsub"
    message = "Hello from agent-1"

    # Subscribe to channel
    pubsub = await redis_client.subscribe(channel)

    # Publish message
    await redis_client.publish(channel, message)

    # Receive message
    received = await asyncio.wait_for(pubsub.get_message(), timeout=5.0)

    assert received is not None
    assert received['data'] == message

async def test_pubsub_multiple_subscribers(redis_client):
    """Test pub/sub with multiple subscribers."""
    channel = "test:coordination:multi_sub"
    message = "Broadcast message"

    # Create 3 subscribers
    subscribers = [
        await redis_client.subscribe(channel)
        for _ in range(3)
    ]

    # Publish once
    await redis_client.publish(channel, message)

    # All subscribers should receive
    for sub in subscribers:
        received = await asyncio.wait_for(sub.get_message(), timeout=5.0)
        assert received['data'] == message

# ==================== TASK QUEUE PATTERN ====================

async def test_task_queue_distribution(taskqueue_client):
    """Test task distribution across agents."""
    # Create project
    project = await taskqueue_client.create_project(
        name="test-project",
        description="Coordination test"
    )
    project_id = project['project_id']

    # Add 5 tasks
    tasks = []
    for i in range(5):
        task = await taskqueue_client.add_task(
            project_id=project_id,
            title=f"Task {i}",
            description=f"Test task {i}"
        )
        tasks.append(task)

    # Simulate 3 agents retrieving tasks
    retrieved = []
    for agent_id in range(3):
        task = await taskqueue_client.get_next_task(project_id)
        if task:
            retrieved.append(task)
            await taskqueue_client.update_task(
                project_id=project_id,
                task_id=task['task_id'],
                status='in_progress'
            )

    # Should retrieve 3 tasks (one per agent)
    assert len(retrieved) == 3

    # All should be different tasks
    task_ids = {t['task_id'] for t in retrieved}
    assert len(task_ids) == 3

async def test_task_queue_completion_flow(taskqueue_client):
    """Test complete task lifecycle."""
    project = await taskqueue_client.create_project(name="test-completion")
    project_id = project['project_id']

    # Add task
    task = await taskqueue_client.add_task(
        project_id=project_id,
        title="Complete me",
        description="Test completion"
    )
    task_id = task['task_id']

    # Get task
    retrieved = await taskqueue_client.get_next_task(project_id)
    assert retrieved['task_id'] == task_id
    assert retrieved['status'] == 'pending'

    # Mark in progress
    await taskqueue_client.update_task(
        project_id=project_id,
        task_id=task_id,
        status='in_progress'
    )

    # Complete task
    await taskqueue_client.update_task(
        project_id=project_id,
        task_id=task_id,
        status='done',
        completed_details='Task finished successfully'
    )

    # Verify status
    task_status = await taskqueue_client.get_task(project_id, task_id)
    assert task_status['status'] == 'done'

# ==================== REQUEST-REPLY PATTERN ====================

async def test_request_reply_pattern(redis_client):
    """Test request-reply coordination."""
    request_channel = "test:requests"
    reply_channel = "test:replies"

    # Subscriber (responder)
    async def responder():
        pubsub = await redis_client.subscribe(request_channel)
        msg = await pubsub.get_message()
        request_id = msg['data']

        # Send reply
        await redis_client.publish(reply_channel, f"reply-{request_id}")

    # Start responder
    responder_task = asyncio.create_task(responder())

    # Requester
    request_id = "req-12345"
    reply_sub = await redis_client.subscribe(reply_channel)

    # Send request
    await redis_client.publish(request_channel, request_id)

    # Wait for reply
    reply = await asyncio.wait_for(reply_sub.get_message(), timeout=5.0)

    assert reply['data'] == f"reply-{request_id}"
    await responder_task

# ==================== SCATTER-GATHER PATTERN ====================

async def test_scatter_gather_pattern(redis_client):
    """Test scatter-gather coordination."""
    scatter_channel = "test:scatter"
    gather_channel = "test:gather"

    num_workers = 5

    # Workers (process and reply)
    async def worker(worker_id: int):
        pubsub = await redis_client.subscribe(scatter_channel)
        msg = await pubsub.get_message()
        task_id = msg['data']

        # Simulate work
        await asyncio.sleep(0.1)

        # Send result
        await redis_client.publish(gather_channel, f"result-{worker_id}-{task_id}")

    # Start workers
    worker_tasks = [asyncio.create_task(worker(i)) for i in range(num_workers)]

    # Coordinator
    gather_sub = await redis_client.subscribe(gather_channel)

    # Scatter task
    task_id = "task-xyz"
    await redis_client.publish(scatter_channel, task_id)

    # Gather results
    results = []
    for _ in range(num_workers):
        result = await asyncio.wait_for(gather_sub.get_message(), timeout=10.0)
        results.append(result['data'])

    # Verify all workers responded
    assert len(results) == num_workers
    assert all(task_id in r for r in results)

    await asyncio.gather(*worker_tasks)

# ==================== BARRIER SYNCHRONIZATION ====================

async def test_barrier_synchronization(redis_client):
    """Test barrier synchronization pattern."""
    barrier_key = "test:barrier:sync"
    num_agents = 4

    # Agents wait at barrier
    async def agent(agent_id: int):
        # Increment barrier counter
        count = await redis_client.incr(barrier_key)

        # Wait until all agents reach barrier
        while True:
            current = await redis_client.get(barrier_key)
            if int(current) >= num_agents:
                break
            await asyncio.sleep(0.05)

        return agent_id

    # Run all agents
    results = await asyncio.gather(*[agent(i) for i in range(num_agents)])

    # All agents should complete
    assert len(results) == num_agents
    assert set(results) == set(range(num_agents))

# ==================== CIRCUIT BREAKER PATTERN ====================

async def test_circuit_breaker_pattern(redis_client):
    """Test circuit breaker for fault tolerance."""
    service_key = "test:circuit_breaker:failures"
    threshold = 3

    # Simulate service failures
    for _ in range(threshold):
        await redis_client.incr(service_key)

    failure_count = int(await redis_client.get(service_key))

    # Circuit should be open (too many failures)
    assert failure_count >= threshold

    # Reset after timeout
    await redis_client.delete(service_key)
    failure_count = await redis_client.get(service_key)

    # Circuit should be closed
    assert failure_count is None or int(failure_count) == 0
```

**Test Plan**: Complete test matrix covering:

- [x] Pub/sub: basic delivery, multiple subscribers, pattern matching
- [x] Task queue: distribution, completion flow, priority handling
- [x] Request-reply: synchronous communication
- [x] Scatter-gather: parallel processing and aggregation
- [x] Barrier synchronization: agent coordination points
- [x] Circuit breaker: fault tolerance

**Acceptance Criteria**:

- [ ] All 6 coordination patterns tested
- [ ] Tests pass with both mock and real MCP servers
- [ ] Each test is deterministic and repeatable
- [ ] Error messages are clear and actionable

### Task 6.4: Add Failure Injection and Metrics

**Agent**: multi-agent-coordinator, ai-engineer **Effort**: 4 hours

**Description**: Implement failure injection (network delays, timeouts, errors) and metrics collection (latency,
throughput) to validate resilience.

**Implementation**:

```python
# mycelium_testing/failure_injection.py
"""Failure injection for coordination testing."""

import asyncio
import random
from typing import Callable, Any
from functools import wraps

class FailureInjector:
    """Inject failures into coordination operations."""

    def __init__(self, seed: int = 42):
        self.random = random.Random(seed)

    def inject_delay(
        self,
        min_ms: float = 10,
        max_ms: float = 100,
        probability: float = 0.3,
    ):
        """
        Decorator to inject random delays.

        Args:
            min_ms: Minimum delay in milliseconds
            max_ms: Maximum delay in milliseconds
            probability: Probability of delay injection (0-1)
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if self.random.random() < probability:
                    delay_ms = self.random.uniform(min_ms, max_ms)
                    await asyncio.sleep(delay_ms / 1000)

                return await func(*args, **kwargs)

            return wrapper
        return decorator

    def inject_timeout(
        self,
        probability: float = 0.1,
    ):
        """Inject timeout errors."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if self.random.random() < probability:
                    raise asyncio.TimeoutError("Injected timeout")

                return await func(*args, **kwargs)

            return wrapper
        return decorator

    def inject_error(
        self,
        error_type: type = Exception,
        probability: float = 0.05,
        message: str = "Injected error",
    ):
        """Inject arbitrary errors."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if self.random.random() < probability:
                    raise error_type(message)

                return await func(*args, **kwargs)

            return wrapper
        return decorator

# mycelium_testing/metrics.py
"""Metrics collection for coordination tests."""

import time
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

@dataclass
class MetricsCollector:
    """Collect and aggregate test metrics."""

    latencies: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    throughput: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def record_latency(self, operation: str, latency_ms: float) -> None:
        """Record operation latency."""
        self.latencies[operation].append(latency_ms)

    def record_throughput(self, operation: str, count: int = 1) -> None:
        """Record successful operations."""
        self.throughput[operation] += count

    def record_error(self, operation: str, count: int = 1) -> None:
        """Record errors."""
        self.errors[operation] += count

    def get_stats(self, operation: str) -> dict:
        """Get statistics for operation."""
        latencies = self.latencies.get(operation, [])

        if not latencies:
            return {}

        return {
            'count': len(latencies),
            'min_ms': min(latencies),
            'max_ms': max(latencies),
            'avg_ms': sum(latencies) / len(latencies),
            'p50_ms': self._percentile(latencies, 0.5),
            'p95_ms': self._percentile(latencies, 0.95),
            'p99_ms': self._percentile(latencies, 0.99),
            'throughput': self.throughput.get(operation, 0),
            'errors': self.errors.get(operation, 0),
        }

    @staticmethod
    def _percentile(data: list[float], percentile: float) -> float:
        """Calculate percentile."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def generate_report(self) -> str:
        """Generate metrics report."""
        lines = ["METRICS REPORT", "=" * 60]

        for operation in sorted(self.latencies.keys()):
            stats = self.get_stats(operation)
            lines.extend([
                f"\n{operation}:",
                f"  Count: {stats['count']}",
                f"  Latency (ms): min={stats['min_ms']:.2f}, avg={stats['avg_ms']:.2f}, max={stats['max_ms']:.2f}",
                f"  Percentiles (ms): p50={stats['p50_ms']:.2f}, p95={stats['p95_ms']:.2f}, p99={stats['p99_ms']:.2f}",
                f"  Throughput: {stats['throughput']} ops",
                f"  Errors: {stats['errors']}",
            ])

        return "\n".join(lines)
```

**Usage in Tests**:

```python
# tests/functional/test_with_failures.py
"""Tests with failure injection."""

import pytest
from mycelium_testing.failure_injection import FailureInjector
from mycelium_testing.metrics import MetricsCollector

pytestmark = pytest.mark.asyncio

@pytest.fixture
def failure_injector():
    return FailureInjector(seed=42)

@pytest.fixture
def metrics():
    return MetricsCollector()

async def test_pubsub_with_network_delays(redis_client, failure_injector, metrics):
    """Test pub/sub resilience to network delays."""
    channel = "test:delays"

    # Wrap publish with delay injection
    original_publish = redis_client.publish
    redis_client.publish = failure_injector.inject_delay(
        min_ms=50,
        max_ms=200,
        probability=0.5,
    )(original_publish)

    # Measure latency
    import time
    for i in range(10):
        start = time.perf_counter()
        await redis_client.publish(channel, f"msg-{i}")
        latency_ms = (time.perf_counter() - start) * 1000

        metrics.record_latency("publish", latency_ms)
        metrics.record_throughput("publish")

    # Verify metrics
    stats = metrics.get_stats("publish")
    assert stats['count'] == 10
    assert stats['avg_ms'] > 0  # Some operations were delayed
```

**Acceptance Criteria**:

- [ ] Failure injection decorators implemented
- [ ] Metrics collector tracks latency, throughput, errors
- [ ] Tests validate resilience under failures
- [ ] Metrics reports are human-readable

### Task 6.5: Create /mycelium-test Command

**Agent**: claude-code-developer, multi-agent-coordinator **Effort**: 3 hours

**Description**: Integrate test framework as `/mycelium-test` command with options for test selection, verbosity, and
reporting.

**Implementation**:

```markdown
# ~/.claude/plugins/mycelium-core/commands/mycelium-test.md

# Mycelium Test

Run coordination pattern tests to validate infrastructure.

## Usage

```

/mycelium-test \[--pattern PATTERN\] \[--mock\] \[--verbose\] \[--report\]

````

## Options

- `--pattern`: Test pattern to run ('pubsub', 'taskqueue', 'all')
- `--mock`: Use mock MCP servers (for development)
- `--verbose`: Show detailed test output
- `--report`: Generate metrics report
- `--fail-fast`: Stop on first failure

## Examples

```bash
# Run all tests with real MCP servers
/mycelium-test

# Run only pub/sub tests
/mycelium-test --pattern pubsub

# Use mocks for development
/mycelium-test --mock

# Verbose output with metrics
/mycelium-test --verbose --report
````

## Test Patterns

- **pubsub**: Pub/sub messaging tests
- **taskqueue**: Task distribution tests
- **request-reply**: Synchronous coordination
- **scatter-gather**: Parallel processing
- **barrier**: Agent synchronization
- **circuit-breaker**: Fault tolerance
- **all**: Run all patterns (default)

## Prerequisites

- Configuration complete (`/mycelium-configuration`)
- Services running (`docker-compose up` or `just up`)
- MCP servers accessible

## Troubleshooting

### Tests Fail to Connect

```bash
# Check services are running
docker-compose ps
just status

# Use mock mode
/mycelium-test --mock
```

### Timeout Errors

```bash
# Increase timeout (in config)
/mycelium-configuration edit

# Run single pattern
/mycelium-test --pattern pubsub
```

````

```python
# mycelium_onboarding/cli/test.py
"""CLI command for coordination testing."""

import click
import asyncio
import os
from rich.console import Console

from mycelium_testing.orchestrator import TestOrchestrator, TestSuite
from tests.functional import test_coordination_patterns

console = Console()

@click.command()
@click.option(
    '--pattern',
    type=click.Choice(['pubsub', 'taskqueue', 'request-reply', 'scatter-gather', 'barrier', 'circuit-breaker', 'all']),
    default='all',
    help='Test pattern to run'
)
@click.option('--mock', is_flag=True, help='Use mock MCP servers')
@click.option('--verbose', is_flag=True, help='Verbose output')
@click.option('--report', is_flag=True, help='Generate metrics report')
@click.option('--fail-fast', is_flag=True, help='Stop on first failure')
def test(pattern: str, mock: bool, verbose: bool, report: bool, fail_fast: bool):
    """Run coordination pattern tests."""

    # Set mock mode
    if mock:
        os.environ['USE_MOCK_MCP'] = 'true'

    console.print(f"[cyan]Running {pattern} tests...[/cyan]\n")

    # Create test suite
    suite = TestSuite(
        name=f"coordination-{pattern}",
        tests=_get_tests_for_pattern(pattern),
    )

    # Run tests
    orchestrator = TestOrchestrator()
    results = asyncio.run(orchestrator.run_suite(suite, fail_fast=fail_fast))

    # Show report
    console.print(orchestrator.generate_report())

    if report:
        # Generate metrics report if requested
        console.print("\n" + metrics.generate_report())

    # Exit with appropriate code
    failed = sum(1 for r in results if r.status == 'failed')
    if failed > 0:
        raise click.ClickException(f"{failed} tests failed")

def _get_tests_for_pattern(pattern: str) -> list:
    """Get test functions for pattern."""
    # Import test module and filter by pattern
    import tests.functional.test_coordination_patterns as tests_module

    if pattern == 'all':
        return [
            getattr(tests_module, name)
            for name in dir(tests_module)
            if name.startswith('test_')
        ]
    else:
        pattern_prefix = f"test_{pattern.replace('-', '_')}"
        return [
            getattr(tests_module, name)
            for name in dir(tests_module)
            if name.startswith(pattern_prefix)
        ]

if __name__ == '__main__':
    test()
````

**Acceptance Criteria**:

- [ ] Command runs all or selected test patterns
- [ ] Mock mode works for development
- [ ] Reports show pass/fail status clearly
- [ ] Metrics report generated when requested

## Exit Criteria

- [ ] Test orchestrator implemented with asyncio TaskGroup
- [ ] All 6 coordination patterns tested
- [ ] Tests work with both mock and real MCP servers
- [ ] Failure injection validates resilience
- [ ] Metrics collection tracks performance
- [ ] `/mycelium-test` command functional
- [ ] ≥90% test coverage for coordination patterns
- [ ] Documentation includes test examples
- [ ] Code reviewed by multi-agent-coordinator + test-automator
- [ ] CI/CD pipeline integration tested

## Deliverables

1. **Test Framework**:

   - `mycelium_testing/orchestrator.py`
   - `mycelium_testing/failure_injection.py`
   - `mycelium_testing/metrics.py`

1. **Test Fixtures**:

   - `tests/fixtures/mcp_clients.py`

1. **Functional Tests**:

   - `tests/functional/test_coordination_patterns.py`
   - `tests/functional/test_with_failures.py`

1. **CLI Command**:

   - `mycelium_onboarding/cli/test.py`
   - `~/.claude/plugins/mycelium-core/commands/mycelium-test.md`

1. **Documentation**:

   - `docs/testing/coordination-tests.md`
   - `docs/testing/failure-scenarios.md`

## Risk Assessment

| Risk                                      | Probability | Impact | Mitigation                                            |
| ----------------------------------------- | ----------- | ------ | ----------------------------------------------------- |
| Flaky tests due to timing                 | Medium      | High   | Deterministic seeds, clear timeouts, retry logic      |
| MCP server connection failures            | Medium      | High   | Mock mode for development, health checks before tests |
| Test data pollution                       | Low         | Medium | Automatic cleanup fixtures, isolated namespaces       |
| Performance bottlenecks in parallel tests | Low         | Medium | Configurable parallelism limit, resource monitoring   |

## Dependencies for Next Milestones

**M07, M08, M09** (Phase 3 parallel work) require:

- Working coordination tests as validation
- Test patterns for documentation examples
- Metrics baseline for performance monitoring
- Test infrastructure for CI/CD (M09)

**M10 (Polish & Release)** requires:

- All coordination tests passing
- Performance metrics meeting targets
- Test suite as quality gate

______________________________________________________________________

**Milestone Owner**: multi-agent-coordinator **Reviewers**: test-automator, python-pro **Status**: Ready for
Implementation **Created**: 2025-10-13 **Target Completion**: Day 16 (3 days after M05)
