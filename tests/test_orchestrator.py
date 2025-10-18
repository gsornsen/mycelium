"""Tests for detection orchestrator module."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.detection.docker_detector import DockerDetectionResult
from mycelium_onboarding.detection.gpu_detector import (
    GPUDetectionResult,
    GPUInfo,
    GPUVendor,
)
from mycelium_onboarding.detection.orchestrator import (
    DetectionSummary,
    detect_all,
    detect_all_async,
    generate_detection_report,
    update_config_from_detection,
)
from mycelium_onboarding.detection.postgres_detector import PostgresDetectionResult
from mycelium_onboarding.detection.redis_detector import RedisDetectionResult
from mycelium_onboarding.detection.temporal_detector import TemporalDetectionResult


@pytest.fixture
def mock_detection_results():
    """Fixture providing mock detection results."""
    docker = DockerDetectionResult(
        available=True,
        version="24.0.7",
        socket_path="/var/run/docker.sock",
    )

    redis = [
        RedisDetectionResult(
            available=True,
            host="localhost",
            port=6379,
            version="7.2.3",
            password_required=False,
        )
    ]

    postgres = [
        PostgresDetectionResult(
            available=True,
            host="localhost",
            port=5432,
            version="16.1",
            authentication_method="password",
        )
    ]

    temporal = TemporalDetectionResult(
        available=True,
        frontend_port=7233,
        ui_port=8080,
        version="1.22.0",
    )

    gpu = GPUDetectionResult(
        available=True,
        gpus=[
            GPUInfo(
                vendor=GPUVendor.NVIDIA,
                model="NVIDIA GeForce RTX 4090",
                memory_mb=24576,
                driver_version="535.129.03",
                cuda_version="12.2",
                index=0,
            )
        ],
        total_memory_mb=24576,
    )

    return {
        "docker": docker,
        "redis": redis,
        "postgres": postgres,
        "temporal": temporal,
        "gpu": gpu,
    }


@pytest.fixture
def detection_summary(mock_detection_results):
    """Fixture providing a DetectionSummary instance."""
    return DetectionSummary(
        docker=mock_detection_results["docker"],
        redis=mock_detection_results["redis"],
        postgres=mock_detection_results["postgres"],
        temporal=mock_detection_results["temporal"],
        gpu=mock_detection_results["gpu"],
        detection_time=2.5,
    )


def test_detection_summary_properties(detection_summary):
    """Test DetectionSummary convenience properties."""
    assert detection_summary.has_docker is True
    assert detection_summary.has_redis is True
    assert detection_summary.has_postgres is True
    assert detection_summary.has_temporal is True
    assert detection_summary.has_gpu is True


def test_detection_summary_properties_unavailable():
    """Test DetectionSummary properties when services are unavailable."""
    summary = DetectionSummary(
        docker=DockerDetectionResult(available=False, error_message="Not installed"),
        redis=[],
        postgres=[],
        temporal=TemporalDetectionResult(available=False, error_message="Not running"),
        gpu=GPUDetectionResult(available=False, error_message="No GPUs"),
        detection_time=1.0,
    )

    assert summary.has_docker is False
    assert summary.has_redis is False
    assert summary.has_postgres is False
    assert summary.has_temporal is False
    assert summary.has_gpu is False


@pytest.mark.asyncio
async def test_detect_all_async_performance(mock_detection_results):
    """Test that parallel detection completes in <5 seconds."""
    with (
        patch(
            "mycelium_onboarding.detection.orchestrator.detect_docker"
        ) as mock_docker,
        patch(
            "mycelium_onboarding.detection.orchestrator.scan_common_redis_ports"
        ) as mock_redis,
        patch(
            "mycelium_onboarding.detection.orchestrator.scan_common_postgres_ports"
        ) as mock_postgres,
        patch(
            "mycelium_onboarding.detection.orchestrator.detect_temporal"
        ) as mock_temporal,
        patch("mycelium_onboarding.detection.orchestrator.detect_gpus") as mock_gpu,
    ):
        # Configure mocks
        mock_docker.return_value = mock_detection_results["docker"]
        mock_redis.return_value = mock_detection_results["redis"]
        mock_postgres.return_value = mock_detection_results["postgres"]
        mock_temporal.return_value = mock_detection_results["temporal"]
        mock_gpu.return_value = mock_detection_results["gpu"]

        # Run detection
        summary = await detect_all_async()

        # Verify performance
        assert summary.detection_time < 5.0

        # Verify all detections were called
        mock_docker.assert_called_once()
        mock_redis.assert_called_once()
        mock_postgres.assert_called_once()
        mock_temporal.assert_called_once()
        mock_gpu.assert_called_once()


def test_detect_all_sync(mock_detection_results):
    """Test synchronous wrapper."""
    with (
        patch(
            "mycelium_onboarding.detection.orchestrator.detect_docker"
        ) as mock_docker,
        patch(
            "mycelium_onboarding.detection.orchestrator.scan_common_redis_ports"
        ) as mock_redis,
        patch(
            "mycelium_onboarding.detection.orchestrator.scan_common_postgres_ports"
        ) as mock_postgres,
        patch(
            "mycelium_onboarding.detection.orchestrator.detect_temporal"
        ) as mock_temporal,
        patch("mycelium_onboarding.detection.orchestrator.detect_gpus") as mock_gpu,
    ):
        # Configure mocks
        mock_docker.return_value = mock_detection_results["docker"]
        mock_redis.return_value = mock_detection_results["redis"]
        mock_postgres.return_value = mock_detection_results["postgres"]
        mock_temporal.return_value = mock_detection_results["temporal"]
        mock_gpu.return_value = mock_detection_results["gpu"]

        # Run detection
        summary = detect_all()

        # Verify type
        assert isinstance(summary, DetectionSummary)
        assert summary.has_docker is True
        assert summary.detection_time < 5.0


def test_update_config_from_detection_all_available(detection_summary):
    """Test config update when all services are detected."""
    config = update_config_from_detection(detection_summary)

    # Verify services are enabled
    assert config.services.redis.enabled is True
    assert config.services.postgres.enabled is True
    assert config.services.temporal.enabled is True

    # Verify ports are updated
    assert config.services.redis.port == 6379
    assert config.services.postgres.port == 5432
    assert config.services.temporal.frontend_port == 7233
    assert config.services.temporal.ui_port == 8080

    # Verify versions
    assert config.services.redis.version == "7.2.3"
    assert config.services.postgres.version == "16.1"
    assert config.services.temporal.version == "1.22.0"


def test_update_config_from_detection_none_available():
    """Test config update when no services are detected."""
    summary = DetectionSummary(
        docker=DockerDetectionResult(available=False),
        redis=[],
        postgres=[],
        temporal=TemporalDetectionResult(available=False),
        gpu=GPUDetectionResult(available=False),
        detection_time=1.0,
    )

    config = update_config_from_detection(summary)

    # When nothing is detected, services should be re-enabled with defaults
    assert config.services.redis.enabled is True
    assert config.services.postgres.enabled is True
    assert config.services.temporal.enabled is True


def test_update_config_from_detection_with_base_config(detection_summary):
    """Test config update preserves base config values."""
    base_config = MyceliumConfig(project_name="test-project")
    base_config.services.redis.max_memory = "512mb"
    base_config.services.postgres.database = "custom_db"

    config = update_config_from_detection(
        summary=detection_summary, base_config=base_config
    )

    # Verify base config values are preserved
    assert config.project_name == "test-project"
    assert config.services.redis.max_memory == "512mb"
    assert config.services.postgres.database == "custom_db"

    # Verify detected values are applied
    assert config.services.redis.port == 6379
    assert config.services.postgres.port == 5432


def test_update_config_from_detection_multiple_instances(mock_detection_results):
    """Test config update uses first instance when multiple are detected."""
    # Add second Redis instance
    redis_instances = [
        RedisDetectionResult(
            available=True, host="localhost", port=6379, version="7.2.3"
        ),
        RedisDetectionResult(
            available=True, host="localhost", port=6380, version="7.0.0"
        ),
    ]

    summary = DetectionSummary(
        docker=mock_detection_results["docker"],
        redis=redis_instances,
        postgres=mock_detection_results["postgres"],
        temporal=mock_detection_results["temporal"],
        gpu=mock_detection_results["gpu"],
        detection_time=2.0,
    )

    config = update_config_from_detection(summary)

    # Should use first instance
    assert config.services.redis.port == 6379
    assert config.services.redis.version == "7.2.3"


def test_generate_detection_report_text(detection_summary):
    """Test text format report generation."""
    report = generate_detection_report(detection_summary, format="text")

    # Verify report contains key information
    assert "Service Detection Report" in report
    assert "Docker:" in report
    assert "24.0.7" in report
    assert "Redis:" in report
    assert "6379" in report
    assert "PostgreSQL:" in report
    assert "5432" in report
    assert "Temporal:" in report
    assert "7233" in report
    assert "GPU:" in report
    assert "NVIDIA GeForce RTX 4090" in report
    assert "2.5" in report  # detection time


def test_generate_detection_report_json(detection_summary):
    """Test JSON format report generation."""
    import json

    report = generate_detection_report(detection_summary, format="json")

    # Parse JSON
    data = json.loads(report)

    # Verify structure
    assert "detection_time" in data
    assert data["detection_time"] == 2.5

    assert "docker" in data
    assert data["docker"]["available"] is True
    assert data["docker"]["version"] == "24.0.7"

    assert "redis" in data
    assert data["redis"]["available"] is True
    assert len(data["redis"]["instances"]) == 1
    assert data["redis"]["instances"][0]["port"] == 6379

    assert "postgres" in data
    assert data["postgres"]["available"] is True

    assert "temporal" in data
    assert data["temporal"]["available"] is True

    assert "gpu" in data
    assert data["gpu"]["available"] is True
    assert len(data["gpu"]["gpus"]) == 1


def test_generate_detection_report_yaml(detection_summary):
    """Test YAML format report generation."""
    import yaml

    report = generate_detection_report(detection_summary, format="yaml")

    # Parse YAML
    data = yaml.safe_load(report)

    # Verify structure
    assert "detection_time" in data
    assert data["detection_time"] == 2.5

    assert "docker" in data
    assert data["docker"]["available"] is True
    assert data["docker"]["version"] == "24.0.7"

    assert "redis" in data
    assert data["redis"]["available"] is True

    assert "gpu" in data
    assert data["gpu"]["available"] is True


def test_generate_detection_report_invalid_format(detection_summary):
    """Test error handling for invalid format."""
    with pytest.raises(ValueError, match="Unsupported format"):
        generate_detection_report(detection_summary, format="xml")


def test_generate_detection_report_unavailable_services():
    """Test report generation when services are unavailable."""
    summary = DetectionSummary(
        docker=DockerDetectionResult(
            available=False, error_message="Docker not installed"
        ),
        redis=[],
        postgres=[],
        temporal=TemporalDetectionResult(
            available=False, error_message="Temporal not running"
        ),
        gpu=GPUDetectionResult(available=False, error_message="No GPUs detected"),
        detection_time=1.0,
    )

    report = generate_detection_report(summary, format="text")

    # Verify error messages are included
    assert "Not Available" in report
    assert "Docker not installed" in report
    assert "Temporal not running" in report
    assert "No GPUs detected" in report


def test_detection_summary_with_partial_results(mock_detection_results):
    """Test DetectionSummary with some services available and some not."""
    summary = DetectionSummary(
        docker=mock_detection_results["docker"],
        redis=mock_detection_results["redis"],
        postgres=[],  # PostgreSQL not available
        temporal=TemporalDetectionResult(available=False),
        gpu=mock_detection_results["gpu"],
        detection_time=2.0,
    )

    assert summary.has_docker is True
    assert summary.has_redis is True
    assert summary.has_postgres is False
    assert summary.has_temporal is False
    assert summary.has_gpu is True


def test_update_config_selective_detection(mock_detection_results):
    """Test that config update handles selective detection correctly."""
    summary = DetectionSummary(
        docker=mock_detection_results["docker"],
        redis=mock_detection_results["redis"],
        postgres=[],  # Not detected
        temporal=TemporalDetectionResult(available=False),
        gpu=mock_detection_results["gpu"],
        detection_time=2.0,
    )

    config = update_config_from_detection(summary)

    # Redis should be enabled (detected)
    assert config.services.redis.enabled is True
    assert config.services.redis.port == 6379

    # PostgreSQL and Temporal should be disabled (not detected)
    # Redis alone satisfies the "at least one service" requirement
    assert config.services.postgres.enabled is False
    assert config.services.temporal.enabled is False


@pytest.mark.asyncio
async def test_detect_all_async_parallel_execution(mock_detection_results):
    """Test that detections run in parallel (not sequential)."""
    import time

    call_times = []

    def slow_detect_docker():
        call_times.append(("docker", time.time()))
        time.sleep(0.1)
        return mock_detection_results["docker"]

    def slow_detect_redis():
        call_times.append(("redis", time.time()))
        time.sleep(0.1)
        return mock_detection_results["redis"]

    def slow_detect_postgres():
        call_times.append(("postgres", time.time()))
        time.sleep(0.1)
        return mock_detection_results["postgres"]

    def slow_detect_temporal():
        call_times.append(("temporal", time.time()))
        time.sleep(0.1)
        return mock_detection_results["temporal"]

    def slow_detect_gpu():
        call_times.append(("gpu", time.time()))
        time.sleep(0.1)
        return mock_detection_results["gpu"]

    with (
        patch(
            "mycelium_onboarding.detection.orchestrator.detect_docker",
            side_effect=slow_detect_docker,
        ),
        patch(
            "mycelium_onboarding.detection.orchestrator.scan_common_redis_ports",
            side_effect=slow_detect_redis,
        ),
        patch(
            "mycelium_onboarding.detection.orchestrator.scan_common_postgres_ports",
            side_effect=slow_detect_postgres,
        ),
        patch(
            "mycelium_onboarding.detection.orchestrator.detect_temporal",
            side_effect=slow_detect_temporal,
        ),
        patch(
            "mycelium_onboarding.detection.orchestrator.detect_gpus",
            side_effect=slow_detect_gpu,
        ),
    ):
        summary = await detect_all_async()

        # If executed in parallel, total time should be ~0.1s (not 0.5s)
        # Allow some overhead
        assert summary.detection_time < 0.3

        # Verify all detections were called
        assert len(call_times) == 5

        # Check that all calls started around the same time (parallel execution)
        start_times = [t for _, t in call_times]
        time_spread = max(start_times) - min(start_times)
        # All should start within 0.05s of each other (parallel)
        assert time_spread < 0.05
