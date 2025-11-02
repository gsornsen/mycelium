"""Unit tests for telemetry functionality."""

import json
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add plugins directory to Python path
plugins_dir = Path(__file__).parent.parent.parent / "plugins" / "mycelium-core"
sys.path.insert(0, str(plugins_dir))

from telemetry.anonymization import DataAnonymizer  # noqa: E402
from telemetry.client import TelemetryClient  # noqa: E402
from telemetry.config import TelemetryConfig  # noqa: E402


class TestTelemetryConfig:
    """Tests for TelemetryConfig."""

    def test_default_config_disabled(self) -> None:
        """Test that telemetry is disabled by default."""
        config = TelemetryConfig()
        assert config.enabled is False
        assert config.is_enabled() is False

    def test_config_from_dict(self) -> None:
        """Test configuration from dictionary."""
        config_dict = {
            "enabled": True,
            "api_endpoint": "https://telemetry.example.com",
            "device_id": str(uuid.uuid4()),
            "consent_given": True,
        }
        config = TelemetryConfig(**config_dict)
        assert config.enabled is True
        assert config.is_enabled() is True
        assert config.api_endpoint == "https://telemetry.example.com"
        assert config.consent_given is True

    def test_config_persistence(self, tmp_path: Path) -> None:
        """Test that configuration persists to file."""
        config_file = tmp_path / "telemetry.json"
        config = TelemetryConfig(
            enabled=True,
            consent_given=True,
            config_path=config_file,
        )

        # Save configuration
        config.save()
        assert config_file.exists()

        # Load configuration
        loaded_config = TelemetryConfig.load(config_file)
        assert loaded_config.enabled is True
        assert loaded_config.consent_given is True
        assert loaded_config.device_id == config.device_id

    def test_is_enabled_requires_consent(self) -> None:
        """Test that is_enabled requires both enabled and consent."""
        config = TelemetryConfig(enabled=True, consent_given=False)
        assert config.is_enabled() is False

        config = TelemetryConfig(enabled=False, consent_given=True)
        assert config.is_enabled() is False

        config = TelemetryConfig(enabled=True, consent_given=True)
        assert config.is_enabled() is True


class TestDataAnonymizer:
    """Tests for DataAnonymizer."""

    def test_hash_string(self) -> None:
        """Test string hashing."""
        anonymizer = DataAnonymizer()
        hashed = anonymizer.hash_string("test_value")
        assert hashed != "test_value"
        assert len(hashed) == 64  # SHA256 hex digest length
        # Consistent hashing
        assert anonymizer.hash_string("test_value") == hashed

    def test_hash_with_salt(self) -> None:
        """Test hashing with salt."""
        anonymizer1 = DataAnonymizer(salt="salt1")
        anonymizer2 = DataAnonymizer(salt="salt2")
        hash1 = anonymizer1.hash_string("test")
        hash2 = anonymizer2.hash_string("test")
        assert hash1 != hash2

    def test_anonymize_paths(self) -> None:
        """Test path anonymization."""
        anonymizer = DataAnonymizer()
        test_path = "/home/user/project/file.py"
        anonymized = anonymizer.anonymize_path(test_path)
        assert "/home/user" not in anonymized
        assert "file.py" in anonymized  # Filename preserved

    def test_anonymize_data_structure(self) -> None:
        """Test anonymization of nested data structures."""
        anonymizer = DataAnonymizer()
        data = {
            "user": "john.doe",
            "email": "john@example.com",
            "path": "/home/john/project",
            "stats": {"count": 10, "duration": 1.5},
        }

        anonymized = anonymizer.anonymize_data(data, fields_to_hash=["user", "email"])
        assert anonymized["user"] != "john.doe"
        assert anonymized["email"] != "john@example.com"
        assert anonymized["stats"]["count"] == 10
        assert anonymized["stats"]["duration"] == 1.5

    def test_remove_sensitive_fields(self) -> None:
        """Test removal of sensitive fields."""
        anonymizer = DataAnonymizer()
        data = {
            "api_key": "secret_key",
            "password": "secret_pass",
            "token": "auth_token",
            "safe_field": "safe_value",
        }

        cleaned = anonymizer.remove_sensitive_fields(data)
        assert "api_key" not in cleaned
        assert "password" not in cleaned
        assert "token" not in cleaned
        assert cleaned["safe_field"] == "safe_value"


