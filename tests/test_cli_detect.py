"""Tests for CLI detection commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from mycelium_onboarding.cli import cli
from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.detection.docker_detector import DockerDetectionResult
from mycelium_onboarding.detection.gpu_detector import (
    GPUDetectionResult,
    GPUInfo,
    GPUVendor,
)
from mycelium_onboarding.detection.orchestrator import DetectionSummary
from mycelium_onboarding.detection.postgres_detector import PostgresDetectionResult
from mycelium_onboarding.detection.redis_detector import RedisDetectionResult
from mycelium_onboarding.detection.temporal_detector import TemporalDetectionResult


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_detection_summary():
    """Fixture providing a mock DetectionSummary."""
    return DetectionSummary(
        docker=DockerDetectionResult(
            available=True,
            version="24.0.7",
            socket_path="/var/run/docker.sock",
        ),
        redis=[
            RedisDetectionResult(
                available=True,
                host="localhost",
                port=6379,
                version="7.2.3",
                password_required=False,
            )
        ],
        postgres=[
            PostgresDetectionResult(
                available=True,
                host="localhost",
                port=5432,
                version="16.1",
                authentication_method="password",
            )
        ],
        temporal=TemporalDetectionResult(
            available=True,
            frontend_port=7233,
            ui_port=8080,
            version="1.22.0",
        ),
        gpu=GPUDetectionResult(
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
        ),
        detection_time=2.5,
    )


def test_detect_services_text_format(runner, mock_detection_summary):
    """Test 'detect services' command with text format."""
    with patch("mycelium_onboarding.detection.orchestrator.detect_all") as mock_detect:
        mock_detect.return_value = mock_detection_summary

        result = runner.invoke(cli, ["detect", "services"])

        assert result.exit_code == 0
        assert "Service Detection Report" in result.output
        assert "Docker:" in result.output
        assert "24.0.7" in result.output
        assert "Redis:" in result.output
        assert "6379" in result.output
        assert "PostgreSQL:" in result.output
        assert "5432" in result.output


def test_detect_services_json_format(runner, mock_detection_summary):
    """Test 'detect services --format json' command."""
    import json

    with patch("mycelium_onboarding.detection.orchestrator.detect_all") as mock_detect:
        mock_detect.return_value = mock_detection_summary

        result = runner.invoke(cli, ["detect", "services", "--format", "json"])

        assert result.exit_code == 0

        # Parse JSON output
        data = json.loads(result.output)
        assert "detection_time" in data
        assert data["docker"]["available"] is True
        assert data["redis"]["available"] is True


def test_detect_services_yaml_format(runner, mock_detection_summary):
    """Test 'detect services --format yaml' command."""
    import yaml

    with patch("mycelium_onboarding.detection.orchestrator.detect_all") as mock_detect:
        mock_detect.return_value = mock_detection_summary

        result = runner.invoke(cli, ["detect", "services", "--format", "yaml"])

        assert result.exit_code == 0

        # Parse YAML output
        data = yaml.safe_load(result.output)
        assert "detection_time" in data
        assert data["docker"]["available"] is True


def test_detect_services_save_config(runner, mock_detection_summary, tmp_path):
    """Test 'detect services --save-config' command."""
    config_file = tmp_path / "mycelium.yaml"

    with (
        patch("mycelium_onboarding.detection.orchestrator.detect_all") as mock_detect,
        patch("mycelium_onboarding.cli.get_config_path") as mock_config_path,
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_class,
    ):
        mock_detect.return_value = mock_detection_summary
        mock_config_path.return_value = config_file

        # Mock ConfigManager instance
        mock_manager = MagicMock()
        mock_manager.load.return_value = MyceliumConfig()
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(cli, ["detect", "services", "--save-config"])

        assert result.exit_code == 0
        assert "Configuration updated with detected settings" in result.output

        # Verify save was called
        mock_manager.save.assert_called()


def test_detect_services_save_config_no_existing(runner, mock_detection_summary, tmp_path):
    """Test --save-config when no existing config exists."""
    config_file = tmp_path / "mycelium.yaml"

    with (
        patch("mycelium_onboarding.detection.orchestrator.detect_all") as mock_detect,
        patch("mycelium_onboarding.cli.get_config_path") as mock_config_path,
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_class,
    ):
        mock_detect.return_value = mock_detection_summary
        mock_config_path.return_value = config_file

        # Mock ConfigManager to raise FileNotFoundError on load
        mock_manager = MagicMock()
        mock_manager.load.side_effect = FileNotFoundError("No config")
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(cli, ["detect", "services", "--save-config"])

        assert result.exit_code == 0
        assert "Configuration updated with detected settings" in result.output


def test_detect_docker(runner):
    """Test 'detect docker' command."""
    mock_result = DockerDetectionResult(
        available=True,
        version="24.0.7",
        socket_path="/var/run/docker.sock",
    )

    with patch("mycelium_onboarding.detection.docker_detector.detect_docker") as mock_detect:
        mock_detect.return_value = mock_result

        result = runner.invoke(cli, ["detect", "docker"])

        assert result.exit_code == 0
        assert "Docker Available" in result.output
        assert "24.0.7" in result.output
        assert "/var/run/docker.sock" in result.output


def test_detect_docker_not_available(runner):
    """Test 'detect docker' when Docker is not available."""
    mock_result = DockerDetectionResult(
        available=False,
        error_message="Docker not installed",
    )

    with patch("mycelium_onboarding.detection.docker_detector.detect_docker") as mock_detect:
        mock_detect.return_value = mock_result

        result = runner.invoke(cli, ["detect", "docker"])

        assert result.exit_code == 0
        assert "Docker Not Available" in result.output
        assert "Docker not installed" in result.output


def test_detect_redis(runner):
    """Test 'detect redis' command."""
    mock_results = [
        RedisDetectionResult(
            available=True,
            host="localhost",
            port=6379,
            version="7.2.3",
            password_required=False,
        ),
        RedisDetectionResult(
            available=True,
            host="localhost",
            port=6380,
            version="7.0.0",
            password_required=True,
        ),
    ]

    with patch("mycelium_onboarding.detection.redis_detector.scan_common_redis_ports") as mock_scan:
        mock_scan.return_value = mock_results

        result = runner.invoke(cli, ["detect", "redis"])

        assert result.exit_code == 0
        assert "Found 2 Redis instance(s)" in result.output
        assert "6379" in result.output
        assert "7.2.3" in result.output
        assert "6380" in result.output
        assert "Auth: Required" in result.output


def test_detect_redis_none_found(runner):
    """Test 'detect redis' when no instances are found."""
    with patch("mycelium_onboarding.detection.redis_detector.scan_common_redis_ports") as mock_scan:
        mock_scan.return_value = []

        result = runner.invoke(cli, ["detect", "redis"])

        assert result.exit_code == 0
        assert "No Redis instances found" in result.output
        assert "Scanned ports: 6379, 6380, 6381" in result.output


def test_detect_postgres(runner):
    """Test 'detect postgres' command."""
    mock_results = [
        PostgresDetectionResult(
            available=True,
            host="localhost",
            port=5432,
            version="16.1",
            authentication_method="password",
        )
    ]

    with patch("mycelium_onboarding.detection.postgres_detector.scan_common_postgres_ports") as mock_scan:
        mock_scan.return_value = mock_results

        result = runner.invoke(cli, ["detect", "postgres"])

        assert result.exit_code == 0
        assert "Found 1 PostgreSQL instance(s)" in result.output
        assert "5432" in result.output
        assert "16.1" in result.output
        assert "password" in result.output


def test_detect_postgres_none_found(runner):
    """Test 'detect postgres' when no instances are found."""
    with patch("mycelium_onboarding.detection.postgres_detector.scan_common_postgres_ports") as mock_scan:
        mock_scan.return_value = []

        result = runner.invoke(cli, ["detect", "postgres"])

        assert result.exit_code == 0
        assert "No PostgreSQL instances found" in result.output
        assert "Scanned ports: 5432, 5433" in result.output


def test_detect_temporal(runner):
    """Test 'detect temporal' command."""
    mock_result = TemporalDetectionResult(
        available=True,
        frontend_port=7233,
        ui_port=8080,
        version="1.22.0",
    )

    with patch("mycelium_onboarding.detection.temporal_detector.detect_temporal") as mock_detect:
        mock_detect.return_value = mock_result

        result = runner.invoke(cli, ["detect", "temporal"])

        assert result.exit_code == 0
        assert "Temporal Available" in result.output
        assert "7233" in result.output
        assert "8080" in result.output
        assert "1.22.0" in result.output


def test_detect_temporal_not_available(runner):
    """Test 'detect temporal' when Temporal is not available."""
    mock_result = TemporalDetectionResult(
        available=False,
        error_message="Temporal not running",
    )

    with patch("mycelium_onboarding.detection.temporal_detector.detect_temporal") as mock_detect:
        mock_detect.return_value = mock_result

        result = runner.invoke(cli, ["detect", "temporal"])

        assert result.exit_code == 0
        assert "Temporal Not Available" in result.output
        assert "Temporal not running" in result.output


def test_detect_gpu(runner):
    """Test 'detect gpu' command."""
    mock_result = GPUDetectionResult(
        available=True,
        gpus=[
            GPUInfo(
                vendor=GPUVendor.NVIDIA,
                model="NVIDIA GeForce RTX 4090",
                memory_mb=24576,
                driver_version="535.129.03",
                cuda_version="12.2",
                index=0,
            ),
            GPUInfo(
                vendor=GPUVendor.NVIDIA,
                model="NVIDIA GeForce RTX 3090",
                memory_mb=24576,
                driver_version="535.129.03",
                cuda_version="12.2",
                index=1,
            ),
        ],
        total_memory_mb=49152,
    )

    with patch("mycelium_onboarding.detection.gpu_detector.detect_gpus") as mock_detect:
        mock_detect.return_value = mock_result

        result = runner.invoke(cli, ["detect", "gpu"])

        assert result.exit_code == 0
        assert "Found 2 GPU(s)" in result.output
        assert "Total Memory: 49152 MB" in result.output
        assert "NVIDIA GeForce RTX 4090" in result.output
        assert "NVIDIA GeForce RTX 3090" in result.output
        assert "CUDA: 12.2" in result.output


def test_detect_gpu_not_available(runner):
    """Test 'detect gpu' when no GPUs are detected."""
    mock_result = GPUDetectionResult(
        available=False,
        error_message="No GPUs detected",
    )

    with patch("mycelium_onboarding.detection.gpu_detector.detect_gpus") as mock_detect:
        mock_detect.return_value = mock_result

        result = runner.invoke(cli, ["detect", "gpu"])

        assert result.exit_code == 0
        assert "No GPUs detected" in result.output


def test_detect_services_error_handling(runner):
    """Test error handling in 'detect services' command."""
    with patch("mycelium_onboarding.detection.orchestrator.detect_all") as mock_detect:
        mock_detect.side_effect = RuntimeError("Detection failed")

        result = runner.invoke(cli, ["detect", "services"])

        assert result.exit_code == 1
        assert "Detection failed" in result.output


def test_detect_docker_error_handling(runner):
    """Test error handling in 'detect docker' command."""
    with patch("mycelium_onboarding.detection.docker_detector.detect_docker") as mock_detect:
        mock_detect.side_effect = RuntimeError("Docker detection failed")

        result = runner.invoke(cli, ["detect", "docker"])

        assert result.exit_code == 1
        assert "Detection failed" in result.output


def test_detect_services_save_config_error(runner, mock_detection_summary):
    """Test error handling when config save fails."""
    with (
        patch("mycelium_onboarding.detection.orchestrator.detect_all") as mock_detect,
        patch("mycelium_onboarding.cli.ConfigManager") as mock_manager_class,
    ):
        mock_detect.return_value = mock_detection_summary

        # Mock ConfigManager to fail on save
        mock_manager = MagicMock()
        mock_manager.save.side_effect = RuntimeError("Save failed")
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(cli, ["detect", "services", "--save-config"])

        assert result.exit_code == 1
        assert "Failed to save configuration" in result.output


def test_detect_gpu_amd(runner):
    """Test 'detect gpu' command with AMD GPU."""
    mock_result = GPUDetectionResult(
        available=True,
        gpus=[
            GPUInfo(
                vendor=GPUVendor.AMD,
                model="AMD Radeon RX 7900 XTX",
                memory_mb=24576,
                driver_version="6.0.2",
                rocm_version="5.7.0",
                index=0,
            )
        ],
        total_memory_mb=24576,
    )

    with patch("mycelium_onboarding.detection.gpu_detector.detect_gpus") as mock_detect:
        mock_detect.return_value = mock_result

        result = runner.invoke(cli, ["detect", "gpu"])

        assert result.exit_code == 0
        assert "AMD Radeon RX 7900 XTX" in result.output
        assert "ROCm: 5.7.0" in result.output


def test_detect_gpu_intel(runner):
    """Test 'detect gpu' command with Intel GPU."""
    mock_result = GPUDetectionResult(
        available=True,
        gpus=[
            GPUInfo(
                vendor=GPUVendor.INTEL,
                model="Intel UHD Graphics 770",
                memory_mb=None,
                driver_version=None,
                index=0,
            )
        ],
        total_memory_mb=0,
    )

    with patch("mycelium_onboarding.detection.gpu_detector.detect_gpus") as mock_detect:
        mock_detect.return_value = mock_result

        result = runner.invoke(cli, ["detect", "gpu"])

        assert result.exit_code == 0
        assert "Intel UHD Graphics 770" in result.output


def test_detect_redis_with_password(runner):
    """Test 'detect redis' with password-protected instance."""
    mock_results = [
        RedisDetectionResult(
            available=True,
            host="localhost",
            port=6379,
            version="7.2.3",
            password_required=True,
        )
    ]

    with patch("mycelium_onboarding.detection.redis_detector.scan_common_redis_ports") as mock_scan:
        mock_scan.return_value = mock_results

        result = runner.invoke(cli, ["detect", "redis"])

        assert result.exit_code == 0
        assert "Auth: Required" in result.output
