"""Unit tests for telemetry infrastructure."""

import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest

# Add plugins directory to Python path
plugins_dir = Path(__file__).parent.parent.parent / "plugins" / "mycelium-core"
sys.path.insert(0, str(plugins_dir))

from telemetry.anonymization import DataAnonymizer
from telemetry.client import TelemetryClient
from telemetry.config import TelemetryConfig


class TestTelemetryConfig:
    """Tests for TelemetryConfig."""

    def test_default_config_disabled(self) -> None:
        """Test that telemetry is disabled by default."""
        config = TelemetryConfig()
        assert config.enabled is False
        assert config.is_enabled() is False

    def test_config_from_env_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading config from environment when disabled."""
        monkeypatch.delenv("TELEMETRY_ENABLED", raising=False)
        config = TelemetryConfig.from_env()
        assert config.enabled is False

    def test_config_from_env_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading config from environment when enabled."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "true")
        monkeypatch.setenv("TELEMETRY_ENDPOINT", "https://test.example.com")
        monkeypatch.setenv("TELEMETRY_TIMEOUT", "10")
        monkeypatch.setenv("TELEMETRY_BATCH_SIZE", "50")

        config = TelemetryConfig.from_env()
        assert config.enabled is True
        assert str(config.endpoint) == "https://test.example.com/"
        assert config.timeout == 10
        assert config.batch_size == 50

    def test_config_enabled_variations(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test various ways to enable telemetry."""
        for value in ["true", "True", "TRUE", "1", "yes", "on"]:
            monkeypatch.setenv("TELEMETRY_ENABLED", value)
            config = TelemetryConfig.from_env()
            assert config.enabled is True, f"Failed for value: {value}"

    def test_config_disabled_variations(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test various ways telemetry stays disabled."""
        for value in ["false", "False", "FALSE", "0", "no", "off", ""]:
            monkeypatch.setenv("TELEMETRY_ENABLED", value)
            config = TelemetryConfig.from_env()
            assert config.enabled is False, f"Failed for value: {value}"

    def test_endpoint_validation(self) -> None:
        """Test endpoint URL validation."""
        # Should add https:// if missing
        config = TelemetryConfig(
            enabled=True,
            endpoint="test.example.com",  # type: ignore
        )
        assert str(config.endpoint).startswith("https://")

        # Should accept http://
        config = TelemetryConfig(
            enabled=True,
            endpoint="http://localhost:8080",  # type: ignore
        )
        assert str(config.endpoint).startswith("http://")

    def test_config_validation_ranges(self) -> None:
        """Test configuration value validation."""
        # Valid timeout
        config = TelemetryConfig(timeout=5)
        assert config.timeout == 5

        # Invalid timeout (too low)
        with pytest.raises(ValueError):
            TelemetryConfig(timeout=0)

        # Invalid timeout (too high)
        with pytest.raises(ValueError):
            TelemetryConfig(timeout=100)

        # Valid batch size
        config = TelemetryConfig(batch_size=100)
        assert config.batch_size == 100

        # Invalid batch size
        with pytest.raises(ValueError):
            TelemetryConfig(batch_size=0)

    def test_salt_generation(self) -> None:
        """Test that salt is auto-generated if not provided."""
        config1 = TelemetryConfig()
        config2 = TelemetryConfig()

        # Each config should have a unique salt
        assert config1.salt != config2.salt
        assert len(config1.salt) == 64  # 32 bytes hex-encoded


class TestDataAnonymizer:
    """Tests for DataAnonymizer."""

    @pytest.fixture
    def anonymizer(self) -> DataAnonymizer:
        """Create anonymizer with fixed salt for testing."""
        return DataAnonymizer(salt="test_salt_12345")

    def test_hash_identifier_deterministic(self, anonymizer: DataAnonymizer) -> None:
        """Test that hashing is deterministic."""
        hash1 = anonymizer.hash_identifier("user123")
        hash2 = anonymizer.hash_identifier("user123")
        assert hash1 == hash2

    def test_hash_identifier_unique(self, anonymizer: DataAnonymizer) -> None:
        """Test that different identifiers produce different hashes."""
        hash1 = anonymizer.hash_identifier("user123")
        hash2 = anonymizer.hash_identifier("user456")
        assert hash1 != hash2

    def test_hash_identifier_salt_impact(self) -> None:
        """Test that different salts produce different hashes."""
        anon1 = DataAnonymizer(salt="salt1")
        anon2 = DataAnonymizer(salt="salt2")

        hash1 = anon1.hash_identifier("user123")
        hash2 = anon2.hash_identifier("user123")
        assert hash1 != hash2

    def test_anonymize_unix_file_path(self, anonymizer: DataAnonymizer) -> None:
        """Test anonymizing Unix file paths."""
        path = "/home/john/project/myfile.py"
        anonymized = anonymizer.anonymize_file_path(path)
        assert "john" not in anonymized
        assert "<user>" in anonymized or "myfile.py" in anonymized

    def test_anonymize_windows_file_path(self, anonymizer: DataAnonymizer) -> None:
        """Test anonymizing Windows file paths."""
        path = "C:\\Users\\jane\\Documents\\code.py"
        anonymized = anonymizer.anonymize_file_path(path)
        assert "jane" not in anonymized
        assert "<user>" in anonymized or "code.py" in anonymized

    def test_anonymize_stack_trace(self, anonymizer: DataAnonymizer) -> None:
        """Test anonymizing stack traces."""
        trace = """File "/home/user/project/file.py", line 42, in function
    raise ValueError("error")
ValueError: error"""
        anonymized = anonymizer.anonymize_stack_trace(trace)

        # Should not contain full path
        assert "/home/user" not in anonymized
        # Should contain file name
        assert "file.py" in anonymized
        # Should preserve line number and error
        assert "line 42" in anonymized
        assert "ValueError" in anonymized

    def test_anonymize_error(self, anonymizer: DataAnonymizer) -> None:
        """Test anonymizing error data."""
        error_data = anonymizer.anonymize_error(
            error_type="ValueError",
            error_message="Invalid value in /home/user/file.py",
            stack_trace='File "/home/user/file.py", line 10',
        )

        assert error_data["error_type"] == "ValueError"
        assert "/home/user" not in error_data["error_message"]
        assert "/home/user" not in error_data["stack_trace"]

    def test_anonymize_agent_usage(self, anonymizer: DataAnonymizer) -> None:
        """Test anonymizing agent usage data."""
        usage_data = anonymizer.anonymize_agent_usage(
            agent_id="agent-123",
            operation="discover",
            metadata={"duration_ms": 150, "success": True},
        )

        assert "agent_id_hash" in usage_data
        assert usage_data["agent_id_hash"] != "agent-123"
        assert usage_data["operation"] == "discover"
        assert usage_data["metadata"]["duration_ms"] == 150

    def test_filter_safe_metadata(self, anonymizer: DataAnonymizer) -> None:
        """Test filtering metadata for safe fields only."""
        unsafe_metadata = {
            "duration_ms": 100,
            "user_prompt": "secret data",  # Should be filtered
            "file_content": "code",  # Should be filtered
            "success": True,
            "nested_dict": {"key": "value"},  # Should be filtered
        }

        safe = anonymizer._filter_safe_metadata(unsafe_metadata)

        assert "duration_ms" in safe
        assert "success" in safe
        assert "user_prompt" not in safe
        assert "file_content" not in safe
        assert "nested_dict" not in safe

    def test_anonymize_performance_metric(self, anonymizer: DataAnonymizer) -> None:
        """Test anonymizing performance metrics."""
        metric = anonymizer.anonymize_performance_metric(
            metric_name="discovery_latency",
            value=123.45,
            unit="ms",
            tags={"agent_id": "agent-123", "operation": "search"},
        )

        assert metric["metric_name"] == "discovery_latency"
        assert metric["value"] == 123.45
        assert metric["unit"] == "ms"
        # agent_id tag should be hashed
        assert metric["tags"]["agent_id"] != "agent-123"
        # operation tag should not be hashed
        assert metric["tags"]["operation"] == "search"

    def test_email_anonymization(self, anonymizer: DataAnonymizer) -> None:
        """Test that email addresses are anonymized."""
        message = "Error for user john.doe@example.com in file.py"
        anonymized = anonymizer._anonymize_message(message)
        assert "john.doe@example.com" not in anonymized
        assert "<email>" in anonymized


class TestTelemetryClient:
    """Tests for TelemetryClient."""

    @pytest.fixture
    def disabled_config(self) -> TelemetryConfig:
        """Create disabled telemetry config."""
        return TelemetryConfig(enabled=False)

    @pytest.fixture
    def enabled_config(self) -> TelemetryConfig:
        """Create enabled telemetry config."""
        return TelemetryConfig(
            enabled=True,
            endpoint="https://test.example.com",  # type: ignore
            timeout=5,
            batch_size=10,
            retry_attempts=2,
        )

    def test_client_disabled_is_noop(self, disabled_config: TelemetryConfig) -> None:
        """Test that disabled client has no overhead."""
        client = TelemetryClient(config=disabled_config)

        # Worker thread should not be started
        assert client._worker_thread is None

        # All tracking methods should be no-ops
        client.track_agent_usage("agent-1", "test")
        client.track_performance("test_metric", 100.0)
        client.track_error("ValueError", "test error")

        # Queue should be empty
        assert client._event_queue.empty()

    def test_client_enabled_starts_worker(
        self, enabled_config: TelemetryConfig
    ) -> None:
        """Test that enabled client starts worker thread."""
        client = TelemetryClient(config=enabled_config)

        assert client._worker_thread is not None
        assert client._worker_thread.is_alive()

        client.shutdown()

    def test_track_agent_usage(self, enabled_config: TelemetryConfig) -> None:
        """Test tracking agent usage."""
        client = TelemetryClient(config=enabled_config)

        client.track_agent_usage(
            agent_id="test-agent", operation="discover", metadata={"duration_ms": 150}
        )

        # Event should be queued
        assert not client._event_queue.empty()

        # Get event and verify structure
        event = client._event_queue.get(timeout=1.0)
        assert event["event_type"] == "agent_usage"
        assert "agent_id_hash" in event
        assert event["operation"] == "discover"
        assert "timestamp" in event

        client.shutdown()

    def test_track_performance(self, enabled_config: TelemetryConfig) -> None:
        """Test tracking performance metrics."""
        client = TelemetryClient(config=enabled_config)

        client.track_performance(
            metric_name="test_latency",
            value=123.45,
            unit="ms",
            tags={"operation": "test"},
        )

        event = client._event_queue.get(timeout=1.0)
        assert event["event_type"] == "performance"
        assert event["metric_name"] == "test_latency"
        assert event["value"] == 123.45

        client.shutdown()

    def test_track_error(self, enabled_config: TelemetryConfig) -> None:
        """Test tracking errors."""
        client = TelemetryClient(config=enabled_config)

        client.track_error(
            error_type="ValueError",
            error_message="Test error",
            stack_trace="File test.py, line 1",
            context={"retry_count": 3},
        )

        event = client._event_queue.get(timeout=1.0)
        assert event["event_type"] == "error"
        assert event["error_type"] == "ValueError"
        assert "timestamp" in event

        client.shutdown()

    @patch("telemetry.client.urlopen")
    def test_batch_sending(
        self, mock_urlopen: MagicMock, enabled_config: TelemetryConfig
    ) -> None:
        """Test that events are batched before sending."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = TelemetryClient(config=enabled_config)

        # Send multiple events
        for i in range(enabled_config.batch_size):
            client.track_agent_usage(f"agent-{i}", "test")

        # Wait for batch to be sent
        time.sleep(0.5)

        # Should have called urlopen at least once
        assert mock_urlopen.call_count >= 1

        client.shutdown()

    @patch("telemetry.client.urlopen")
    def test_graceful_failure_handling(
        self, mock_urlopen: MagicMock, enabled_config: TelemetryConfig
    ) -> None:
        """Test that network failures are handled gracefully."""
        mock_urlopen.side_effect = URLError("Network error")

        client = TelemetryClient(config=enabled_config)

        # Should not raise exception
        client.track_agent_usage("agent-1", "test")

        # Force immediate send by filling batch
        for i in range(enabled_config.batch_size):
            client.track_agent_usage(f"agent-{i}", "test")

        time.sleep(0.5)

        # Client should still be functional
        assert client.is_enabled()

        client.shutdown()

    def test_context_manager(self, enabled_config: TelemetryConfig) -> None:
        """Test using client as context manager."""
        with patch("telemetry.client.urlopen"):
            with TelemetryClient(config=enabled_config) as client:
                assert client.is_enabled()
                client.track_agent_usage("agent-1", "test")

            # Should be shutdown after exiting context
            assert client._shutdown.is_set()

    def test_track_system_info(self, enabled_config: TelemetryConfig) -> None:
        """Test tracking system information."""
        client = TelemetryClient(config=enabled_config)

        client.track_system_info()

        event = client._event_queue.get(timeout=1.0)
        assert event["event_type"] == "system_info"
        assert "platform" in event
        assert "python_version" in event
        assert "python_implementation" in event

        client.shutdown()


class TestPrivacyGuarantees:
    """Tests to validate privacy guarantees."""

    @pytest.fixture
    def client(self) -> TelemetryClient:
        """Create enabled telemetry client for testing."""
        config = TelemetryConfig(
            enabled=True,
            endpoint="https://test.example.com",  # type: ignore
        )
        return TelemetryClient(config=config)

    def test_no_user_prompts_collected(self, client: TelemetryClient) -> None:
        """Verify that user prompts are never collected."""
        # Try to track with user prompt in metadata
        client.track_agent_usage(
            "agent-1", "test", metadata={"user_prompt": "secret user input"}
        )

        event = client._event_queue.get(timeout=1.0)

        # user_prompt should be filtered out
        if "metadata" in event:
            assert "user_prompt" not in event["metadata"]

        client.shutdown()

    def test_no_code_content_collected(self, client: TelemetryClient) -> None:
        """Verify that code content is never collected."""
        client.track_agent_usage(
            "agent-1", "test", metadata={"code": "def secret(): pass"}
        )

        event = client._event_queue.get(timeout=1.0)

        # code should be filtered out
        if "metadata" in event:
            assert "code" not in event["metadata"]

        client.shutdown()

    def test_identifiers_are_hashed(self, client: TelemetryClient) -> None:
        """Verify that all identifiers are hashed."""
        client.track_agent_usage("my-agent-id", "test")

        event = client._event_queue.get(timeout=1.0)

        # Original ID should not appear
        assert "my-agent-id" not in json.dumps(event)
        # Should have hashed version
        assert "agent_id_hash" in event

        client.shutdown()

    def test_file_paths_anonymized(self, client: TelemetryClient) -> None:
        """Verify that file paths are anonymized."""
        client.track_error(
            "IOError",
            "Cannot read /home/username/secret/file.txt",
            stack_trace='File "/home/username/project/code.py", line 1',
        )

        event = client._event_queue.get(timeout=1.0)
        event_json = json.dumps(event)

        # Username should not appear
        assert "username" not in event_json
        # Full paths should not appear
        assert "/home/username" not in event_json

        client.shutdown()