class TestTelemetryClient:
    """Tests for TelemetryClient."""

    def test_client_disabled_by_default(self) -> None:
        """Test that client doesn't send when disabled."""
        config = TelemetryConfig(enabled=False)
        client = TelemetryClient(config)

        with patch("requests.post") as mock_post:
            client.track_event("test_event", {"key": "value"})
            mock_post.assert_not_called()

    def test_client_respects_consent(self) -> None:
        """Test that client respects consent."""
        config = TelemetryConfig(enabled=True, consent_given=False)
        client = TelemetryClient(config)

        with patch("requests.post") as mock_post:
            client.track_event("test_event", {"key": "value"})
            mock_post.assert_not_called()

    @patch("requests.post")
    def test_client_sends_events(self, mock_post: MagicMock) -> None:
        """Test that client sends events when enabled."""
        config = TelemetryConfig(enabled=True, consent_given=True)
        client = TelemetryClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client.track_event("test_event", {"key": "value"})
        mock_post.assert_called_once()

        # Check payload structure
        call_args = mock_post.call_args
        payload = json.loads(call_args[1]["data"])
        assert payload["event"] == "test_event"
        assert payload["properties"]["key"] == "value"
        assert "timestamp" in payload
        assert "device_id" in payload

    @patch("requests.post")
    def test_client_anonymizes_data(self, mock_post: MagicMock) -> None:
        """Test that client anonymizes sensitive data."""
        config = TelemetryConfig(enabled=True, consent_given=True)
        client = TelemetryClient(config, anonymize=True)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client.track_event(
            "test_event",
            {"user_id": "john.doe", "file_path": "/home/john/project/file.py"},
        )

        call_args = mock_post.call_args
        payload = json.loads(call_args[1]["data"])
        properties = payload["properties"]

        # User ID should be hashed
        assert properties["user_id"] != "john.doe"
        assert len(properties["user_id"]) == 64  # SHA256 hash

        # Path should be partially anonymized
        assert "/home/john" not in properties["file_path"]

    @patch("requests.post")
    def test_client_batch_events(self, mock_post: MagicMock) -> None:
        """Test batching of events."""
        config = TelemetryConfig(enabled=True, consent_given=True, batch_size=2)
        client = TelemetryClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Send 3 events, should trigger 1 batch send
        client.track_event("event1", {"key": "value1"})
        client.track_event("event2", {"key": "value2"})
        client.track_event("event3", {"key": "value3"})

        # Force flush remaining
        client.flush()

        # Should have made 2 calls (batch of 2 + remaining 1)
        assert mock_post.call_count == 2

    def test_client_handles_errors_gracefully(self) -> None:
        """Test that client handles errors without crashing."""
        config = TelemetryConfig(enabled=True, consent_given=True)
        client = TelemetryClient(config)

        with patch("requests.post") as mock_post:
            # Simulate network error
            mock_post.side_effect = Exception("Network error")

            # Should not raise exception
            client.track_event("test_event", {"key": "value"})

    def test_client_respects_opt_out(self, tmp_path: Path) -> None:
        """Test that client respects opt-out."""
        config_file = tmp_path / "telemetry.json"
        config = TelemetryConfig(
            enabled=True,
            consent_given=True,
            config_path=config_file,
        )
        client = TelemetryClient(config)

        # Opt out
        client.opt_out()
        assert config.enabled is False
        assert config.consent_given is False

        # Verify persistence
        loaded_config = TelemetryConfig.load(config_file)
        assert loaded_config.enabled is False
        assert loaded_config.consent_given is False

    def test_performance_metrics(self) -> None:
        """Test performance metric tracking."""
        config = TelemetryConfig(enabled=True, consent_given=True)
        client = TelemetryClient(config)

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            # Track performance metric
            client.track_performance(
                operation="database_query",
                duration_ms=150.5,
                metadata={"query_type": "SELECT"},
            )

            call_args = mock_post.call_args
            payload = json.loads(call_args[1]["data"])
            assert payload["event"] == "performance"
            assert payload["properties"]["operation"] == "database_query"
            assert payload["properties"]["duration_ms"] == 150.5
            assert payload["properties"]["query_type"] == "SELECT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
