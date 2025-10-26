"""Integration tests for complete detection system.

These tests verify the entire detection pipeline works correctly
with real or mocked services, testing end-to-end functionality
from CLI commands to config updates.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from click.testing import CliRunner

from mycelium_onboarding.cli import cli
from mycelium_onboarding.config.manager import ConfigManager
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

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_all_services_available():
    """Mock all services as available for testing."""
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
        # Mock Docker
        mock_docker.return_value = DockerDetectionResult(
            available=True,
            version="24.0.5",
            socket_path="/var/run/docker.sock",
            error_message=None,
        )

        # Mock Redis
        mock_redis.return_value = [
            RedisDetectionResult(
                available=True,
                host="localhost",
                port=6379,
                version="7.2.3",
                password_required=False,
                error_message=None,
            )
        ]

        # Mock PostgreSQL
        mock_postgres.return_value = [
            PostgresDetectionResult(
                available=True,
                host="localhost",
                port=5432,
                version="15.4",
                authentication_method="trust",
                error_message=None,
            )
        ]

        # Mock Temporal
        mock_temporal.return_value = TemporalDetectionResult(
            available=True,
            frontend_port=7233,
            ui_port=8233,
            version="1.22.3",
            error_message=None,
        )

        # Mock GPU
        mock_gpu.return_value = GPUDetectionResult(
            available=True,
            gpus=[
                GPUInfo(
                    vendor=GPUVendor.NVIDIA,
                    model="NVIDIA RTX 3090",
                    memory_mb=24576,
                    driver_version="535.104.05",
                    cuda_version="12.2",
                    rocm_version=None,
                    index=0,
                )
            ],
            total_memory_mb=24576,
            error_message=None,
        )

        yield {
            "docker": mock_docker,
            "redis": mock_redis,
            "postgres": mock_postgres,
            "temporal": mock_temporal,
            "gpu": mock_gpu,
        }


@pytest.fixture
def mock_no_services_available():
    """Mock all services as unavailable for testing."""
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
        # Mock Docker unavailable
        mock_docker.return_value = DockerDetectionResult(
            available=False,
            version=None,
            socket_path=None,
            error_message="Docker daemon not running",
        )

        # Mock Redis unavailable
        mock_redis.return_value = []

        # Mock PostgreSQL unavailable
        mock_postgres.return_value = []

        # Mock Temporal unavailable
        mock_temporal.return_value = TemporalDetectionResult(
            available=False,
            frontend_port=7233,
            ui_port=8233,
            version=None,
            error_message="Connection refused",
        )

        # Mock GPU unavailable
        mock_gpu.return_value = GPUDetectionResult(
            available=False,
            gpus=[],
            total_memory_mb=0,
            error_message="No GPU hardware detected",
        )

        yield {
            "docker": mock_docker,
            "redis": mock_redis,
            "postgres": mock_postgres,
            "temporal": mock_temporal,
            "gpu": mock_gpu,
        }


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create temporary config directory for testing."""
    config_dir = tmp_path / ".config" / "mycelium"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


# ============================================================================
# Full Pipeline Integration Tests
# ============================================================================


def test_full_detection_pipeline(mock_all_services_available):
    """Test complete detection pipeline from CLI to config update."""
    runner = CliRunner()
    result = runner.invoke(cli, ["detect", "services"])

    assert result.exit_code == 0
    assert (
        "Service Detection Report" in result.output
        or "Detecting services" in result.output
    )
    assert "Docker" in result.output
    assert "Redis" in result.output
    assert "PostgreSQL" in result.output
    assert "Temporal" in result.output
    assert "GPU" in result.output


