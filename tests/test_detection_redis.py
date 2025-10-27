"""Tests for Redis detection module."""

from __future__ import annotations

import socket
from unittest.mock import Mock

import pytest
import pytest_mock

from mycelium_onboarding.detection.redis_detector import (
    RedisDetectionResult,
    detect_redis,
    scan_common_redis_ports,
)

pytestmark = pytest.mark.integration  # Mark entire file as integration


class TestDetectRedis:
    """Tests for detect_redis function."""

    def test_detect_redis_success(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test successful Redis detection."""
        # Mock socket
        mock_socket = Mock()
        mock_socket.recv.side_effect = [
            b"+PONG\r\n",  # PING response
            b"$679\r\n# Server\r\nredis_version:7.2.3\r\n",  # INFO response
        ]

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = detect_redis()

        assert result.available is True
        assert result.host == "localhost"
        assert result.port == 6379
        assert result.version == "7.2.3"
        assert result.password_required is False
        assert result.error_message is None

    def test_detect_redis_with_custom_host_port(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test Redis detection with custom host and port."""
        mock_socket = Mock()
        mock_socket.recv.side_effect = [
            b"+PONG\r\n",
            b"$679\r\n# Server\r\nredis_version:6.2.7\r\n",
        ]

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = detect_redis(host="redis.example.com", port=6380)

        assert result.available is True
        assert result.host == "redis.example.com"
        assert result.port == 6380

    def test_detect_redis_not_running(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test Redis not running scenario."""
        mock_socket = Mock()
        mock_socket.connect.side_effect = ConnectionRefusedError()

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = detect_redis()

        assert result.available is False
        assert result.error_message is not None
        assert "Connection refused" in result.error_message
        assert "redis-server" in result.error_message

    def test_detect_redis_timeout(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test Redis connection timeout."""
        mock_socket = Mock()
        mock_socket.connect.side_effect = TimeoutError()

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = detect_redis(timeout=1.0)

        assert result.available is False
        assert result.error_message is not None
        assert "timed out" in result.error_message

    def test_detect_redis_password_required(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test Redis requiring authentication."""
        mock_socket = Mock()
        mock_socket.recv.return_value = b"-NOAUTH Authentication required.\r\n"

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = detect_redis()

        assert result.available is True
        assert result.password_required is True
        assert result.error_message is not None
        assert "requires authentication" in result.error_message

    def test_detect_redis_unexpected_response(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test Redis returning unexpected response."""
        mock_socket = Mock()
        mock_socket.recv.return_value = b"-ERR unknown command\r\n"

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = detect_redis()

        assert result.available is False
        assert result.error_message is not None
        assert "Unexpected response" in result.error_message

    def test_detect_redis_hostname_resolution_error(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test Redis hostname resolution error."""
        mock_socket = Mock()
        mock_socket.connect.side_effect = socket.gaierror("Name resolution failed")

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = detect_redis(host="invalid.hostname")

        assert result.available is False
        assert result.error_message is not None
        assert "Cannot resolve hostname" in result.error_message

    def test_detect_redis_network_error(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test Redis network error."""
        mock_socket = Mock()
        mock_socket.connect.side_effect = OSError("Network unreachable")

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = detect_redis()

        assert result.available is False
        assert result.error_message is not None
        assert "Network error" in result.error_message

    def test_detect_redis_version_parsing(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test various Redis version formats."""
        test_cases = [
            ("redis_version:7.2.3\r\n", "7.2.3"),
            ("redis_version:6.2.7\r\n", "6.2.7"),
            ("redis_version:5.0.14\r\n", "5.0.14"),
        ]

        for info_response, expected_version in test_cases:
            mock_socket = Mock()
            mock_socket.recv.side_effect = [
                b"+PONG\r\n",
                info_response.encode(),
            ]

            mock_socket_class = mocker.patch("socket.socket")
            mock_socket_class.return_value = mock_socket

            result = detect_redis()

            assert result.available is True
            assert result.version == expected_version

    def test_detect_redis_no_version(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test Redis detection when version cannot be parsed."""
        mock_socket = Mock()
        mock_socket.recv.side_effect = [
            b"+PONG\r\n",
            b"$100\r\n# Server\r\n",  # No version info
        ]

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = detect_redis()

        assert result.available is True
        assert result.version is None

    def test_detect_redis_socket_cleanup(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test that socket is properly closed even on error."""
        mock_socket = Mock()
        mock_socket.connect.side_effect = Exception("Test error")

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = detect_redis()

        assert result.available is False
        mock_socket.close.assert_called_once()


class TestScanCommonRedisPorts:
    """Tests for scan_common_redis_ports function."""

    def test_scan_common_ports_all_available(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test scanning when all common ports have Redis."""
        # Mock detect_redis to return success for all ports
        mock_detect = mocker.patch(
            "mycelium_onboarding.detection.redis_detector.detect_redis"
        )
        mock_detect.side_effect = [
            RedisDetectionResult(
                available=True, host="localhost", port=6379, version="7.2.3"
            ),
            RedisDetectionResult(
                available=True, host="localhost", port=6380, version="7.2.3"
            ),
            RedisDetectionResult(
                available=True, host="localhost", port=6381, version="7.2.3"
            ),
        ]

        results = scan_common_redis_ports()

        assert len(results) == 3
        assert all(r.available for r in results)
        assert [r.port for r in results] == [6379, 6380, 6381]

    def test_scan_common_ports_some_available(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test scanning when only some ports have Redis."""
        mock_detect = mocker.patch(
            "mycelium_onboarding.detection.redis_detector.detect_redis"
        )
        mock_detect.side_effect = [
            RedisDetectionResult(
                available=True, host="localhost", port=6379, version="7.2.3"
            ),
            RedisDetectionResult(
                available=False,
                host="localhost",
                port=6380,
                error_message="Connection refused",
            ),
            RedisDetectionResult(
                available=False,
                host="localhost",
                port=6381,
                error_message="Connection refused",
            ),
        ]

        results = scan_common_redis_ports()

        assert len(results) == 1
        assert results[0].port == 6379

    def test_scan_common_ports_none_available(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test scanning when no ports have Redis."""
        mock_detect = mocker.patch(
            "mycelium_onboarding.detection.redis_detector.detect_redis"
        )
        mock_detect.side_effect = [
            RedisDetectionResult(
                available=False,
                host="localhost",
                port=6379,
                error_message="Connection refused",
            ),
            RedisDetectionResult(
                available=False,
                host="localhost",
                port=6380,
                error_message="Connection refused",
            ),
            RedisDetectionResult(
                available=False,
                host="localhost",
                port=6381,
                error_message="Connection refused",
            ),
        ]

        results = scan_common_redis_ports()

        assert len(results) == 0

    def test_scan_common_ports_custom_host(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test scanning with custom host."""
        mock_detect = mocker.patch(
            "mycelium_onboarding.detection.redis_detector.detect_redis"
        )
        mock_detect.side_effect = [
            RedisDetectionResult(
                available=True, host="redis.example.com", port=6379, version="7.2.3"
            ),
            RedisDetectionResult(
                available=False,
                host="redis.example.com",
                port=6380,
                error_message="Connection refused",
            ),
            RedisDetectionResult(
                available=False,
                host="redis.example.com",
                port=6381,
                error_message="Connection refused",
            ),
        ]

        results = scan_common_redis_ports(host="redis.example.com")

        assert len(results) == 1
        assert results[0].host == "redis.example.com"


class TestRedisDetectionResult:
    """Tests for RedisDetectionResult dataclass."""

    def test_detection_result_defaults(self) -> None:
        """Test default values of detection result."""
        result = RedisDetectionResult(available=True)

        assert result.available is True
        assert result.host == "localhost"
        assert result.port == 6379
        assert result.version is None
        assert result.password_required is False
        assert result.error_message is None

    def test_detection_result_with_values(self) -> None:
        """Test detection result with all values."""
        result = RedisDetectionResult(
            available=True,
            host="redis.example.com",
            port=6380,
            version="7.2.3",
            password_required=True,
            error_message="Authentication required",
        )

        assert result.available is True
        assert result.host == "redis.example.com"
        assert result.port == 6380
        assert result.version == "7.2.3"
        assert result.password_required is True
        assert result.error_message == "Authentication required"

    def test_detection_result_error(self) -> None:
        """Test detection result with error."""
        result = RedisDetectionResult(
            available=False,
            host="localhost",
            port=6379,
            error_message="Redis not found",
        )

        assert result.available is False
        assert result.error_message == "Redis not found"
