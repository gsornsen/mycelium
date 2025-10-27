"""Tests for Docker detection module."""

from __future__ import annotations

import subprocess
from unittest.mock import Mock

import pytest
import pytest_mock

from mycelium_onboarding.detection.docker_detector import (
    DockerDetectionResult,
    detect_docker,
    verify_docker_permissions,
)

pytestmark = pytest.mark.integration  # Mark entire file as integration


class TestDetectDocker:
    """Tests for detect_docker function."""

    def test_detect_docker_success(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test successful Docker detection."""
        # Mock docker --version
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "Docker version 24.0.7, build afdd53b"
        version_result.stderr = ""

        # Mock docker info
        info_result = Mock()
        info_result.returncode = 0
        info_result.stdout = "Server Version: 24.0.7\n"
        info_result.stderr = ""

        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = [version_result, info_result]

        # Mock socket detection
        mocker.patch("pathlib.Path.exists", return_value=True)

        result = detect_docker()

        assert result.available is True
        assert result.version == "24.0.7"
        assert result.socket_path is not None
        assert result.error_message is None

    def test_detect_docker_not_installed(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test Docker not installed scenario."""
        mocker.patch(
            "subprocess.run", side_effect=FileNotFoundError("docker not found")
        )

        result = detect_docker()

        assert result.available is False
        assert result.version is None
        assert result.error_message is not None
        assert "Docker CLI not found" in result.error_message
        assert "https://docs.docker.com/get-docker/" in result.error_message

    def test_detect_docker_daemon_not_running(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test Docker installed but daemon not running."""
        # Mock docker --version success
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "Docker version 24.0.7, build afdd53b"
        version_result.stderr = ""

        # Mock docker info failure (daemon not running)
        info_result = Mock()
        info_result.returncode = 1
        info_result.stdout = ""
        info_result.stderr = "Cannot connect to the Docker daemon"

        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = [version_result, info_result]

        result = detect_docker()

        assert result.available is False
        assert result.version == "24.0.7"
        assert result.error_message is not None
        assert "daemon is not running" in result.error_message

    def test_detect_docker_permission_denied(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test Docker daemon running but no permissions."""
        # Mock docker --version success
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "Docker version 24.0.7, build afdd53b"
        version_result.stderr = ""

        # Mock docker info failure (permission denied)
        info_result = Mock()
        info_result.returncode = 1
        info_result.stdout = ""
        info_result.stderr = "permission denied while trying to connect"

        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = [version_result, info_result]

        result = detect_docker()

        assert result.available is False
        assert result.version == "24.0.7"
        assert result.error_message is not None
        assert "don't have permissions" in result.error_message
        assert "usermod -aG docker" in result.error_message

    def test_detect_docker_version_timeout(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test Docker version command timeout."""
        mocker.patch(
            "subprocess.run", side_effect=subprocess.TimeoutExpired("docker", 2.0)
        )

        result = detect_docker()

        assert result.available is False
        assert result.error_message is not None
        assert "timed out" in result.error_message

    def test_detect_docker_info_timeout(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test Docker info command timeout."""
        # Mock docker --version success
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "Docker version 24.0.7, build afdd53b"
        version_result.stderr = ""

        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = [
            version_result,
            subprocess.TimeoutExpired("docker", 2.0),
        ]

        result = detect_docker()

        assert result.available is False
        assert result.version == "24.0.7"
        assert result.error_message is not None
        assert "timed out" in result.error_message

    def test_detect_docker_cli_error(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test Docker CLI returning error."""
        version_result = Mock()
        version_result.returncode = 1
        version_result.stdout = ""
        version_result.stderr = "unknown error"

        mocker.patch("subprocess.run", return_value=version_result)

        result = detect_docker()

        assert result.available is False
        assert result.error_message is not None
        assert "Docker CLI not found" in result.error_message

    def test_detect_docker_version_parsing(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test various Docker version string formats."""
        test_cases = [
            ("Docker version 24.0.7, build afdd53b", "24.0.7"),
            ("Docker version 20.10.21", "20.10.21"),
            ("Docker version 25.0.0-rc.1, build 123abc", "25.0.0-rc.1"),
        ]

        for version_string, expected_version in test_cases:
            version_result = Mock()
            version_result.returncode = 0
            version_result.stdout = version_string
            version_result.stderr = ""

            info_result = Mock()
            info_result.returncode = 0
            info_result.stdout = "Server running"
            info_result.stderr = ""

            mock_run = mocker.patch("subprocess.run")
            mock_run.side_effect = [version_result, info_result]
            mocker.patch("pathlib.Path.exists", return_value=True)

            result = detect_docker()

            assert result.available is True
            assert result.version == expected_version

    def test_detect_docker_socket_detection_linux(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test Docker socket detection on Linux."""
        # Mock docker commands
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "Docker version 24.0.7, build afdd53b"
        version_result.stderr = ""

        info_result = Mock()
        info_result.returncode = 0
        info_result.stdout = "Server running"
        info_result.stderr = ""

        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = [version_result, info_result]

        # Mock platform and path
        mocker.patch("platform.system", return_value="Linux")
        mock_path = mocker.patch("pathlib.Path.exists")
        mock_path.return_value = True

        result = detect_docker()

        assert result.available is True
        assert result.socket_path == "/var/run/docker.sock"

    def test_detect_docker_socket_detection_windows(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test Docker socket detection on Windows."""
        # Mock docker commands
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "Docker version 24.0.7, build afdd53b"
        version_result.stderr = ""

        info_result = Mock()
        info_result.returncode = 0
        info_result.stdout = "Server running"
        info_result.stderr = ""

        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = [version_result, info_result]

        # Mock platform
        mocker.patch("platform.system", return_value="Windows")

        result = detect_docker()

        assert result.available is True
        assert result.socket_path == "npipe:////./pipe/docker_engine"


class TestVerifyDockerPermissions:
    """Tests for verify_docker_permissions function."""

    def test_verify_permissions_success(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test successful permission verification."""
        result = Mock()
        result.returncode = 0
        result.stdout = "CONTAINER ID   IMAGE     COMMAND\n"
        result.stderr = ""

        mocker.patch("subprocess.run", return_value=result)

        has_permission, error = verify_docker_permissions()

        assert has_permission is True
        assert error is None

    def test_verify_permissions_denied(self, mocker: pytest_mock.MockerFixture) -> None:
        """Test permission denied scenario."""
        result = Mock()
        result.returncode = 1
        result.stdout = ""
        result.stderr = "permission denied while trying to connect"

        mocker.patch("subprocess.run", return_value=result)

        has_permission, error = verify_docker_permissions()

        assert has_permission is False
        assert error is not None
        assert "Permission denied" in error
        assert "usermod -aG docker" in error

    def test_verify_permissions_daemon_not_running(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test daemon not running scenario."""
        result = Mock()
        result.returncode = 1
        result.stdout = ""
        result.stderr = "Cannot connect to the Docker daemon"

        mocker.patch("subprocess.run", return_value=result)

        has_permission, error = verify_docker_permissions()

        assert has_permission is False
        assert error is not None
        assert "Cannot connect" in error

    def test_verify_permissions_cli_not_found(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test Docker CLI not found."""
        mocker.patch(
            "subprocess.run", side_effect=FileNotFoundError("docker not found")
        )

        has_permission, error = verify_docker_permissions()

        assert has_permission is False
        assert error is not None
        assert "Docker CLI not found" in error

    def test_verify_permissions_timeout(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test permission verification timeout."""
        mocker.patch(
            "subprocess.run", side_effect=subprocess.TimeoutExpired("docker", 2.0)
        )

        has_permission, error = verify_docker_permissions()

        assert has_permission is False
        assert error is not None
        assert "timed out" in error

    def test_verify_permissions_unexpected_error(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        """Test unexpected error during verification."""
        mocker.patch(
            "subprocess.run", side_effect=Exception("Unexpected error")
        )

        has_permission, error = verify_docker_permissions()

        assert has_permission is False
        assert error is not None
        assert "Error verifying" in error


class TestDockerDetectionResult:
    """Tests for DockerDetectionResult dataclass."""

    def test_detection_result_defaults(self) -> None:
        """Test default values of detection result."""
        result = DockerDetectionResult(available=True)

        assert result.available is True
        assert result.version is None
        assert result.socket_path is None
        assert result.error_message is None

    def test_detection_result_with_values(self) -> None:
        """Test detection result with all values."""
        result = DockerDetectionResult(
            available=True,
            version="24.0.7",
            socket_path="/var/run/docker.sock",
            error_message=None,
        )

        assert result.available is True
        assert result.version == "24.0.7"
        assert result.socket_path == "/var/run/docker.sock"
        assert result.error_message is None

    def test_detection_result_error(self) -> None:
        """Test detection result with error."""
        result = DockerDetectionResult(
            available=False, error_message="Docker not found"
        )

        assert result.available is False
        assert result.error_message == "Docker not found"