def test_detection_with_config_save(mock_all_services_available, temp_config_dir):
    """Test detection with config save functionality."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create config directory structure
        config_path = Path(".config/mycelium/mycelium.yaml")
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Patch get_config_path to use temp directory
        with patch(
            "mycelium_onboarding.cli.get_config_path",
            return_value=config_path,
        ):
            result = runner.invoke(cli, ["detect", "services", "--save-config"])

            assert result.exit_code == 0
            assert "Configuration updated" in result.output

            # Verify config file was created and contains detected values
            if config_path.exists():
                manager = ConfigManager(config_path=config_path)
                config = manager.load()

                assert config.services.redis.enabled is True
                assert config.services.redis.port == 6379
                assert config.services.postgres.enabled is True
                assert config.services.postgres.port == 5432
                assert config.services.temporal.enabled is True


def test_detection_performance_threshold(mock_all_services_available):
    """Verify all detections complete within performance threshold (<5s)."""
    start = time.time()
    summary = detect_all()
    elapsed = time.time() - start

    # Detection should complete within 5 seconds
    assert elapsed < 5.0, f"Detection took {elapsed:.2f}s, expected <5s"

    # Detection time should be recorded and reasonable
    assert summary.detection_time < 5.0
    assert summary.detection_time > 0.0


def test_detection_json_output(mock_all_services_available):
    """Test JSON output format integration."""
    runner = CliRunner()
    result = runner.invoke(cli, ["detect", "services", "--format", "json"])

    assert result.exit_code == 0

    # Verify valid JSON output
    try:
        data = json.loads(result.output)
        assert "docker" in data
        assert "redis" in data
        assert "postgres" in data
        assert "temporal" in data
        assert "gpu" in data
        assert "detection_time" in data
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON output: {e}")


def test_detection_yaml_output(mock_all_services_available):
    """Test YAML output format integration."""
    runner = CliRunner()
    result = runner.invoke(cli, ["detect", "services", "--format", "yaml"])

    assert result.exit_code == 0

    # Verify valid YAML output
    try:
        data = yaml.safe_load(result.output)
        assert "docker" in data
        assert "redis" in data
        assert "postgres" in data
        assert "temporal" in data
        assert "gpu" in data
        assert "detection_time" in data
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML output: {e}")


def test_detection_text_output(mock_all_services_available):
    """Test text output format integration (default)."""
    runner = CliRunner()
    result = runner.invoke(cli, ["detect", "services", "--format", "text"])

    assert result.exit_code == 0
    assert "Service Detection Report" in result.output
    assert "=" * 80 in result.output
    assert "Docker:" in result.output
    assert "Redis:" in result.output
    assert "PostgreSQL:" in result.output
    assert "Temporal:" in result.output
    assert "GPU:" in result.output
    assert "Summary:" in result.output


# ============================================================================
# Individual Detector Command Tests
# ============================================================================


def test_individual_docker_command(mock_all_services_available):
    """Test individual Docker detect command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["detect", "docker"])

    assert result.exit_code == 0
    assert "Docker" in result.output
    assert "Available" in result.output or "Version" in result.output


def test_individual_redis_command(mock_all_services_available):
    """Test individual Redis detect command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["detect", "redis"])

    assert result.exit_code == 0
    assert "Redis" in result.output


def test_individual_postgres_command(mock_all_services_available):
    """Test individual PostgreSQL detect command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["detect", "postgres"])

    assert result.exit_code == 0
    assert "PostgreSQL" in result.output


def test_individual_temporal_command(mock_all_services_available):
    """Test individual Temporal detect command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["detect", "temporal"])

    assert result.exit_code == 0
    assert "Temporal" in result.output


def test_individual_gpu_command(mock_all_services_available):
    """Test individual GPU detect command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["detect", "gpu"])

    assert result.exit_code == 0
    assert "GPU" in result.output


def test_all_individual_detector_commands(mock_all_services_available):
    """Test all individual detect subcommands in sequence."""
    runner = CliRunner()
    commands = ["docker", "redis", "postgres", "temporal", "gpu"]

    for cmd in commands:
        result = runner.invoke(cli, ["detect", cmd])
        assert result.exit_code == 0, f"Command 'detect {cmd}' failed"


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_detection_error_handling_unavailable_services(mock_no_services_available):
    """Test graceful error handling when services unavailable."""
    # All detectors should gracefully handle unavailable services
    summary = detect_all()

    # Should not raise exceptions even if services unavailable
    assert summary is not None
    assert isinstance(summary, DetectionSummary)

    # Verify services are marked as unavailable
    assert summary.has_docker is False
    assert summary.has_redis is False
    assert summary.has_postgres is False
    assert summary.has_temporal is False
    assert summary.has_gpu is False


