"""Tests for PostgreSQL detection module."""

from __future__ import annotations

import socket
from unittest.mock import Mock

import pytest
import pytest_mock

from mycelium_onboarding.detection.postgres_detector import (
    PostgresDetectionResult,
    detect_postgres,
    scan_common_postgres_ports,
)

pytestmark = pytest.mark.integration  # Mark entire file as integration


class TestDetectPostgres:
    """Tests for detect_postgres function."""

    def test_detect_postgres_success(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test successful PostgreSQL detection."""
        mock_socket = Mock()
        mock_socket.recv.return_value = b"N"  # SSL not supported

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        # Mock version detection to return None (optional)
        mocker.patch(
            "mycelium_onboarding.detection.postgres_detector._attempt_version_detection",
            return_value="16.1",
        )

        result = detect_postgres()

        assert result.available is True
        assert result.host == "localhost"
        assert result.port == 5432
        assert result.version == "16.1"
        assert result.error_message is None

    def test_detect_postgres_with_custom_host_port(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test PostgreSQL detection with custom host and port."""
        mock_socket = Mock()
        mock_socket.recv.return_value = b"S"  # SSL supported

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        mocker.patch(
            "mycelium_onboarding.detection.postgres_detector._attempt_version_detection",
            return_value=None,
        )

        result = detect_postgres(host="db.example.com", port=5433)

        assert result.available is True
        assert result.host == "db.example.com"
        assert result.port == 5433
        assert result.authentication_method == "ssl"

    def test_detect_postgres_not_running(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test PostgreSQL not running scenario."""
        mock_socket = Mock()
        mock_socket.connect.side_effect = ConnectionRefusedError()

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = detect_postgres()

        assert result.available is False
        assert result.error_message is not None
        assert "Connection refused" in result.error_message
        assert "systemctl start postgresql" in result.error_message

    def test_detect_postgres_timeout(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test PostgreSQL connection timeout."""
        mock_socket = Mock()
        mock_socket.connect.side_effect = TimeoutError()

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = detect_postgres(timeout=1.0)

        assert result.available is False
        assert result.error_message is not None
        assert "timed out" in result.error_message

    def test_detect_postgres_no_response(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test PostgreSQL not responding."""
        mock_socket = Mock()
        mock_socket.recv.return_value = b""

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = detect_postgres()

        assert result.available is False
        assert result.error_message is not None
        assert "No response" in result.error_message

    def test_detect_postgres_hostname_resolution_error(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test PostgreSQL hostname resolution error."""
        mock_socket = Mock()
        mock_socket.connect.side_effect = socket.gaierror("Name resolution failed")

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = detect_postgres(host="invalid.hostname")

        assert result.available is False
        assert result.error_message is not None
        assert "Cannot resolve hostname" in result.error_message

    def test_detect_postgres_network_error(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test PostgreSQL network error."""
        mock_socket = Mock()
        mock_socket.connect.side_effect = OSError("Network unreachable")

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = detect_postgres()

        assert result.available is False
        assert result.error_message is not None
        assert "Network error" in result.error_message

    def test_detect_postgres_ssl_supported(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test PostgreSQL with SSL support."""
        mock_socket = Mock()
        mock_socket.recv.return_value = b"S"

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        mocker.patch(
            "mycelium_onboarding.detection.postgres_detector._attempt_version_detection",
            return_value=None,
        )

        result = detect_postgres()

        assert result.available is True
        assert result.authentication_method == "ssl"

    def test_detect_postgres_ssl_not_supported(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test PostgreSQL without SSL support."""
        mock_socket = Mock()
        mock_socket.recv.return_value = b"N"

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        mocker.patch(
            "mycelium_onboarding.detection.postgres_detector._attempt_version_detection",
            return_value=None,
        )

        result = detect_postgres()

        assert result.available is True
        assert result.authentication_method == "password"

    def test_detect_postgres_socket_cleanup(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test that socket is properly closed even on error."""
        mock_socket = Mock()
        mock_socket.connect.side_effect = Exception("Test error")

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = detect_postgres()

        assert result.available is False
        mock_socket.close.assert_called_once()


class TestScanCommonPostgresPorts:
    """Tests for scan_common_postgres_ports function."""

    def test_scan_common_ports_all_available(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test scanning when all common ports have PostgreSQL."""
        mock_detect = mocker.patch(
            "mycelium_onboarding.detection.postgres_detector.detect_postgres"
        )
        mock_detect.side_effect = [
            PostgresDetectionResult(
                available=True, host="localhost", port=5432, version="16.1"
            ),
            PostgresDetectionResult(
                available=True, host="localhost", port=5433, version="15.4"
            ),
        ]

        results = scan_common_postgres_ports()

        assert len(results) == 2
        assert all(r.available for r in results)
        assert [r.port for r in results] == [5432, 5433]

    def test_scan_common_ports_some_available(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test scanning when only some ports have PostgreSQL."""
        mock_detect = mocker.patch(
            "mycelium_onboarding.detection.postgres_detector.detect_postgres"
        )
        mock_detect.side_effect = [
            PostgresDetectionResult(
                available=True, host="localhost", port=5432, version="16.1"
            ),
            PostgresDetectionResult(
                available=False,
                host="localhost",
                port=5433,
                error_message="Connection refused",
            ),
        ]

        results = scan_common_postgres_ports()

        assert len(results) == 1
        assert results[0].port == 5432

    def test_scan_common_ports_none_available(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test scanning when no ports have PostgreSQL."""
        mock_detect = mocker.patch(
            "mycelium_onboarding.detection.postgres_detector.detect_postgres"
        )
        mock_detect.side_effect = [
            PostgresDetectionResult(
                available=False,
                host="localhost",
                port=5432,
                error_message="Connection refused",
            ),
            PostgresDetectionResult(
                available=False,
                host="localhost",
                port=5433,
                error_message="Connection refused",
            ),
        ]

        results = scan_common_postgres_ports()

        assert len(results) == 0

    def test_scan_common_ports_custom_host(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test scanning with custom host."""
        mock_detect = mocker.patch(
            "mycelium_onboarding.detection.postgres_detector.detect_postgres"
        )
        mock_detect.side_effect = [
            PostgresDetectionResult(
                available=True, host="db.example.com", port=5432, version="16.1"
            ),
            PostgresDetectionResult(
                available=False,
                host="db.example.com",
                port=5433,
                error_message="Connection refused",
            ),
        ]

        results = scan_common_postgres_ports(host="db.example.com")

        assert len(results) == 1
        assert results[0].host == "db.example.com"


class TestVersionDetection:
    """Tests for PostgreSQL version detection helper functions."""

    def test_parse_error_message_version(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test parsing version from error message."""
        from mycelium_onboarding.detection.postgres_detector import (
            _parse_error_message_version,
        )

        test_cases = [
            (b"PostgreSQL 16.1 on x86_64-linux", "16.1"),
            (b"server version 15.4", "15.4"),
            (b"database system version 14.10", "14.10"),
            (b"No version info", None),
        ]

        for response, expected_version in test_cases:
            result = _parse_error_message_version(response)
            assert result == expected_version

    def test_build_startup_message(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test building PostgreSQL startup message."""
        from mycelium_onboarding.detection.postgres_detector import (
            _build_startup_message,
        )

        message = _build_startup_message()

        # Check that it's bytes
        assert isinstance(message, bytes)
        # Check minimum length (should have length prefix, protocol, and params)
        assert len(message) > 20
        # Check that it contains user and database params
        assert b"user\x00postgres\x00" in message
        assert b"database\x00postgres\x00" in message


class TestPostgresDetectionResult:
    """Tests for PostgresDetectionResult dataclass."""

    def test_detection_result_defaults(self) -> None:
        """Test default values of detection result."""
        result = PostgresDetectionResult(available=True)

        assert result.available is True
        assert result.host == "localhost"
        assert result.port == 5432
        assert result.version is None
        assert result.authentication_method is None
        assert result.error_message is None

    def test_detection_result_with_values(self) -> None:
        """Test detection result with all values."""
        result = PostgresDetectionResult(
            available=True,
            host="db.example.com",
            port=5433,
            version="16.1",
            authentication_method="ssl",
            error_message=None,
        )

        assert result.available is True
        assert result.host == "db.example.com"
        assert result.port == 5433
        assert result.version == "16.1"
        assert result.authentication_method == "ssl"
        assert result.error_message is None

    def test_detection_result_error(self) -> None:
        """Test detection result with error."""
        result = PostgresDetectionResult(
            available=False,
            host="localhost",
            port=5432,
            error_message="PostgreSQL not found",
        )

        assert result.available is False
        assert result.error_message == "PostgreSQL not found"

    def test_attempt_version_detection_with_error_response(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test version detection with PostgreSQL error response."""
        from mycelium_onboarding.detection.postgres_detector import (
            _attempt_version_detection,
        )

        mock_socket = Mock()
        mock_socket.recv.return_value = b"EFATAL\x00PostgreSQL 16.1 server error"

        version = _attempt_version_detection(mock_socket, 2.0)

        assert version == "16.1"

    def test_attempt_version_detection_with_exception(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test version detection handles exceptions gracefully."""
        from mycelium_onboarding.detection.postgres_detector import (
            _attempt_version_detection,
        )

        mock_socket = Mock()
        mock_socket.sendall.side_effect = Exception("Network error")

        # Should not raise, should return None
        version = _attempt_version_detection(mock_socket, 2.0)

        assert version is None

    def test_parse_error_message_version_with_exception(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test error message parsing handles exceptions."""
        from mycelium_onboarding.detection.postgres_detector import (
            _parse_error_message_version,
        )

        # Invalid byte sequence that might cause decode issues
        result = _parse_error_message_version(b"\xff\xfe")

        # Should handle gracefully
        assert result is None
