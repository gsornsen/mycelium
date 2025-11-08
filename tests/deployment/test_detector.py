"""Tests for service detection module."""

from __future__ import annotations

from unittest.mock import Mock, patch

from mycelium_onboarding.deployment.strategy.detector import (
    DetectedService,
    ServiceDetector,
    ServiceStatus,
    ServiceType,
)


class TestServiceDetector:
    """Tests for ServiceDetector class."""

    def test_init(self):
        """Test ServiceDetector initialization."""
        detector = ServiceDetector()
        assert detector.scan_system is True
        assert detector.scan_docker is True
        assert detector._detected_services == []

    def test_init_custom_scan_settings(self):
        """Test ServiceDetector with custom scan settings."""
        detector = ServiceDetector(scan_system=False, scan_docker=True)
        assert detector.scan_system is False
        assert detector.scan_docker is True


class TestRedisCapabilityDetection:
    """Tests for Redis capability detection including JSON module."""

    def test_detect_redis_capabilities_with_json_module(self):
        """Test Redis capability detection when JSON module is present."""
        detector = ServiceDetector()

        # Mock redis module import
        with patch("builtins.__import__") as mock_import:
            mock_redis = Mock()
            mock_client = Mock()

            def import_side_effect(name, *args, **kwargs):
                if name == "redis":
                    return mock_redis
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect
            mock_redis.Redis.return_value = mock_client

            # Mock successful connection and info
            mock_client.ping.return_value = True
            mock_client.info.return_value = {"redis_version": "7.2.3"}

            # Mock MODULE LIST with ReJSON
            mock_client.execute_command.return_value = [
                ["name", b"ReJSON", "ver", 20009, "path", "/usr/lib/redis/modules/rejson.so"]
            ]

            caps = detector.detect_redis_capabilities("localhost", 6379)

            assert caps["host"] == "localhost"
            assert caps["port"] == 6379
            assert caps["version"] == "7.2.3"
            assert caps["has_json_module"] is True
            assert caps["status"] == "compatible"
            assert caps["recommendation"] is None
            assert "ReJSON" in caps["modules"]

    def test_detect_redis_capabilities_without_json_module(self):
        """Test Redis capability detection when JSON module is missing."""
        detector = ServiceDetector()

        with patch("builtins.__import__") as mock_import:
            mock_redis = Mock()
            mock_client = Mock()

            def import_side_effect(name, *args, **kwargs):
                if name == "redis":
                    return mock_redis
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect
            mock_redis.Redis.return_value = mock_client

            # Mock successful connection
            mock_client.ping.return_value = True
            mock_client.info.return_value = {"redis_version": "6.2.7"}

            # Mock empty MODULE LIST (no modules loaded)
            mock_client.execute_command.return_value = []

            caps = detector.detect_redis_capabilities("localhost", 6379)

            assert caps["host"] == "localhost"
            assert caps["port"] == 6379
            assert caps["version"] == "6.2.7"
            assert caps["has_json_module"] is False
            assert caps["status"] == "limited"
            assert caps["recommendation"] == "Upgrade to Redis Stack for full coordination support"
            assert caps["modules"] == []

    def test_detect_redis_capabilities_connection_error(self):
        """Test Redis capability detection with connection error."""
        detector = ServiceDetector()

        with patch("builtins.__import__") as mock_import:
            mock_redis = Mock()
            mock_client = Mock()

            def import_side_effect(name, *args, **kwargs):
                if name == "redis":
                    return mock_redis
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect
            mock_redis.Redis.return_value = mock_client

            # Create exception class
            connection_error = type("ConnectionError", (Exception,), {})
            mock_redis.exceptions.ConnectionError = connection_error

            # Mock connection failure
            mock_client.ping.side_effect = connection_error("Connection refused")

            caps = detector.detect_redis_capabilities("localhost", 6379)

            assert caps["host"] == "localhost"
            assert caps["port"] == 6379
            assert caps["status"] == "unreachable"
            assert "error" in caps

    def test_detect_redis_capabilities_no_redis_py(self):
        """Test Redis capability detection when redis-py is not installed."""
        detector = ServiceDetector()

        with patch("builtins.__import__") as mock_import:

            def import_side_effect(name, *args, **kwargs):
                if name == "redis":
                    raise ImportError("No module named 'redis'")
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            caps = detector.detect_redis_capabilities("localhost", 6379)

            assert caps["status"] == "unknown"
            assert "redis-py" in caps["error"]

    def test_detect_redis_capabilities_module_list_error(self):
        """Test Redis capability detection when MODULE LIST command fails."""
        detector = ServiceDetector()

        with patch("builtins.__import__") as mock_import:
            mock_redis = Mock()
            mock_client = Mock()

            def import_side_effect(name, *args, **kwargs):
                if name == "redis":
                    return mock_redis
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect
            mock_redis.Redis.return_value = mock_client

            # Create exception class
            response_error = type("ResponseError", (Exception,), {})
            mock_redis.exceptions.ResponseError = response_error

            mock_client.ping.return_value = True
            mock_client.info.return_value = {"redis_version": "5.0.14"}

            # Mock MODULE LIST failure (command not supported in older Redis)
            mock_client.execute_command.side_effect = response_error("ERR unknown command 'MODULE'")

            caps = detector.detect_redis_capabilities("localhost", 6379)

            assert caps["version"] == "5.0.14"
            assert caps["has_json_module"] is False
            assert caps["modules"] == []
            assert caps["status"] == "limited"

    def test_detect_redis_capabilities_json_module_name_variations(self):
        """Test detection of JSON module with different naming conventions."""
        detector = ServiceDetector()

        test_cases = [
            (b"ReJSON", True),
            (b"rejson", True),
            ("json", True),
            ("JSON", True),
            (b"search", False),
        ]

        for module_name, should_detect in test_cases:
            with patch("builtins.__import__") as mock_import:
                mock_redis = Mock()
                mock_client = Mock()

                def import_side_effect(name, *args, _mock_redis=mock_redis, **kwargs):
                    if name == "redis":
                        return _mock_redis
                    return __import__(name, *args, **kwargs)

                mock_import.side_effect = import_side_effect
                mock_redis.Redis.return_value = mock_client

                mock_client.ping.return_value = True
                mock_client.info.return_value = {"redis_version": "7.2.3"}
                mock_client.execute_command.return_value = [["name", module_name]]

                caps = detector.detect_redis_capabilities("localhost", 6379)

                assert caps["has_json_module"] == should_detect, f"Failed for module_name={module_name}"