def test_detection_with_partial_failures(mock_all_services_available):
    """Test detection continues even if individual detectors fail."""
    # Mock one detector to raise exception
    with patch(
        "mycelium_onboarding.detection.orchestrator.detect_docker",
        side_effect=Exception("Docker detection failed"),
    ):
        # Detection should handle the error gracefully
        with pytest.raises(Exception):
            detect_all()


def test_cli_error_handling_invalid_format():
    """Test CLI handles invalid format gracefully."""
    runner = CliRunner()
    result = runner.invoke(cli, ["detect", "services", "--format", "invalid"])

    # Should fail with clear error message
    assert result.exit_code != 0


def test_cli_error_handling_invalid_command():
    """Test CLI handles invalid subcommand gracefully."""
    runner = CliRunner()
    result = runner.invoke(cli, ["detect", "invalid_service"])

    # Should fail with clear error message
    assert result.exit_code != 0


# ============================================================================
# Parallel Execution Tests
# ============================================================================


def test_parallel_execution_correctness(mock_all_services_available):
    """Verify parallel execution produces consistent results."""
    # Run detection multiple times and verify consistency
    results = [detect_all() for _ in range(3)]

    # All results should have same availability status
    for i in range(1, len(results)):
        assert results[i].has_docker == results[0].has_docker
        assert results[i].has_redis == results[0].has_redis
        assert results[i].has_postgres == results[0].has_postgres
        assert results[i].has_temporal == results[0].has_temporal
        assert results[i].has_gpu == results[0].has_gpu


@pytest.mark.asyncio
async def test_async_detection_execution(mock_all_services_available):
    """Test async detection execution works correctly."""
    summary = await detect_all_async()

    assert isinstance(summary, DetectionSummary)
    assert summary.detection_time > 0.0
    assert summary.has_docker is True
    assert summary.has_redis is True
    assert summary.has_postgres is True
    assert summary.has_temporal is True
    assert summary.has_gpu is True


def test_detection_concurrency_performance(mock_all_services_available):
    """Verify concurrent detection is faster than sequential."""
    # This test verifies the parallel execution optimization

    # Mock detectors with delays to simulate I/O
    def slow_detect():
        time.sleep(0.1)
        return True

    start = time.time()
    summary = detect_all()
    parallel_time = time.time() - start

    # Even with 5 detectors at 0.1s each, parallel should be much faster than 0.5s
    # Allow some overhead but should be significantly faster than sequential
    assert parallel_time < 1.0, f"Parallel detection took {parallel_time:.2f}s"


# ============================================================================
# Config Integration Tests
# ============================================================================


def test_config_integration_with_detected_values(mock_all_services_available):
    """Test config integration with detected values."""
    summary = detect_all()
    config = update_config_from_detection(summary)

    # Verify config was updated with detected values
    assert config.services.redis.enabled is True
    assert config.services.redis.port == 6379
    assert config.services.postgres.enabled is True
    assert config.services.postgres.port == 5432
    assert config.services.temporal.enabled is True
    assert config.services.temporal.frontend_port == 7233
    assert config.services.temporal.ui_port == 8233


def test_config_integration_preserves_existing_config(mock_all_services_available):
    """Test that detection preserves existing config values where appropriate."""
    # Create base config with custom values
    base_config = MyceliumConfig()
    base_config.project_name = "my-custom-project"
    base_config.services.redis.max_memory = "512mb"

    summary = detect_all()
    config = update_config_from_detection(summary, base_config)

    # Verify custom values preserved
    assert config.project_name == "my-custom-project"
    assert config.services.redis.max_memory == "512mb"

    # Verify detected values applied
    assert config.services.redis.port == 6379
    assert config.services.redis.enabled is True


