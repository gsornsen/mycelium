"""Service detection package for Mycelium onboarding.

This package provides hardware and service detection capabilities for:
- GPU detection (NVIDIA, AMD, Intel)
- Docker detection and validation
- Kubernetes cluster detection
- Runtime environment detection
- Redis service detection
- PostgreSQL service detection
- Temporal service detection
- Detection orchestration (parallel execution)
"""

from __future__ import annotations

from mycelium_onboarding.detection.docker_detector import (
    DockerDetectionResult,
    detect_docker,
    verify_docker_permissions,
)
from mycelium_onboarding.detection.orchestrator import (
    DetectionSummary,
    detect_all,
    detect_all_async,
    generate_detection_report,
    update_config_from_detection,
)
from mycelium_onboarding.detection.postgres_detector import (
    PostgresDetectionResult,
    detect_postgres,
    scan_common_postgres_ports,
)
from mycelium_onboarding.detection.redis_detector import (
    RedisDetectionResult,
    detect_redis,
    scan_common_redis_ports,
)
from mycelium_onboarding.detection.temporal_detector import (
    TemporalDetectionResult,
    detect_temporal,
)

__all__ = [
    "gpu_detector",
    # Docker
    "DockerDetectionResult",
    "detect_docker",
    "verify_docker_permissions",
    # Redis
    "RedisDetectionResult",
    "detect_redis",
    "scan_common_redis_ports",
    # PostgreSQL
    "PostgresDetectionResult",
    "detect_postgres",
    "scan_common_postgres_ports",
    # Temporal
    "TemporalDetectionResult",
    "detect_temporal",
    # Orchestrator
    "DetectionSummary",
    "detect_all",
    "detect_all_async",
    "generate_detection_report",
    "update_config_from_detection",
]
