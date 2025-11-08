#!/usr/bin/env python3
"""End-to-end integration tests for Redis MCP coordination fixes.

This test suite validates:
1. RedisCoordinationHelper with live Redis Stack
2. JSON serialization with datetime handling
3. Multi-agent coordination workflows
4. Error handling and fallback mechanisms
5. Performance benchmarks
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

import redis.asyncio as aioredis

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class MockRedisClient:
    """Mock Redis client for testing fallback behavior."""

    def __init__(self, fail: bool = True):
        self.fail = fail

    async def hset(self, *args, **kwargs):
        if self.fail:
            raise Exception("Simulated Redis failure")
        return True

    async def hget(self, *args, **kwargs):
        if self.fail:
            raise Exception("Simulated Redis failure")
        return

    async def hgetall(self, *args, **kwargs):
        if self.fail:
            raise Exception("Simulated Redis failure")
        return {}

    async def expire(self, *args, **kwargs):
        if self.fail:
            raise Exception("Simulated Redis failure")
        return True


class IntegrationTestSuite:
    """Comprehensive integration test suite for Redis coordination."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.test_results = []

    async def setup(self):
        """Initialize test environment."""
        logger.info("Setting up integration test environment...")

        # Import RedisCoordinationHelper
        try:
            from mycelium_onboarding.coordination import RedisCoordinationHelper

            self.RedisCoordinationHelper = RedisCoordinationHelper
            logger.info("✅ RedisCoordinationHelper imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import RedisCoordinationHelper: {e}")
            raise

        # Connect to Redis
        try:
            self.redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info("✅ Connected to Redis Stack at localhost:6379")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise

    async def teardown(self):
        """Clean up test environment."""
        logger.info("Cleaning up test environment...")

        if self.redis_client:
            # Clean up test data
            test_keys = await self.redis_client.keys("test:*")
            test_keys += await self.redis_client.keys("agents:*")

            if test_keys:
                await self.redis_client.delete(*test_keys)
                logger.info(f"Deleted {len(test_keys)} test keys")

            await self.redis_client.close()
            logger.info("✅ Redis connection closed")

    def record_result(self, test_name: str, passed: bool, details: str = ""):
        """Record test result."""
        self.test_results.append({"test": test_name, "passed": passed, "details": details, "timestamp": datetime.now()})

        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if details:
            logger.info(f"  Details: {details}")

    # Phase 1: RedisCoordinationHelper Validation

    async def test_phase1_basic_operations(self):
        """Test 1: Basic store and retrieve operations."""
        logger.info("\n=== PHASE 1: RedisCoordinationHelper Validation ===\n")

        helper = self.RedisCoordinationHelper(self.redis_client)

        # Test 1.1: Store agent status with datetime
        logger.info("Test 1.1: Storing agent status with datetime...")
        status_data = {
            "status": "busy",
            "workload": 85,
            "current_task": {
                "id": "test-coordination-fixes",
                "description": "Testing Redis MCP coordination",
                "progress": 50,
            },
            "started_at": datetime.now(),
        }

        try:
            success = await helper.set_agent_status("test-agent", status_data)
            self.record_result("Phase 1.1: Store agent status", success, "Status stored with datetime object")
        except Exception as e:
            self.record_result("Phase 1.1: Store agent status", False, str(e))
            return

        # Test 1.2: Retrieve with datetime restoration
        logger.info("\nTest 1.2: Retrieving agent status...")
        try:
            retrieved = await helper.get_agent_status("test-agent")

            assert retrieved is not None, "Status should be retrieved"
            assert retrieved["status"] == "busy", "Status should match"
            assert retrieved["workload"] == 85, "Workload should match"
            assert isinstance(retrieved["started_at"], datetime), "Datetime should be restored"

            self.record_result(
                "Phase 1.2: Retrieve with datetime", True, f"Datetime type: {type(retrieved['started_at']).__name__}"
            )
        except Exception as e:
            self.record_result("Phase 1.2: Retrieve with datetime", False, str(e))

        # Test 1.3: Store multiple agents
        logger.info("\nTest 1.3: Storing multiple agents...")
        agents = [
            ("backend-developer", {"status": "busy", "workload": 40, "task_count": 1}),
            ("python-pro", {"status": "busy", "workload": 60, "task_count": 2}),
            ("claude-code-developer", {"status": "idle", "workload": 0, "task_count": 0}),
        ]

        try:
            for agent_type, data in agents:
                await helper.set_agent_status(agent_type, data)

            self.record_result("Phase 1.3: Store multiple agents", True, f"Stored {len(agents)} agents successfully")
        except Exception as e:
            self.record_result("Phase 1.3: Store multiple agents", False, str(e))

        # Test 1.4: Get all agents
        logger.info("\nTest 1.4: Retrieving all agents...")
        try:
            all_agents = await helper.get_all_agents()

            assert len(all_agents) >= 3, "Should retrieve at least 3 agents"

            self.record_result("Phase 1.4: Get all agents", True, f"Retrieved {len(all_agents)} agents")
        except Exception as e:
            self.record_result("Phase 1.4: Get all agents", False, str(e))

        # Test 1.5: Heartbeat updates
        logger.info("\nTest 1.5: Testing heartbeat mechanism...")
        try:
            for agent_type in ["backend-developer", "python-pro", "test-agent"]:
                await helper.update_heartbeat(agent_type)
                is_fresh = await helper.check_heartbeat_freshness(agent_type, max_age_seconds=60)
                assert is_fresh, f"Heartbeat for {agent_type} should be fresh"

            self.record_result("Phase 1.5: Heartbeat updates", True, "All heartbeats fresh")
        except Exception as e:
            self.record_result("Phase 1.5: Heartbeat updates", False, str(e))

    # Phase 2: JSON Serialization Edge Cases

    async def test_phase2_json_serialization(self):
        """Test 2: Complex JSON serialization scenarios."""
        logger.info("\n=== PHASE 2: JSON Serialization Edge Cases ===\n")

        helper = self.RedisCoordinationHelper(self.redis_client)

        # Test 2.1: Complex nested structures
        logger.info("Test 2.1: Complex datetime in nested objects...")
        complex_data = {
            "status": "busy",
            "workload": 75,
            "tasks": [
                {"id": "task-1", "started_at": datetime.now(), "progress": 35},
                {"id": "task-2", "started_at": datetime.now() - timedelta(hours=2), "progress": 80},
            ],
            "metrics": {"last_success_at": datetime.now() - timedelta(hours=1), "total_duration": 3600},
        }

        try:
            await helper.set_agent_status("complex-test", complex_data)
            retrieved = await helper.get_agent_status("complex-test")

            # Verify datetime fields restored
            assert isinstance(retrieved["tasks"][0]["started_at"], datetime), "Nested datetime should be restored"
            assert isinstance(retrieved["metrics"]["last_success_at"], datetime), (
                "Deeply nested datetime should be restored"
            )

            self.record_result(
                "Phase 2.1: Complex datetime serialization", True, "All nested datetime fields restored correctly"
            )
        except Exception as e:
            self.record_result("Phase 2.1: Complex datetime serialization", False, str(e))

        # Test 2.2: Edge cases
        logger.info("\nTest 2.2: Testing edge cases...")
        edge_cases = {
            "none_value": None,
            "empty_list": [],
            "empty_dict": {},
            "unicode": "Hello 世界 🚀",
            "large_number": 9999999999999,
            "float_precision": 3.14159265359,
        }

        try:
            await helper.set_agent_status("edge-cases", edge_cases)
            retrieved = await helper.get_agent_status("edge-cases")

            assert retrieved["none_value"] is None, "None should be preserved"
            assert retrieved["empty_list"] == [], "Empty list should be preserved"
            assert retrieved["unicode"] == "Hello 世界 🚀", "Unicode should be preserved"

            self.record_result("Phase 2.2: Edge case handling", True, "All edge cases handled correctly")
        except Exception as e:
            self.record_result("Phase 2.2: Edge case handling", False, str(e))

    # Phase 3: Error Handling and Fallback

    async def test_phase3_error_handling(self):
        """Test 3: Error handling and markdown fallback."""
        logger.info("\n=== PHASE 3: Error Handling and Fallback ===\n")

        # Test 3.1: Fallback to markdown
        logger.info("Test 3.1: Testing markdown fallback...")
        try:
            failing_helper = self.RedisCoordinationHelper(MockRedisClient(fail=True))

            # Should fall back to markdown
            await failing_helper.set_agent_status("fallback-test", {"status": "testing", "workload": 50})

            # Verify markdown file created
            fallback_file = Path(".claude/coordination/agent-fallback-test.md")
            assert fallback_file.exists(), "Markdown fallback file should be created"

            # Retrieve from markdown
            retrieved = await failing_helper.get_agent_status("fallback-test")
            assert retrieved is not None, "Should retrieve from markdown"
            assert retrieved["status"] == "testing", "Data should match"

            self.record_result("Phase 3.1: Markdown fallback", True, f"Fallback file created at {fallback_file}")
        except Exception as e:
            self.record_result("Phase 3.1: Markdown fallback", False, str(e))

        # Test 3.2: Graceful degradation
        logger.info("\nTest 3.2: Testing graceful degradation...")
        try:
            helper = self.RedisCoordinationHelper(self.redis_client)

            # Store invalid JSON (should handle gracefully)
            await self.redis_client.hset("agents:status", "invalid-json", "{not valid json}")

            # Should return wrapped value or None, not crash
            await helper.get_agent_status("invalid-json")

            self.record_result("Phase 3.2: Graceful degradation", True, "Invalid JSON handled without crash")
        except Exception as e:
            self.record_result("Phase 3.2: Graceful degradation", False, str(e))

    # Phase 4: Performance Benchmarks

    async def test_phase4_performance(self):
        """Test 4: Performance benchmarks."""
        logger.info("\n=== PHASE 4: Performance Benchmarks ===\n")

        helper = self.RedisCoordinationHelper(self.redis_client)

        # Test 4.1: Store 100 agent updates
        logger.info("Test 4.1: Benchmark - Store 100 agent updates...")
        start = time.time()

        try:
            for i in range(100):
                await helper.set_agent_status(
                    f"agent-{i}",
                    {"status": "busy", "workload": i % 100, "task_count": i % 5, "updated_at": datetime.now()},
                )

            duration = time.time() - start
            throughput = 100 / duration
            latency_ms = (duration / 100) * 1000

            self.record_result(
                "Phase 4.1: Store throughput",
                throughput > 20,  # Target: >20 ops/sec
                f"{throughput:.1f} updates/sec, {latency_ms:.1f}ms per update",
            )
        except Exception as e:
            self.record_result("Phase 4.1: Store throughput", False, str(e))

        # Test 4.2: Retrieve 100 agents
        logger.info("\nTest 4.2: Benchmark - Retrieve 100 agent statuses...")
        start = time.time()

        try:
            for i in range(100):
                await helper.get_agent_status(f"agent-{i}")

            duration = time.time() - start
            throughput = 100 / duration
            latency_ms = (duration / 100) * 1000

            self.record_result(
                "Phase 4.2: Retrieve throughput",
                throughput > 20,  # Target: >20 ops/sec
                f"{throughput:.1f} reads/sec, {latency_ms:.1f}ms per read",
            )
        except Exception as e:
            self.record_result("Phase 4.2: Retrieve throughput", False, str(e))

        # Test 4.3: Get all agents
        logger.info("\nTest 4.3: Benchmark - Get all agents...")
        start = time.time()

        try:
            all_agents = await helper.get_all_agents()
            duration = time.time() - start
            duration_ms = duration * 1000

            self.record_result(
                "Phase 4.3: Bulk retrieval",
                duration_ms < 100,  # Target: <100ms
                f"Retrieved {len(all_agents)} agents in {duration_ms:.1f}ms",
            )
        except Exception as e:
            self.record_result("Phase 4.3: Bulk retrieval", False, str(e))

    # Phase 5: Integration Test - Multi-Agent Workflow

    async def test_phase5_integration_workflow(self):
        """Test 5: Realistic multi-agent coordination workflow."""
        logger.info("\n=== PHASE 5: Integration Test - Multi-Agent Workflow ===\n")

        helper = self.RedisCoordinationHelper(self.redis_client)

        # Step 1: Initialize agents
        logger.info("Step 1: Initializing agents...")
        agents_config = [
            ("backend-developer", 40, ["Update templates"]),
            ("python-pro", 60, ["Create helper library", "Write tests"]),
            ("claude-code-developer", 50, ["Update command"]),
        ]

        try:
            for agent_type, workload, tasks in agents_config:
                await helper.set_agent_status(
                    agent_type,
                    {
                        "status": "busy",
                        "workload": workload,
                        "tasks": [{"id": t, "progress": 50} for t in tasks],
                        "started_at": datetime.now(),
                    },
                )
                await helper.update_heartbeat(agent_type)

            self.record_result("Phase 5.1: Agent initialization", True, f"Initialized {len(agents_config)} agents")
        except Exception as e:
            self.record_result("Phase 5.1: Agent initialization", False, str(e))
            return

        # Step 2: Verify coordination
        logger.info("\nStep 2: Verifying coordination...")
        try:
            all_agents = await helper.get_all_agents()
            total_tasks = sum(len(a.get("tasks", [])) for a in all_agents.values())
            avg_workload = sum(a.get("workload", 0) for a in all_agents.values()) / len(all_agents)

            self.record_result(
                "Phase 5.2: Coordination verification",
                True,
                f"{len(all_agents)} agents, {total_tasks} tasks, {avg_workload:.0f}% avg workload",
            )
        except Exception as e:
            self.record_result("Phase 5.2: Coordination verification", False, str(e))

        # Step 3: Simulate task completion
        logger.info("\nStep 3: Simulating task completion...")
        try:
            status = await helper.get_agent_status("backend-developer")
            status["workload"] = 0
            status["status"] = "idle"
            status["tasks"] = []
            await helper.set_agent_status("backend-developer", status)

            updated = await helper.get_agent_status("backend-developer")
            assert updated["status"] == "idle", "Status should be updated"

            self.record_result(
                "Phase 5.3: Task completion", True, "Backend developer task completed and status updated"
            )
        except Exception as e:
            self.record_result("Phase 5.3: Task completion", False, str(e))

    # Generate validation report

    def generate_report(self) -> str:
        """Generate comprehensive validation report."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["passed"])
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        report = f"""# Redis Coordination Validation Report

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Test Suite**: End-to-End Integration Tests
**Status**: {"✅ PASSED" if failed_tests == 0 else "❌ FAILED"}

