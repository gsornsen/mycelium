# Source: projects/onboarding/milestones/M09_TESTING_SUITE.md
# Line: 246
# Valid syntax: True
# Has imports: True
# Has assignments: True

# tests/unit/test_detection.py
"""Unit tests for infrastructure detection."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from mycelium.detection import (
    InfraDetector,
    DetectionResults,
    ServiceStatus,
    RedisDetection,
)


class TestRedisDetection:
    """Tests for Redis service detection."""

    @patch('subprocess.run')
    def test_detect_docker_redis(self, mock_run):
        """Test detection of Redis running in Docker."""
        # Arrange
        mock_run.return_value = Mock(
            returncode=0,
            stdout="mycelium-redis\n6379/tcp\nrunning"
        )

        detector = InfraDetector()

        # Act
        result = detector.detect_redis()

        # Assert
        assert result.available
        assert result.method == "docker"
        assert result.port == 6379
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_detect_native_redis(self, mock_run):
        """Test detection of Redis running natively (systemd)."""
        # Arrange
        mock_run.side_effect = [
            Mock(returncode=1, stdout=""),  # Docker check fails
            Mock(returncode=0, stdout="active")  # Systemd check succeeds
        ]

        detector = InfraDetector()

        # Act
        result = detector.detect_redis()

        # Assert
        assert result.available
        assert result.method == "systemd"
        assert mock_run.call_count == 2

    @patch('subprocess.run')
    def test_detect_redis_not_found(self, mock_run):
        """Test detection when Redis is not running."""
        # Arrange
        mock_run.return_value = Mock(returncode=1, stdout="")

        detector = InfraDetector()

        # Act
        result = detector.detect_redis()

        # Assert
        assert not result.available
        assert result.method is None

    @patch('socket.socket')
    def test_detect_redis_port_in_use(self, mock_socket):
        """Test detection of Redis by checking if port 6379 is in use."""
        # Arrange
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.connect_ex.return_value = 0  # Port is open

        detector = InfraDetector()

        # Act
        result = detector._check_redis_port()

        # Assert
        assert result
        mock_sock.connect_ex.assert_called_with(('localhost', 6379))


class TestInfraDetectorFullScan:
    """Tests for complete infrastructure scanning."""

    @patch.object(InfraDetector, 'detect_redis')
    @patch.object(InfraDetector, 'detect_postgres')
    @patch.object(InfraDetector, 'detect_docker')
    def test_scan_all_services(self, mock_docker, mock_postgres, mock_redis):
        """Test scanning all services returns complete results."""
        # Arrange
        mock_redis.return_value = RedisDetection(available=True, method="docker")
        mock_postgres.return_value = Mock(available=False)
        mock_docker.return_value = Mock(available=True, version="24.0.0")

        detector = InfraDetector()

        # Act
        results = detector.scan_all()

        # Assert
        assert isinstance(results, DetectionResults)
        assert results.redis.available
        assert not results.postgres.available
        assert results.docker.available
        mock_redis.assert_called_once()
        mock_postgres.assert_called_once()
        mock_docker.assert_called_once()