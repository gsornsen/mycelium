"""Detection orchestration layer.

This module coordinates all service detection modules and provides parallel
execution for fast detection times (<5 seconds).
"""

from __future__ import annotations

import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

import yaml

from mycelium_onboarding.config.schema import (
    MyceliumConfig,
)
from mycelium_onboarding.detection.docker_detector import (
    DockerDetectionResult,
    detect_docker,
)
from mycelium_onboarding.detection.gpu_detector import GPUDetectionResult, detect_gpus
from mycelium_onboarding.detection.postgres_detector import (
    PostgresDetectionResult,
    scan_common_postgres_ports,
)
from mycelium_onboarding.detection.redis_detector import (
    RedisDetectionResult,
    scan_common_redis_ports,
)
from mycelium_onboarding.detection.temporal_detector import (
    TemporalDetectionResult,
    detect_temporal,
)

__all__ = [
    "DetectionSummary",
    "detect_all_async",
    "detect_all",
    "update_config_from_detection",
    "generate_detection_report",
]


@dataclass
class DetectionSummary:
    """Summary of all detection results.

    Attributes:
        docker: Docker daemon detection result
        redis: List of detected Redis instances
        postgres: List of detected PostgreSQL instances
        temporal: Temporal server detection result
        gpu: GPU detection result
        detection_time: Total time in seconds for all detections
    """

    docker: DockerDetectionResult
    redis: list[RedisDetectionResult]
    postgres: list[PostgresDetectionResult]
    temporal: TemporalDetectionResult
    gpu: GPUDetectionResult
    detection_time: float  # Total time in seconds

    @property
    def has_docker(self) -> bool:
        """Check if Docker is available."""
        return self.docker.available

    @property
    def has_redis(self) -> bool:
        """Check if at least one Redis instance is available."""
        return any(r.available for r in self.redis)

    @property
    def has_postgres(self) -> bool:
        """Check if at least one PostgreSQL instance is available."""
        return any(p.available for p in self.postgres)

    @property
    def has_temporal(self) -> bool:
        """Check if Temporal is available."""
        return self.temporal.available

    @property
    def has_gpu(self) -> bool:
        """Check if at least one GPU is available."""
        return self.gpu.available


async def detect_all_async() -> DetectionSummary:
    """Run all detections in parallel using asyncio.

    Returns:
        DetectionSummary with all detection results

    Performance target: <5 seconds total

    All detections run concurrently using ThreadPoolExecutor to maximize
    detection speed. Individual detectors use timeouts to prevent hanging.
    """
    start_time = time.time()

    # Run all detections concurrently using thread pool
    # This allows us to parallelize I/O-bound detection operations
    with ThreadPoolExecutor(max_workers=5) as executor:
        loop = asyncio.get_event_loop()

        # Submit all detection tasks
        docker_future = loop.run_in_executor(executor, detect_docker)
        redis_future = loop.run_in_executor(executor, scan_common_redis_ports)
        postgres_future = loop.run_in_executor(executor, scan_common_postgres_ports)
        temporal_future = loop.run_in_executor(executor, detect_temporal)
        gpu_future = loop.run_in_executor(executor, detect_gpus)

        # Wait for all to complete
        docker, redis, postgres, temporal, gpu = await asyncio.gather(
            docker_future,
            redis_future,
            postgres_future,
            temporal_future,
            gpu_future,
        )

    detection_time = time.time() - start_time

    return DetectionSummary(
        docker=docker,
        redis=redis,
        postgres=postgres,
        temporal=temporal,
        gpu=gpu,
        detection_time=detection_time,
    )


def detect_all() -> DetectionSummary:
    """Synchronous wrapper for detect_all_async().

    Returns:
        DetectionSummary with all detection results

    Example:
        >>> summary = detect_all()
        >>> if summary.has_docker:
        ...     print(f"Docker version: {summary.docker.version}")
    """
    return asyncio.run(detect_all_async())


