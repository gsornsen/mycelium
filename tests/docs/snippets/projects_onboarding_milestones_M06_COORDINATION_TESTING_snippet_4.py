# Source: projects/onboarding/milestones/M06_COORDINATION_TESTING.md
# Line: 698
# Valid syntax: True
# Has imports: True
# Has assignments: True

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