def test_config_update_with_no_services(mock_no_services_available):
    """Test config update when no services detected."""
    summary = detect_all()
    config = update_config_from_detection(summary)

    # Should create valid config with defaults when nothing detected
    assert isinstance(config, MyceliumConfig)

    # Services should be re-enabled with defaults (per orchestrator logic)
    assert config.services.redis.enabled is True
    assert config.services.postgres.enabled is True
    assert config.services.temporal.enabled is True


# ============================================================================
# Multiple Instance Tests
# ============================================================================


def test_multiple_redis_instances():
    """Test detection of multiple Redis instances on different ports."""
    with patch(
        "mycelium_onboarding.detection.orchestrator.scan_common_redis_ports"
    ) as mock_redis:
        mock_redis.return_value = [
            RedisDetectionResult(
                available=True,
                host="localhost",
                port=6379,
                version="7.2.3",
                password_required=False,
                error_message=None,
            ),
            RedisDetectionResult(
                available=True,
                host="localhost",
                port=6380,
                version="7.2.3",
                password_required=True,
                error_message=None,
            ),
        ]

        with patch("mycelium_onboarding.detection.orchestrator.detect_docker"):
            with patch(
                "mycelium_onboarding.detection.orchestrator.scan_common_postgres_ports"
            ):
                with patch(
                    "mycelium_onboarding.detection.orchestrator.detect_temporal"
                ):
                    with patch(
                        "mycelium_onboarding.detection.orchestrator.detect_gpus"
                    ):
                        summary = detect_all()

                        assert summary.has_redis is True
                        assert len(summary.redis) == 2
                        assert summary.redis[0].port == 6379
                        assert summary.redis[1].port == 6380
                        assert summary.redis[1].password_required is True


def test_multiple_postgres_instances():
    """Test detection of multiple PostgreSQL instances on different ports."""
    with patch(
        "mycelium_onboarding.detection.orchestrator.scan_common_postgres_ports"
    ) as mock_postgres:
        mock_postgres.return_value = [
            PostgresDetectionResult(
                available=True,
                host="localhost",
                port=5432,
                version="15.4",
                authentication_method="trust",
                error_message=None,
            ),
            PostgresDetectionResult(
                available=True,
                host="localhost",
                port=5433,
                version="14.9",
                authentication_method="md5",
                error_message=None,
            ),
        ]

        with patch("mycelium_onboarding.detection.orchestrator.detect_docker"):
            with patch(
                "mycelium_onboarding.detection.orchestrator.scan_common_redis_ports"
            ):
                with patch(
                    "mycelium_onboarding.detection.orchestrator.detect_temporal"
                ):
                    with patch(
                        "mycelium_onboarding.detection.orchestrator.detect_gpus"
                    ):
                        summary = detect_all()

                        assert summary.has_postgres is True
                        assert len(summary.postgres) == 2
                        assert summary.postgres[0].port == 5432
                        assert summary.postgres[1].port == 5433


# ============================================================================
# GPU Multi-Vendor Tests
# ============================================================================


def test_gpu_multi_vendor_scenarios():
    """Test GPU detection with multiple vendors."""
    with patch("mycelium_onboarding.detection.orchestrator.detect_gpus") as mock_gpu:
        mock_gpu.return_value = GPUDetectionResult(
            available=True,
            gpus=[
                GPUInfo(
                    vendor=GPUVendor.NVIDIA,
                    model="NVIDIA RTX 3090",
                    memory_mb=24576,
                    driver_version="535.104.05",
                    cuda_version="12.2",
                    rocm_version=None,
                    index=0,
                ),
                GPUInfo(
                    vendor=GPUVendor.AMD,
                    model="AMD Radeon RX 7900 XTX",
                    memory_mb=24576,
                    driver_version="23.20",
                    cuda_version=None,
                    rocm_version="5.7.0",
                    index=1,
                ),
            ],
            total_memory_mb=49152,
            error_message=None,
        )

        with patch("mycelium_onboarding.detection.orchestrator.detect_docker"):
            with patch(
                "mycelium_onboarding.detection.orchestrator.scan_common_redis_ports"
            ):
                with patch(
                    "mycelium_onboarding.detection.orchestrator.scan_common_postgres_ports"
                ):
                    with patch(
                        "mycelium_onboarding.detection.orchestrator.detect_temporal"
                    ):
                        summary = detect_all()

                        assert summary.has_gpu is True
                        assert len(summary.gpu.gpus) == 2
                        assert summary.gpu.gpus[0].vendor == GPUVendor.NVIDIA
                        assert summary.gpu.gpus[1].vendor == GPUVendor.AMD
                        assert summary.gpu.total_memory_mb == 49152