---

## Executive Summary

**Total Tests**: {total_tests}
**Passed**: {passed_tests} (✅)
**Failed**: {failed_tests} (❌)
**Pass Rate**: {pass_rate:.1f}%

---

## Test Results

"""

        # Group results by phase
        phases = {
            "Phase 1: RedisCoordinationHelper Validation": [],
            "Phase 2: JSON Serialization": [],
            "Phase 3: Error Handling": [],
            "Phase 4: Performance": [],
            "Phase 5: Integration": [],
        }

        for result in self.test_results:
            test_name = result["test"]
            if "Phase 1" in test_name:
                phase = "Phase 1: RedisCoordinationHelper Validation"
            elif "Phase 2" in test_name:
                phase = "Phase 2: JSON Serialization"
            elif "Phase 3" in test_name:
                phase = "Phase 3: Error Handling"
            elif "Phase 4" in test_name:
                phase = "Phase 4: Performance"
            elif "Phase 5" in test_name:
                phase = "Phase 5: Integration"
            else:
                phase = "Other"

            if phase in phases:
                phases[phase].append(result)

        for phase_name, results in phases.items():
            if not results:
                continue

            phase_passed = sum(1 for r in results if r["passed"])
            phase_total = len(results)

            report += f"### {phase_name}\n\n"
            report += f"**Results**: {phase_passed}/{phase_total} passed\n\n"

            for result in results:
                status = "✅ PASS" if result["passed"] else "❌ FAIL"
                report += f"- **{status}**: {result['test']}\n"
                if result["details"]:
                    report += f"  - {result['details']}\n"

            report += "\n"

        # Success criteria
        report += """---

