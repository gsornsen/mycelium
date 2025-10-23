# Source: projects/onboarding/milestones/M06_COORDINATION_TESTING.md
# Line: 67
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_testing/orchestrator.py
"""Test orchestration framework for coordination patterns."""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

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
    error: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)

@dataclass
class TestSuite:
    """Collection of coordination tests."""
    name: str
    tests: list[Callable]
    setup: Callable | None = None
    teardown: Callable | None = None

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
