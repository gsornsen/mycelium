# Source: projects/onboarding/milestones/M06_COORDINATION_TESTING.md
# Line: 847
# Valid syntax: True
# Has imports: True
# Has assignments: True

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