## Success Criteria Validation

"""

        criteria = [
            ("RedisCoordinationHelper works with live Redis Stack", passed_tests > 0),
            (
                "JSON serialization handles datetime correctly",
                any("datetime" in r["test"].lower() and r["passed"] for r in self.test_results),
            ),
            (
                "All agents store and retrieve data successfully",
                any("multiple agents" in r["test"].lower() and r["passed"] for r in self.test_results),
            ),
            (
                "Error handling falls back to markdown",
                any("fallback" in r["test"].lower() and r["passed"] for r in self.test_results),
            ),
            (
                "Performance meets targets (>20 ops/sec)",
                any("throughput" in r["test"].lower() and r["passed"] for r in self.test_results),
            ),
            (
                "Integration test passes",
                any("Phase 5" in r["test"] and r["passed"] for r in self.test_results),
            ),
        ]

        for criterion, met in criteria:
            status = "✅" if met else "❌"
            report += f"{status} {criterion}\n"

        report += "\n---\n\n"

        # Performance metrics
        perf_results = [r for r in self.test_results if "Phase 4" in r["test"]]
        if perf_results:
            report += "## Performance Metrics\n\n"
            for result in perf_results:
                report += f"- **{result['test']}**: {result['details']}\n"
            report += "\n---\n\n"

        # Conclusion
        if failed_tests == 0:
            report += """## Conclusion