class TestRedisDetectionIntegration:
    """Integration tests for Redis detection with capabilities."""

    def test_detect_redis_includes_capabilities(self):
        """Test that _detect_redis includes capability information when Redis is running."""
        detector = ServiceDetector()

        with patch("subprocess.run") as mock_run:
            # Mock redis-cli detection
            mock_run.side_effect = [
                Mock(returncode=0, stdout="/usr/bin/redis-cli\n"),  # which redis-cli
                Mock(returncode=0, stdout="redis-cli 7.2.3\n"),  # redis-cli --version
                Mock(returncode=0, stdout="PONG\n"),  # redis-cli ping
                Mock(returncode=0, stdout="1234\n"),  # pgrep redis-server
            ]

            with patch.object(detector, "detect_redis_capabilities") as mock_caps:
                mock_caps.return_value = {
                    "host": "localhost",
                    "port": 6379,
                    "version": "7.2.3",
                    "modules": ["ReJSON"],
                    "has_json_module": True,
                    "status": "compatible",
                    "recommendation": None,
                }

                result = detector._detect_redis()

                assert result is not None
                assert result.service_type == ServiceType.REDIS
                assert result.status == ServiceStatus.RUNNING
                assert result.capabilities is not None
                assert result.capabilities["has_json_module"] is True
                mock_caps.assert_called_once_with("localhost", 6379)

    def test_detect_redis_no_capabilities_when_stopped(self):
        """Test that capabilities are not checked when Redis is not running."""
        detector = ServiceDetector()

        with patch("subprocess.run") as mock_run:
            # Mock redis-cli detection but service not running
            mock_run.side_effect = [
                Mock(returncode=0, stdout="/usr/bin/redis-cli\n"),  # which redis-cli
                Mock(returncode=0, stdout="redis-cli 7.2.3\n"),  # redis-cli --version
                Mock(returncode=1, stdout=""),  # redis-cli ping (fails)
            ]

            with patch.object(detector, "detect_redis_capabilities") as mock_caps:
                result = detector._detect_redis()

                assert result is not None
                assert result.status == ServiceStatus.STOPPED
                assert result.capabilities is None
                mock_caps.assert_not_called()


class TestDetectorServiceTypes:
    """Tests for different service type detection."""

    def test_detect_service_redis(self):
        """Test detecting Redis service type."""
        detector = ServiceDetector()

        with patch.object(detector, "_detect_redis") as mock_detect:
            mock_detect.return_value = DetectedService(
                name="redis",
                service_type=ServiceType.REDIS,
                status=ServiceStatus.RUNNING,
                version="7.2.3",
                port=6379,
            )

            result = detector.detect_service(ServiceType.REDIS)

            assert result is not None
            assert result.service_type == ServiceType.REDIS
            mock_detect.assert_called_once()

    def test_detect_service_postgresql(self):
        """Test detecting PostgreSQL service type."""
        detector = ServiceDetector()

        with patch.object(detector, "_detect_postgresql") as mock_detect:
            mock_detect.return_value = DetectedService(
                name="postgresql",
                service_type=ServiceType.POSTGRESQL,
                status=ServiceStatus.RUNNING,
                version="15.3",
                port=5432,
            )

            result = detector.detect_service(ServiceType.POSTGRESQL)

            assert result is not None
            assert result.service_type == ServiceType.POSTGRESQL
            mock_detect.assert_called_once()

    def test_detect_service_unknown_type(self):
        """Test detecting unknown service type."""
        detector = ServiceDetector()

        result = detector.detect_service(ServiceType.RABBITMQ)

        assert result is None