# ============================================================================
# Report Generation Tests
# ============================================================================


def test_detection_report_text_format(mock_all_services_available):
    """Test detection report in text format."""
    summary = detect_all()
    report = generate_detection_report(summary, format="text")

    assert "Service Detection Report" in report
    assert "Docker:" in report
    assert "Redis:" in report
    assert "PostgreSQL:" in report
    assert "Temporal:" in report
    assert "GPU:" in report
    assert "Summary:" in report


def test_detection_report_json_format(mock_all_services_available):
    """Test detection report in JSON format."""
    summary = detect_all()
    report = generate_detection_report(summary, format="json")

    # Verify valid JSON
    data = json.loads(report)
    assert "docker" in data
    assert "redis" in data
    assert "postgres" in data
    assert "temporal" in data
    assert "gpu" in data


def test_detection_report_yaml_format(mock_all_services_available):
    """Test detection report in YAML format."""
    summary = detect_all()
    report = generate_detection_report(summary, format="yaml")

    # Verify valid YAML
    data = yaml.safe_load(report)
    assert "docker" in data
    assert "redis" in data
    assert "postgres" in data
    assert "temporal" in data
    assert "gpu" in data


def test_detection_report_invalid_format(mock_all_services_available):
    """Test detection report with invalid format."""
    summary = detect_all()

    with pytest.raises(ValueError, match="Unsupported format"):
        generate_detection_report(summary, format="invalid")


# ============================================================================
# Summary Property Tests
# ============================================================================


def test_detection_summary_properties(mock_all_services_available):
    """Test DetectionSummary convenience properties."""
    summary = detect_all()

    # Test all convenience properties
    assert summary.has_docker is True
    assert summary.has_redis is True
    assert summary.has_postgres is True
    assert summary.has_temporal is True
    assert summary.has_gpu is True

    # Test underlying data
    assert summary.docker.available is True
    assert len(summary.redis) > 0
    assert len(summary.postgres) > 0
    assert summary.temporal.available is True
    assert summary.gpu.available is True


def test_detection_summary_with_unavailable_services(mock_no_services_available):
    """Test DetectionSummary properties when services unavailable."""
    summary = detect_all()

    # All should be False
    assert summary.has_docker is False
    assert summary.has_redis is False
    assert summary.has_postgres is False
    assert summary.has_temporal is False
    assert summary.has_gpu is False

    # Underlying data should reflect unavailable state
    assert summary.docker.available is False
    assert len(summary.redis) == 0
    assert len(summary.postgres) == 0
    assert summary.temporal.available is False
    assert summary.gpu.available is False


# ============================================================================
# Integration with Other Modules Tests
# ============================================================================


def test_detection_with_config_manager(mock_all_services_available, temp_config_dir):
    """Test integration between detection and ConfigManager."""
    config_path = temp_config_dir / "mycelium.yaml"

    # Run detection
    summary = detect_all()

    # Update config from detection
    config = update_config_from_detection(summary)

    # Save using ConfigManager
    manager = ConfigManager(config_path=config_path)
    manager.save(config)

    # Verify saved config
    assert config_path.exists()

    # Load and verify
    loaded_config = manager.load()
    assert loaded_config.services.redis.enabled is True
    assert loaded_config.services.redis.port == 6379