def update_config_from_detection(
    summary: DetectionSummary,
    base_config: MyceliumConfig | None = None,
) -> MyceliumConfig:
    """Create or update MyceliumConfig based on detection results.

    Args:
        summary: Detection results
        base_config: Optional base configuration to update (creates new if None)

    Returns:
        Updated MyceliumConfig with detected service settings

    Logic:
        - Enable services that are detected and available
        - Update ports from first detected instance of each service
        - Preserve existing config values if no detection available
        - Set reasonable defaults for detected services
    """
    # Start with base config or create new one
    config = base_config or MyceliumConfig()

    # Update Redis configuration
    if summary.has_redis:
        # Use first available Redis instance
        first_redis = next(r for r in summary.redis if r.available)
        config.services.redis.enabled = True
        config.services.redis.port = first_redis.port

        # Set version if detected
        if first_redis.version:
            config.services.redis.version = first_redis.version
    else:
        # Disable if not detected (but keep existing port)
        config.services.redis.enabled = False

    # Update PostgreSQL configuration
    if summary.has_postgres:
        # Use first available PostgreSQL instance
        first_postgres = next(p for p in summary.postgres if p.available)
        config.services.postgres.enabled = True
        config.services.postgres.port = first_postgres.port

        # Set version if detected
        if first_postgres.version:
            config.services.postgres.version = first_postgres.version
    else:
        # Disable if not detected (but keep existing port)
        config.services.postgres.enabled = False

    # Update Temporal configuration
    if summary.has_temporal:
        config.services.temporal.enabled = True
        config.services.temporal.frontend_port = summary.temporal.frontend_port
        config.services.temporal.ui_port = summary.temporal.ui_port

        # Set version if detected
        if summary.temporal.version:
            config.services.temporal.version = summary.temporal.version
    else:
        # Disable if not detected (but keep existing ports)
        config.services.temporal.enabled = False

    # Validate at least one service is enabled
    # If all are disabled, re-enable defaults
    if not any(
        [
            config.services.redis.enabled,
            config.services.postgres.enabled,
            config.services.temporal.enabled,
        ]
    ):
        # Re-enable all with defaults if nothing was detected
        config.services.redis.enabled = True
        config.services.postgres.enabled = True
        config.services.temporal.enabled = True

    return config


def generate_detection_report(
    summary: DetectionSummary,
    format: str = "text",
) -> str:
    """Generate human-readable detection report.

    Args:
        summary: Detection results
        format: Output format ("text", "json", "yaml")

    Returns:
        Formatted report string

    Raises:
        ValueError: If format is not supported
    """
    if format == "json":
        return _generate_json_report(summary)
    if format == "yaml":
        return _generate_yaml_report(summary)
    if format == "text":
        return _generate_text_report(summary)
    raise ValueError(f"Unsupported format: {format}. Choose 'text', 'json', or 'yaml'.")


def _generate_text_report(summary: DetectionSummary) -> str:
    """Generate text format report."""
    lines: list[str] = []

    # Header
    lines.append("Service Detection Report")
    lines.append("=" * 80)
    lines.append(f"Detection completed in {summary.detection_time:.2f}s")
    lines.append("")

    # Docker
    lines.append("Docker:")
    if summary.has_docker:
        lines.append("  Status: Available")
        lines.append(f"  Version: {summary.docker.version or 'unknown'}")
        if summary.docker.socket_path:
            lines.append(f"  Socket: {summary.docker.socket_path}")
    else:
        lines.append("  Status: Not Available")
        if summary.docker.error_message:
            lines.append(f"  Error: {summary.docker.error_message}")
    lines.append("")

    # Redis
    lines.append("Redis:")
    if summary.has_redis:
        lines.append("  Status: Available")
        lines.append(f"  Instances: {len(summary.redis)}")
        for i, redis in enumerate(summary.redis, 1):
            lines.append(f"    {i}. {redis.host}:{redis.port}")
            if redis.version:
                lines.append(f"       Version: {redis.version}")
            if redis.password_required:
                lines.append("       Auth: Required")
    else:
        lines.append("  Status: Not Available")
        lines.append("  Note: Scanned ports 6379, 6380, 6381")
    lines.append("")

    # PostgreSQL
    lines.append("PostgreSQL:")
    if summary.has_postgres:
        lines.append("  Status: Available")
        lines.append(f"  Instances: {len(summary.postgres)}")
        for i, pg in enumerate(summary.postgres, 1):
            lines.append(f"    {i}. {pg.host}:{pg.port}")
            if pg.version:
                lines.append(f"       Version: {pg.version}")
    else:
        lines.append("  Status: Not Available")
        lines.append("  Note: Scanned ports 5432, 5433")
    lines.append("")

    # Temporal
    lines.append("Temporal:")
    if summary.has_temporal:
        lines.append("  Status: Available")
        lines.append(f"  Frontend Port: {summary.temporal.frontend_port}")
        lines.append(f"  UI Port: {summary.temporal.ui_port}")
        if summary.temporal.version:
            lines.append(f"  Version: {summary.temporal.version}")
    else:
        lines.append("  Status: Not Available")
        if summary.temporal.error_message:
            lines.append(f"  Error: {summary.temporal.error_message}")
    lines.append("")

    # GPU
    lines.append("GPU:")
    if summary.has_gpu:
        lines.append("  Status: Available")
        lines.append(f"  Total GPUs: {len(summary.gpu.gpus)}")
        lines.append(f"  Total Memory: {summary.gpu.total_memory_mb} MB")
        for i, gpu in enumerate(summary.gpu.gpus, 1):
            lines.append(f"    {i}. {gpu.vendor.value.upper()}: {gpu.model}")
            if gpu.memory_mb:
                lines.append(f"       Memory: {gpu.memory_mb} MB")
            if gpu.driver_version:
                lines.append(f"       Driver: {gpu.driver_version}")
            if gpu.cuda_version:
                lines.append(f"       CUDA: {gpu.cuda_version}")
            if gpu.rocm_version:
                lines.append(f"       ROCm: {gpu.rocm_version}")
    else:
        lines.append("  Status: Not Available")
        if summary.gpu.error_message:
            lines.append(f"  Error: {summary.gpu.error_message}")
    lines.append("")

    # Summary
    lines.append("Summary:")
    services_available = sum(
        [
            summary.has_docker,
            summary.has_redis,
            summary.has_postgres,
            summary.has_temporal,
            summary.has_gpu,
        ]
    )
    lines.append(f"  Total Services Available: {services_available}/5")

    return "\n".join(lines)


