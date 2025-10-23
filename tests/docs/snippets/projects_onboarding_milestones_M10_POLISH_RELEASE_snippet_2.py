# Source: projects/onboarding/milestones/M10_POLISH_RELEASE.md
# Line: 418
# Valid syntax: True
# Has imports: True
# Has assignments: True

# scripts/performance_benchmark.py
"""Performance benchmarking for key operations."""

import cProfile
import pstats
import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass
from io import StringIO


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""
    operation_name: str
    mean_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    iterations: int


class PerformanceBenchmark:
    """Performance benchmarking suite."""

    def __init__(self, iterations: int = 100):
        self.iterations = iterations
        self.results: list[BenchmarkResult] = []

    def benchmark_operation(
        self,
        name: str,
        operation: Callable,
        warmup: int = 10
    ) -> BenchmarkResult:
        """Benchmark a single operation."""
        print(f"Benchmarking: {name}")

        # Warmup
        for _ in range(warmup):
            operation()

        # Measure
        timings: list[float] = []
        for _ in range(self.iterations):
            start = time.perf_counter()
            operation()
            end = time.perf_counter()
            timings.append((end - start) * 1000)  # Convert to ms

        # Calculate statistics
        result = BenchmarkResult(
            operation_name=name,
            mean_ms=statistics.mean(timings),
            median_ms=statistics.median(timings),
            p95_ms=self._percentile(timings, 95),
            p99_ms=self._percentile(timings, 99),
            min_ms=min(timings),
            max_ms=max(timings),
            iterations=self.iterations
        )

        self.results.append(result)
        self._print_result(result)

        return result

    def profile_operation(
        self,
        name: str,
        operation: Callable
    ):
        """Profile operation with cProfile to identify hotspots."""
        print(f"\nProfiling: {name}")

        profiler = cProfile.Profile()
        profiler.enable()

        operation()

        profiler.disable()

        # Print stats
        stream = StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.strip_dirs()
        stats.sort_stats('cumulative')
        stats.print_stats(20)  # Top 20 functions

        print(stream.getvalue())

    def _percentile(self, data: list[float], percentile: int) -> float:
        """Calculate percentile of data."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[index]

    def _print_result(self, result: BenchmarkResult):
        """Print benchmark result."""
        print(f"  Mean: {result.mean_ms:.2f}ms")
        print(f"  Median: {result.median_ms:.2f}ms")
        print(f"  P95: {result.p95_ms:.2f}ms")
        print(f"  P99: {result.p99_ms:.2f}ms")
        print(f"  Range: [{result.min_ms:.2f}ms - {result.max_ms:.2f}ms]")
        print()

    def generate_report(self):
        """Generate performance benchmark report."""
        print("=" * 60)
        print("Performance Benchmark Report")
        print("=" * 60)

        for result in self.results:
            status = "✓ PASS" if result.mean_ms < 100 else "⚠ SLOW"
            print(f"{status} {result.operation_name}: {result.mean_ms:.2f}ms (mean)")


def main():
    """Run performance benchmarks."""
    from mycelium.config import MyceliumConfig
    from mycelium.detection import InfraDetector
    from mycelium.generators import DockerComposeGenerator, JustfileGenerator

    benchmark = PerformanceBenchmark(iterations=100)

    # Benchmark detection operations
    detector = InfraDetector()
    benchmark.benchmark_operation(
        "Docker Detection",
        lambda: detector.detect_docker()
    )
    benchmark.benchmark_operation(
        "Redis Detection",
        lambda: detector.detect_redis()
    )
    benchmark.benchmark_operation(
        "Full Infrastructure Scan",
        lambda: detector.scan_all()
    )

    # Benchmark configuration operations
    sample_config = MyceliumConfig()
    benchmark.benchmark_operation(
        "Configuration Validation",
        lambda: MyceliumConfig.model_validate(sample_config.model_dump())
    )

    # Benchmark generation operations
    docker_gen = DockerComposeGenerator()
    benchmark.benchmark_operation(
        "Docker Compose Generation",
        lambda: docker_gen.generate(sample_config)
    )

    justfile_gen = JustfileGenerator()
    benchmark.benchmark_operation(
        "Justfile Generation",
        lambda: justfile_gen.generate(sample_config)
    )

    # Generate report
    benchmark.generate_report()

    # Profile slowest operation
    print("\n" + "=" * 60)
    print("Detailed Profiling")
    print("=" * 60)
    benchmark.profile_operation(
        "Full Infrastructure Scan (detailed)",
        lambda: detector.scan_all()
    )


if __name__ == "__main__":
    main()