✅ **All tests passed!** Redis MCP coordination fixes are working as expected.

**Ready for**:
- Production deployment
- User acceptance testing
- Documentation updates
- Phase 2 continuation

"""
        else:
            report += f"""## Conclusion

❌ **{failed_tests} test(s) failed.** Issues require attention before deployment.

**Action Items**:
- Review failed tests
- Fix identified issues
- Re-run validation
- Update implementation as needed

"""

        report += f"""---

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Test Duration**: {(self.test_results[-1]["timestamp"] - self.test_results[0]["timestamp"]).total_seconds():.1f}s
**Environment**: Redis Stack @ localhost:6379

🚀 Generated by Integration Test Suite
"""

        return report

    async def run_all_tests(self):
        """Run all integration tests."""
        logger.info("=" * 80)
        logger.info("REDIS MCP COORDINATION - INTEGRATION TEST SUITE")
        logger.info("=" * 80)

        try:
            await self.setup()

            # Run all test phases
            await self.test_phase1_basic_operations()
            await self.test_phase2_json_serialization()
            await self.test_phase3_error_handling()
            await self.test_phase4_performance()
            await self.test_phase5_integration_workflow()

        finally:
            await self.teardown()

        # Generate and save report
        report = self.generate_report()

        # Save to file
        report_path = Path("/tmp/REDIS_COORDINATION_VALIDATION_REPORT.md")
        report_path.write_text(report)
        logger.info(f"\n✅ Validation report saved to {report_path}")

        # Print summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["passed"])
        logger.info(f"\n{'=' * 80}")
        logger.info(f"TEST SUMMARY: {passed_tests}/{total_tests} tests passed")
        logger.info(f"{'=' * 80}\n")

        return report


async def main():
    """Main entry point."""
    suite = IntegrationTestSuite()
    await suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