def _generate_json_report(summary: DetectionSummary) -> str:
    """Generate JSON format report."""
    report: dict[str, Any] = {
        "detection_time": summary.detection_time,
        "docker": {
            "available": summary.docker.available,
            "version": summary.docker.version,
            "socket_path": summary.docker.socket_path,
            "error_message": summary.docker.error_message,
        },
        "redis": {
            "available": summary.has_redis,
            "instances": [
                {
                    "host": r.host,
                    "port": r.port,
                    "version": r.version,
                    "password_required": r.password_required,
                }
                for r in summary.redis
            ],
        },
        "postgres": {
            "available": summary.has_postgres,
            "instances": [
                {
                    "host": p.host,
                    "port": p.port,
                    "version": p.version,
                    "authentication_method": p.authentication_method,
                }
                for p in summary.postgres
            ],
        },
        "temporal": {
            "available": summary.temporal.available,
            "frontend_port": summary.temporal.frontend_port,
            "ui_port": summary.temporal.ui_port,
            "version": summary.temporal.version,
            "error_message": summary.temporal.error_message,
        },
        "gpu": {
            "available": summary.gpu.available,
            "total_memory_mb": summary.gpu.total_memory_mb,
            "gpus": [
                {
                    "vendor": gpu.vendor.value,
                    "model": gpu.model,
                    "memory_mb": gpu.memory_mb,
                    "driver_version": gpu.driver_version,
                    "cuda_version": gpu.cuda_version,
                    "rocm_version": gpu.rocm_version,
                    "index": gpu.index,
                }
                for gpu in summary.gpu.gpus
            ],
            "error_message": summary.gpu.error_message,
        },
    }

    return json.dumps(report, indent=2)


def _generate_yaml_report(summary: DetectionSummary) -> str:
    """Generate YAML format report."""
    report: dict[str, Any] = {
        "detection_time": summary.detection_time,
        "docker": {
            "available": summary.docker.available,
            "version": summary.docker.version,
            "socket_path": summary.docker.socket_path,
            "error_message": summary.docker.error_message,
        },
        "redis": {
            "available": summary.has_redis,
            "instances": [
                {
                    "host": r.host,
                    "port": r.port,
                    "version": r.version,
                    "password_required": r.password_required,
                }
                for r in summary.redis
            ],
        },
        "postgres": {
            "available": summary.has_postgres,
            "instances": [
                {
                    "host": p.host,
                    "port": p.port,
                    "version": p.version,
                    "authentication_method": p.authentication_method,
                }
                for p in summary.postgres
            ],
        },
        "temporal": {
            "available": summary.temporal.available,
            "frontend_port": summary.temporal.frontend_port,
            "ui_port": summary.temporal.ui_port,
            "version": summary.temporal.version,
            "error_message": summary.temporal.error_message,
        },
        "gpu": {
            "available": summary.gpu.available,
            "total_memory_mb": summary.gpu.total_memory_mb,
            "gpus": [
                {
                    "vendor": gpu.vendor.value,
                    "model": gpu.model,
                    "memory_mb": gpu.memory_mb,
                    "driver_version": gpu.driver_version,
                    "cuda_version": gpu.cuda_version,
                    "rocm_version": gpu.rocm_version,
                    "index": gpu.index,
                }
                for gpu in summary.gpu.gpus
            ],
            "error_message": summary.gpu.error_message,
        },
    }

    return yaml.dump(report, default_flow_style=False, sort_keys=False)