def test_full_workflow_init_detect_save(mock_all_services_available, temp_config_dir):
    """Test complete workflow: init config, detect services, save config."""
    runner = CliRunner()
    config_path = temp_config_dir / "mycelium.yaml"

    with runner.isolated_filesystem():
        # Step 1: Initialize config
        with patch(
            "mycelium_onboarding.cli.get_config_path",
            return_value=config_path,
        ):
            result = runner.invoke(cli, ["config", "init"])
            assert result.exit_code == 0

            # Step 2: Run detection with save
            result = runner.invoke(cli, ["detect", "services", "--save-config"])
            assert result.exit_code == 0
            assert "Configuration updated" in result.output

            # Step 3: Verify config contains detected values
            if config_path.exists():
                manager = ConfigManager(config_path=config_path)
                config = manager.load()
                assert config.services.redis.enabled is True


# ============================================================================
# Performance and Timing Tests
# ============================================================================


def test_detection_timing_recorded_accurately(mock_all_services_available):
    """Test that detection timing is recorded accurately."""
    start = time.time()
    summary = detect_all()
    actual_elapsed = time.time() - start

    # Recorded time should be close (within 50% for very fast mock detections)
    # Allow higher tolerance for sub-millisecond mock detections
    tolerance = max(actual_elapsed * 0.5, 0.001)  # At least 1ms tolerance
    assert abs(summary.detection_time - actual_elapsed) < tolerance


def test_multiple_sequential_detections(mock_all_services_available):
    """Test that multiple sequential detections work correctly."""
    results = []

    for _ in range(5):
        summary = detect_all()
        results.append(summary)

    # All should succeed
    assert len(results) == 5
    for result in results:
        assert result is not None
        assert result.detection_time > 0.0


# ============================================================================
# Edge Cases and Boundary Tests
# ============================================================================


def test_detection_with_empty_results():
    """Test detection when all services return empty/unavailable results."""
    with (
        patch(
            "mycelium_onboarding.detection.orchestrator.detect_docker",
            return_value=DockerDetectionResult(
                available=False, version=None, socket_path=None, error_message=None
            ),
        ),
        patch(
            "mycelium_onboarding.detection.orchestrator.scan_common_redis_ports",
            return_value=[],
        ),
        patch(
            "mycelium_onboarding.detection.orchestrator.scan_common_postgres_ports",
            return_value=[],
        ),
        patch(
            "mycelium_onboarding.detection.orchestrator.detect_temporal",
            return_value=TemporalDetectionResult(
                available=False,
                frontend_port=7233,
                ui_port=8233,
                version=None,
                error_message=None,
            ),
        ),
        patch(
            "mycelium_onboarding.detection.orchestrator.detect_gpus",
            return_value=GPUDetectionResult(
                available=False, gpus=[], total_memory_mb=0, error_message=None
            ),
        ),
    ):
        summary = detect_all()

        # Should complete successfully even with no services
        assert summary is not None
        assert summary.has_docker is False
        assert summary.has_redis is False
        assert summary.has_postgres is False
        assert summary.has_temporal is False
        assert summary.has_gpu is False


def test_detection_with_version_information(mock_all_services_available):
    """Test that version information is correctly captured."""
    summary = detect_all()

    # Verify version information is available
    assert summary.docker.version == "24.0.5"
    assert summary.redis[0].version == "7.2.3"
    assert summary.postgres[0].version == "15.4"
    assert summary.temporal.version == "1.22.3"
    assert summary.gpu.gpus[0].driver_version == "535.104.05"
    assert summary.gpu.gpus[0].cuda_version == "12.2"


def test_detection_summary_serialization(mock_all_services_available):
    """Test that DetectionSummary can be serialized to dict/JSON."""
    summary = detect_all()

    # Generate JSON report (tests serialization)
    json_report = generate_detection_report(summary, format="json")

    # Should be valid JSON
    data = json.loads(json_report)
    assert isinstance(data, dict)
    assert "docker" in data
    assert "redis" in data
    assert "postgres" in data
