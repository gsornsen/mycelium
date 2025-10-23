# Source: projects/onboarding/milestones/M03_SERVICE_DETECTION.md
# Line: 737
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/detection/orchestrator.py
"""Service detection orchestrator."""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import asdict
import logging

from mycelium_onboarding.xdg_dirs import get_cache_dir
from mycelium_onboarding.detection.docker import detect_docker, DockerInfo
from mycelium_onboarding.detection.redis import detect_redis, RedisInfo
from mycelium_onboarding.detection.postgres import detect_postgres, PostgresInfo
from mycelium_onboarding.detection.temporal import detect_temporal, TemporalInfo
from mycelium_onboarding.detection.gpu import detect_gpu, GPUInfo

logger = logging.getLogger(__name__)


class DetectionResults:
    """All service detection results."""

    def __init__(
        self,
        docker: DockerInfo,
        redis: RedisInfo,
        postgres: PostgresInfo,
        temporal: TemporalInfo,
        gpu: GPUInfo,
        timestamp: datetime = None
    ):
        self.docker = docker
        self.redis = redis
        self.postgres = postgres
        self.temporal = temporal
        self.gpu = gpu
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "docker": asdict(self.docker),
            "redis": asdict(self.redis),
            "postgres": asdict(self.postgres),
            "temporal": asdict(self.temporal),
            "gpu": asdict(self.gpu),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DetectionResults":
        """Load from dictionary."""
        return cls(
            docker=DockerInfo(**data["docker"]),
            redis=RedisInfo(**data["redis"]),
            postgres=PostgresInfo(**data["postgres"]),
            temporal=TemporalInfo(**data["temporal"]),
            gpu=GPUInfo(**data["gpu"]),
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


async def detect_all_services(
    use_cache: bool = True,
    cache_ttl: int = 300  # 5 minutes
) -> DetectionResults:
    """Detect all services in parallel.

    Args:
        use_cache: Use cached results if available and fresh
        cache_ttl: Cache TTL in seconds

    Returns:
        DetectionResults with all detection results
    """
    # Try to load from cache
    if use_cache:
        cached = _load_from_cache(cache_ttl)
        if cached:
            logger.info("Using cached detection results")
            return cached

    # Run all detections in parallel
    logger.info("Running service detection (parallel)...")

    docker_task = asyncio.to_thread(detect_docker)
    redis_task = asyncio.to_thread(detect_redis)
    postgres_task = asyncio.to_thread(detect_postgres)
    temporal_task = asyncio.to_thread(detect_temporal)
    gpu_task = asyncio.to_thread(detect_gpu)

    docker, redis, postgres, temporal, gpu = await asyncio.gather(
        docker_task,
        redis_task,
        postgres_task,
        temporal_task,
        gpu_task
    )

    results = DetectionResults(
        docker=docker,
        redis=redis,
        postgres=postgres,
        temporal=temporal,
        gpu=gpu
    )

    # Save to cache
    _save_to_cache(results)

    return results


def _get_cache_path() -> Path:
    """Get cache file path."""
    cache_dir = get_cache_dir()
    return cache_dir / "service-detection.json"


def _load_from_cache(ttl: int) -> Optional[DetectionResults]:
    """Load detection results from cache if fresh."""
    cache_path = _get_cache_path()

    if not cache_path.exists():
        return None

    try:
        with open(cache_path) as f:
            data = json.load(f)

        results = DetectionResults.from_dict(data)

        # Check if cache is fresh
        age = datetime.now() - results.timestamp
        if age > timedelta(seconds=ttl):
            logger.debug("Cache expired")
            return None

        return results

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f"Failed to load cache: {e}")
        return None


def _save_to_cache(results: DetectionResults) -> None:
    """Save detection results to cache."""
    cache_path = _get_cache_path()

    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        with open(cache_path, "w") as f:
            json.dump(results.to_dict(), f, indent=2)

        logger.debug(f"Saved detection results to cache: {cache_path}")

    except (OSError, TypeError) as e:
        logger.warning(f"Failed to save cache: {e}")