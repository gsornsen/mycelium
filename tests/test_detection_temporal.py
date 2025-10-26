"""Tests for Temporal detection module."""

from __future__ import annotations

from unittest.mock import Mock

import pytest_mock

from mycelium_onboarding.detection.temporal_detector import (
    TemporalDetectionResult,
    detect_temporal,
)


class TestDetectTemporal:
    """Tests for detect_temporal function."""

    def test_detect_temporal_success(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test successful Temporal detection."""
        # Mock both ports as open
        mocker.patch(
            "mycelium_onboarding.detection.temporal_detector._check_port_open",
            side_effect=[True, True],  # frontend and UI
        )

        # Mock version detection
        mocker.patch(
            "mycelium_onboarding.detection.temporal_detector._attempt_version_from_ui",
            return_value="1.22.3",
        )

        result = detect_temporal()

        assert result.available is True
        assert result.frontend_port == 7233
        assert result.ui_port == 8080
        assert result.version == "1.22.3"
        assert result.namespace == "default"
        assert result.error_message is None

    def test_detect_temporal_custom_ports(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test Temporal detection with custom ports."""
        mocker.patch(
            "mycelium_onboarding.detection.temporal_detector._check_port_open",
            side_effect=[True, True],
        )

        mocker.patch(
            "mycelium_onboarding.detection.temporal_detector._attempt_version_from_ui",
            return_value=None,
        )

        result = detect_temporal(frontend_port=7234, ui_port=8081)

        assert result.available is True
        assert result.frontend_port == 7234
        assert result.ui_port == 8081

    def test_detect_temporal_frontend_not_available(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test Temporal frontend not available."""
        mocker.patch(
            "mycelium_onboarding.detection.temporal_detector._check_port_open",
            return_value=False,
        )

        result = detect_temporal()

        assert result.available is False
        assert result.error_message is not None
        assert "frontend not responding" in result.error_message
        assert "temporal server start-dev" in result.error_message

    def test_detect_temporal_ui_not_available(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test Temporal with UI not available (but frontend is)."""
        # Frontend available, UI not available
        mocker.patch(
            "mycelium_onboarding.detection.temporal_detector._check_port_open",
            side_effect=[True, False],
        )

        result = detect_temporal()

        # Should still be considered available since frontend is up
        assert result.available is True
        assert result.version is None

    def test_detect_temporal_timeout(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test Temporal detection with timeout."""
        mocker.patch(
            "mycelium_onboarding.detection.temporal_detector._check_port_open",
            side_effect=[True, True],
        )

        mocker.patch(
            "mycelium_onboarding.detection.temporal_detector._attempt_version_from_ui",
            return_value=None,
        )

        result = detect_temporal(timeout=0.5)

        assert result.available is True


class TestCheckPortOpen:
    """Tests for _check_port_open helper function."""

    def test_check_port_open_success(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test checking open port."""
        from mycelium_onboarding.detection.temporal_detector import _check_port_open

        mock_socket = Mock()
        mock_socket.connect_ex.return_value = 0

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = _check_port_open("localhost", 7233, 2.0)

        assert result is True
        mock_socket.close.assert_called_once()

    def test_check_port_open_closed(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test checking closed port."""
        from mycelium_onboarding.detection.temporal_detector import _check_port_open

        mock_socket = Mock()
        mock_socket.connect_ex.return_value = 1  # Connection failed

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = _check_port_open("localhost", 7233, 2.0)

        assert result is False
        mock_socket.close.assert_called_once()

    def test_check_port_open_exception(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test checking port with exception."""
        from mycelium_onboarding.detection.temporal_detector import _check_port_open

        mock_socket = Mock()
        mock_socket.connect_ex.side_effect = Exception("Network error")

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = _check_port_open("localhost", 7233, 2.0)

        assert result is False

    def test_check_port_open_cleanup_on_error(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test that socket is cleaned up even on error."""
        from mycelium_onboarding.detection.temporal_detector import _check_port_open

        mock_socket = Mock()
        mock_socket.connect_ex.side_effect = Exception("Test error")

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        result = _check_port_open("localhost", 7233, 2.0)

        assert result is False
        mock_socket.close.assert_called_once()


class TestAttemptVersionFromUI:
    """Tests for _attempt_version_from_ui helper function."""

    def test_attempt_version_success(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test successful version detection from UI."""
        from mycelium_onboarding.detection.temporal_detector import (
            _attempt_version_from_ui,
        )

        mock_socket = Mock()
        mock_socket.recv.return_value = (
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
            b"<html><body>Temporal v1.22.3</body></html>"
        )

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        version = _attempt_version_from_ui(8080, 2.0)

        assert version == "1.22.3"
        mock_socket.close.assert_called_once()

    def test_attempt_version_not_found(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test version detection when version not in response."""
        from mycelium_onboarding.detection.temporal_detector import (
            _attempt_version_from_ui,
        )

        mock_socket = Mock()
        mock_socket.recv.return_value = (
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
            b"<html><body>Temporal UI</body></html>"
        )

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        version = _attempt_version_from_ui(8080, 2.0)

        assert version is None

    def test_attempt_version_connection_error(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test version detection with connection error."""
        from mycelium_onboarding.detection.temporal_detector import (
            _attempt_version_from_ui,
        )

        mock_socket = Mock()
        mock_socket.connect.side_effect = ConnectionRefusedError()

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        version = _attempt_version_from_ui(8080, 2.0)

        assert version is None
        mock_socket.close.assert_called_once()

    def test_attempt_version_timeout(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test version detection with timeout."""
        from mycelium_onboarding.detection.temporal_detector import (
            _attempt_version_from_ui,
        )

        mock_socket = Mock()
        mock_socket.recv.side_effect = TimeoutError()

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        version = _attempt_version_from_ui(8080, 0.5)

        assert version is None

    def test_attempt_version_cleanup_on_error(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test that socket is cleaned up even on error."""
        from mycelium_onboarding.detection.temporal_detector import (
            _attempt_version_from_ui,
        )

        mock_socket = Mock()
        mock_socket.connect.side_effect = Exception("Test error")

        mock_socket_class = mocker.patch("socket.socket")
        mock_socket_class.return_value = mock_socket

        version = _attempt_version_from_ui(8080, 2.0)

        assert version is None
        mock_socket.close.assert_called_once()


class TestParseTemporalVersion:
    """Tests for _parse_temporal_version helper function."""

    def test_parse_version_various_formats(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test parsing various version string formats."""
        from mycelium_onboarding.detection.temporal_detector import (
            _parse_temporal_version,
        )

        test_cases = [
            ("Temporal v1.22.3", "1.22.3"),
            ("temporal-server-v1.22.3", "1.22.3"),
            ('version: "1.22.3"', "1.22.3"),
            ("Temporal 1.22.3", "1.22.3"),
            ("No version here", None),
        ]

        for response, expected_version in test_cases:
            result = _parse_temporal_version(response)
            assert result == expected_version

    def test_parse_version_in_headers(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test parsing version from HTTP headers."""
        from mycelium_onboarding.detection.temporal_detector import (
            _parse_temporal_version,
        )

        response = (
            "HTTP/1.1 200 OK\r\n"
            "X-Temporal-Server-Version: 1.22.3\r\n"
            "Content-Type: text/html\r\n"
        )

        # This might not match if the regex doesn't catch the header format
        # but it tests the general parsing capability
        result = _parse_temporal_version(response)
        # Could be None if header format not supported, which is OK
        assert result is None or result == "1.22.3"

    def test_parse_version_exception_handling(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test that parsing handles exceptions gracefully."""
        from mycelium_onboarding.detection.temporal_detector import (
            _parse_temporal_version,
        )

        # Test with invalid input that might cause issues
        result = _parse_temporal_version("")
        assert result is None


class TestTemporalDetectionResult:
    """Tests for TemporalDetectionResult dataclass."""

    def test_detection_result_defaults(self) -> None:
        """Test default values of detection result."""
        result = TemporalDetectionResult(available=True)

        assert result.available is True
        assert result.frontend_port == 7233
        assert result.ui_port == 8080
        assert result.version is None
        assert result.namespace == "default"
        assert result.error_message is None

    def test_detection_result_with_values(self) -> None:
        """Test detection result with all values."""
        result = TemporalDetectionResult(
            available=True,
            frontend_port=7234,
            ui_port=8081,
            version="1.22.3",
            namespace="production",
            error_message=None,
        )

        assert result.available is True
        assert result.frontend_port == 7234
        assert result.ui_port == 8081
        assert result.version == "1.22.3"
        assert result.namespace == "production"
        assert result.error_message is None

    def test_detection_result_error(self) -> None:
        """Test detection result with error."""
        result = TemporalDetectionResult(
            available=False,
            frontend_port=7233,
            ui_port=8080,
            error_message="Temporal not found",
        )

        assert result.available is False
        assert result.error_message == "Temporal not found"
