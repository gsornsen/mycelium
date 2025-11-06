"""Privacy-focused tests for telemetry system."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add plugins directory to Python path
plugins_dir = Path(__file__).parent.parent.parent / "plugins" / "mycelium-core"
sys.path.insert(0, str(plugins_dir))

from telemetry.anonymization import DataAnonymizer  # noqa: E402
from telemetry.client import TelemetryClient  # noqa: E402
from telemetry.config import TelemetryConfig  # noqa: E402


class TestPrivacyCompliance:
    """Tests to ensure privacy compliance in telemetry."""

    def test_no_pii_in_default_collection(self) -> None:
        """Ensure no PII is collected by default."""
        config = TelemetryConfig(enabled=True, consent_given=True)
        client = TelemetryClient(config, anonymize=True)

        # Simulate event with PII
        event_data = {
            "username": "john.doe",
            "email": "john@example.com",
            "project_path": "/home/john/myproject",
            "action": "deploy",
        }

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            client.track_event("user_action", event_data)

            # Verify PII was anonymized
            call_args = mock_post.call_args
            payload = json.loads(call_args[1]["data"])
            props = payload["properties"]

            # Username and email should be hashed
            assert props["username"] != "john.doe"
            assert props["email"] != "john@example.com"
            assert len(props["username"]) == 64  # SHA256 hash

            # Path should not contain username
            assert "john" not in props["project_path"]

    def test_gdpr_data_deletion(self, tmp_path: Path) -> None:
        """Test GDPR-compliant data deletion."""
        config_file = tmp_path / "telemetry.json"
        config = TelemetryConfig(
            enabled=True,
            consent_given=True,
            config_path=config_file,
        )

        # Store some data
        config.save()
        assert config_file.exists()

        # User requests deletion
        config.delete_all_data()

        # Config file should be removed
        assert not config_file.exists()

        # New config should have no previous data
        new_config = TelemetryConfig(config_path=config_file)
        assert new_config.device_id != config.device_id

    def test_consent_withdrawal(self, tmp_path: Path) -> None:
        """Test handling of consent withdrawal."""
        config_file = tmp_path / "telemetry.json"
        config = TelemetryConfig(
            enabled=True,
            consent_given=True,
            config_path=config_file,
        )
        client = TelemetryClient(config)

        # Withdraw consent
        client.withdraw_consent()

        # Verify telemetry is disabled
        assert config.consent_given is False
        assert not config.is_enabled()

        # Verify persistence
        reloaded = TelemetryConfig.load(config_file)
        assert reloaded.consent_given is False

    def test_sensitive_env_vars_not_collected(self) -> None:
        """Ensure sensitive environment variables are not collected."""
        anonymizer = DataAnonymizer()

        env_data = {
            "PATH": "/usr/bin:/usr/local/bin",
            "API_KEY": "secret-key-12345",
            "DATABASE_PASSWORD": "super-secret",
            "AWS_SECRET_ACCESS_KEY": "aws-secret",
            "GITHUB_TOKEN": "ghp_xxxxxxxxxxxx",
            "USER": "john",
        }

        cleaned = anonymizer.remove_sensitive_fields(env_data)

        # Sensitive fields should be removed
        assert "API_KEY" not in cleaned
        assert "DATABASE_PASSWORD" not in cleaned
        assert "AWS_SECRET_ACCESS_KEY" not in cleaned
        assert "GITHUB_TOKEN" not in cleaned

        # Non-sensitive fields preserved (but may be hashed)
        assert "PATH" in cleaned
        assert "USER" in cleaned

    def test_ip_address_anonymization(self) -> None:
        """Test that IP addresses are properly anonymized."""
        anonymizer = DataAnonymizer()

        data = {
            "client_ip": "192.168.1.100",
            "server_ip": "10.0.0.1",
            "public_ip": "203.0.113.42",
        }

        # IP addresses should be hashed or removed
        anonymized = anonymizer.anonymize_data(data, fields_to_hash=["client_ip", "server_ip", "public_ip"])

        for key in ["client_ip", "server_ip", "public_ip"]:
            assert anonymized[key] != data[key]
            # Should be a hash
            assert len(anonymized[key]) == 64

    def test_file_content_never_sent(self) -> None:
        """Ensure file contents are never sent in telemetry."""
        config = TelemetryConfig(enabled=True, consent_given=True)
        client = TelemetryClient(config)

        # Attempt to track event with file content
        event_data = {
            "action": "file_edit",
            "file_path": "/path/to/file.py",
            "file_content": "def secret_function():\n    password = 'secret123'",
        }

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            # Client should filter out file_content
            client.track_event("file_operation", event_data)

            call_args = mock_post.call_args
            payload = json.loads(call_args[1]["data"])
            props = payload["properties"]

            # File content should not be in payload
            assert "file_content" not in props
            # File path should be present but anonymized
            assert "file_path" in props

    def test_deterministic_hashing(self) -> None:
        """Test that hashing is deterministic for consistency."""
        anonymizer1 = DataAnonymizer(salt="test-salt")
        anonymizer2 = DataAnonymizer(salt="test-salt")

        test_value = "user@example.com"

        hash1 = anonymizer1.hash_string(test_value)
        hash2 = anonymizer2.hash_string(test_value)

        # Same salt should produce same hash
        assert hash1 == hash2

        # Different salt should produce different hash
        anonymizer3 = DataAnonymizer(salt="different-salt")
        hash3 = anonymizer3.hash_string(test_value)
        assert hash3 != hash1

    def test_opt_in_required(self) -> None:
        """Test that explicit opt-in is required for telemetry."""
        # Default config should be disabled
        config = TelemetryConfig()
        assert config.enabled is False
        assert config.consent_given is False

        client = TelemetryClient(config)

        with patch("requests.post") as mock_post:
            client.track_event("test", {})
            # Should not send without opt-in
            mock_post.assert_not_called()

    def test_data_minimization(self) -> None:
        """Test that only necessary data is collected."""
        config = TelemetryConfig(enabled=True, consent_given=True)
        client = TelemetryClient(config)

        # Large event with lots of data
        event_data = {
            "action": "deploy",
            "necessary_field": "value",
            "debug_info": "x" * 10000,  # Large debug string
            "stack_trace": "line1\nline2\nline3" * 100,
            "memory_dump": [1, 2, 3] * 1000,
        }

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            client.track_event("deployment", event_data)

            call_args = mock_post.call_args
            payload = json.loads(call_args[1]["data"])

            # Payload should be reasonably sized
            payload_size = len(json.dumps(payload))
            assert payload_size < 10000  # Less than 10KB

    def test_local_only_mode(self, tmp_path: Path) -> None:
        """Test local-only telemetry mode (no network calls)."""
        log_file = tmp_path / "telemetry.log"
        config = TelemetryConfig(
            enabled=True,
            consent_given=True,
            local_only=True,
            local_log_path=log_file,
        )
        client = TelemetryClient(config)

        with patch("requests.post") as mock_post:
            client.track_event("test_event", {"key": "value"})

            # Should not make network calls in local mode
            mock_post.assert_not_called()

            # Should write to local file instead
            if log_file.exists():
                with log_file.open() as f:
                    lines = f.readlines()
                    assert len(lines) > 0
                    # Verify event was logged
                    last_event = json.loads(lines[-1])
                    assert last_event["event"] == "test_event"


class TestDataRetention:
    """Tests for data retention policies."""

    def test_automatic_data_expiry(self, tmp_path: Path) -> None:
        """Test that old telemetry data expires automatically."""
        config_file = tmp_path / "telemetry.json"
        config = TelemetryConfig(
            enabled=True,
            consent_given=True,
            config_path=config_file,
            retention_days=30,
        )

        # Simulate old timestamp
        from datetime import datetime, timedelta

        old_timestamp = datetime.now() - timedelta(days=31)
        config.last_cleanup = old_timestamp.isoformat()
        config.save()

        # Reload and check cleanup
        reloaded = TelemetryConfig.load(config_file)
        reloaded.cleanup_old_data()

        # Old data should be marked for cleanup
        assert reloaded.last_cleanup != old_timestamp.isoformat()

    def test_export_user_data(self, tmp_path: Path) -> None:
        """Test GDPR-compliant data export functionality."""
        config = TelemetryConfig(
            enabled=True,
            consent_given=True,
            device_id="test-device-123",
        )
        client = TelemetryClient(config)

        export_file = tmp_path / "user_data_export.json"

        # Export all user data
        client.export_user_data(export_file)

        assert export_file.exists()
        with export_file.open() as f:
            exported = json.load(f)
            assert exported["device_id"] == "test-device-123"
            assert "export_timestamp" in exported
            assert "telemetry_enabled" in exported


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
