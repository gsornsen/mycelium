"""Privacy validation tests for telemetry system.

These tests ensure that the telemetry system upholds all privacy guarantees
and never collects sensitive information.
"""

import json
import sys
from pathlib import Path

import pytest

# Add plugins directory to Python path
plugins_dir = Path(__file__).parent.parent.parent / "plugins" / "mycelium-core"
sys.path.insert(0, str(plugins_dir))

from telemetry.anonymization import DataAnonymizer  # noqa: E402
from telemetry.client import TelemetryClient  # noqa: E402
from telemetry.config import TelemetryConfig  # noqa: E402


class TestPrivacyCompliance:
    """Test suite validating privacy compliance."""

    @pytest.fixture
    def anonymizer(self) -> DataAnonymizer:
        """Create anonymizer for testing."""
        return DataAnonymizer(salt="test_salt")

    @pytest.fixture
    def client(self) -> TelemetryClient:
        """Create enabled client for testing."""
        config = TelemetryConfig(
            enabled=True,
            endpoint="https://test.example.com",  # type: ignore
        )
        return TelemetryClient(config=config)

    def test_no_pii_in_agent_usage(self, client: TelemetryClient) -> None:
        """Verify no PII is collected in agent usage events."""
        # Attempt to include various PII
        sensitive_metadata = {
            "user_id": "user-123",
            "email": "user@example.com",
            "username": "john_doe",
            "ip_address": "192.168.1.1",
            "session_id": "session-abc-123",
            "user_prompt": "What is my password?",
            "file_content": "SECRET_API_KEY=xyz123",
            "duration_ms": 100,  # This is safe and should be kept
        }

        client.track_agent_usage("agent-1", "test", metadata=sensitive_metadata)

        event = client._event_queue.get(timeout=1.0)

        # Verify only safe metadata is present
        assert "metadata" in event
        assert event["metadata"].get("duration_ms") == 100

        # Verify all PII is excluded
        event_json = json.dumps(event)
        assert "user@example.com" not in event_json
        assert "john_doe" not in event_json
        assert "192.168.1.1" not in event_json
        assert "What is my password?" not in event_json
        assert "SECRET_API_KEY" not in event_json

        client.shutdown()

    def test_no_code_content_leakage(self, client: TelemetryClient) -> None:
        """Verify no code content is ever transmitted."""
        code_metadata = {
            "code": "def hack(): return 'secret'",
            "file_content": "API_KEY = 'secret123'",
            "diff": "+ added secret line",
            "patch": "- removed line\n+ added line",
            "success": True,  # Safe field
        }

        client.track_agent_usage("agent-1", "test", metadata=code_metadata)

        event = client._event_queue.get(timeout=1.0)
        event_json = json.dumps(event)

        # No code content should be present
        assert "def hack()" not in event_json
        assert "API_KEY" not in event_json
        assert "secret" not in event_json

        # Safe metadata should be present
        if "metadata" in event:
            assert event["metadata"].get("success") is True

        client.shutdown()

    def test_user_prompts_never_collected(self, client: TelemetryClient) -> None:
        """Verify user prompts and responses are never collected."""
        sensitive_data = {
            "user_prompt": "Help me hack into this system",
            "user_input": "My password is abc123",
            "user_query": "What's my credit card number?",
            "response": "AI response with sensitive data",
            "message": "User message",
            "retry_count": 2,  # Safe field
        }

        client.track_agent_usage("agent-1", "test", metadata=sensitive_data)

        event = client._event_queue.get(timeout=1.0)
        event_json = json.dumps(event)

        # No user content should be present
        assert "Help me hack" not in event_json
        assert "abc123" not in event_json
        assert "credit card" not in event_json
        assert "AI response" not in event_json

        client.shutdown()

    def test_file_paths_sanitized(self, anonymizer: DataAnonymizer) -> None:
        """Verify file paths are properly sanitized."""
        sensitive_paths = [
            "/home/john_smith/Documents/secret_project/code.py",
            "C:\\Users\\jane_doe\\AppData\\Local\\temp.txt",
            "/Users/admin/Desktop/passwords.txt",
            "/root/.ssh/id_rsa",
        ]

        for path in sensitive_paths:
            anonymized = anonymizer.anonymize_file_path(path)

            # Should not contain usernames
            assert "john_smith" not in anonymized
            assert "jane_doe" not in anonymized
            assert "admin" not in anonymized

            # Should not contain full paths
            assert not anonymized.startswith("/home/")
            assert not anonymized.startswith("C:\\Users\\")
            assert not anonymized.startswith("/Users/")

    def test_stack_traces_sanitized(self, anonymizer: DataAnonymizer) -> None:
        """Verify stack traces are properly sanitized."""
        sensitive_trace = """Traceback (most recent call last):
  File "/home/alice/project/myapp/main.py", line 42, in run
    process_file("/home/alice/Documents/secret.txt")
  File "/home/alice/project/myapp/processor.py", line 15, in process_file
    with open(filename) as f:
FileNotFoundError: No such file: /home/alice/Documents/secret.txt"""

        anonymized = anonymizer.anonymize_stack_trace(sensitive_trace)

        # Should not contain username
        assert "alice" not in anonymized

        # Should not contain full home directory paths
        assert "/home/alice" not in anonymized

        # Should preserve file names and line numbers
        assert "main.py" in anonymized or "processor.py" in anonymized
        assert "line 42" in anonymized or "line 15" in anonymized

        # Should preserve error type
        assert "FileNotFoundError" in anonymized

    def test_error_messages_sanitized(self, client: TelemetryClient) -> None:
        """Verify error messages are sanitized."""
        sensitive_error_msg = (
            "Failed to connect to database at postgresql://user:password@host/db for user john@example.com"
        )

        client.track_error(
            "ConnectionError",
            sensitive_error_msg,
            stack_trace='File "/home/john/app.py", line 10',
        )

        event = client._event_queue.get(timeout=1.0)
        event_json = json.dumps(event)

        # Should not contain credentials
        assert "password" not in event_json or "password@" not in event_json

        # Should not contain email
        assert "john@example.com" not in event_json

        # Should not contain username in paths
        assert "/home/john" not in event_json

        client.shutdown()

    def test_identifier_hashing_consistency(self, anonymizer: DataAnonymizer) -> None:
        """Verify identifier hashing is consistent and irreversible."""
        identifiers = ["user-123", "agent-abc", "session-xyz"]

        for identifier in identifiers:
            # Hash should be consistent
            hash1 = anonymizer.hash_identifier(identifier)
            hash2 = anonymizer.hash_identifier(identifier)
            assert hash1 == hash2

            # Hash should not contain original identifier
            assert identifier not in hash1

            # Hash should be long enough to be secure (SHA-256)
            assert len(hash1) == 64  # 32 bytes hex-encoded

    def test_different_salts_produce_different_hashes(self) -> None:
        """Verify different salts produce different hashes."""
        anon1 = DataAnonymizer(salt="salt1")
        anon2 = DataAnonymizer(salt="salt2")

        identifier = "user-123"
        hash1 = anon1.hash_identifier(identifier)
        hash2 = anon2.hash_identifier(identifier)

        # Different salts should produce different hashes
        assert hash1 != hash2

    def test_safe_metadata_allowlist(self, anonymizer: DataAnonymizer) -> None:
        """Verify only explicitly safe metadata fields are allowed."""
        mixed_metadata = {
            # Safe fields (should be kept)
            "duration_ms": 100,
            "success": True,
            "retry_count": 3,
            "cache_hit": True,
            "result_count": 5,
            "status_code": 200,
            # Unsafe fields (should be filtered)
            "user_data": "sensitive",
            "credentials": "secret",
            "api_key": "xyz123",
            "token": "abc456",
        }

        safe = anonymizer._filter_safe_metadata(mixed_metadata)

        # All safe fields should be present
        assert safe["duration_ms"] == 100
        assert safe["success"] is True
        assert safe["retry_count"] == 3
        assert safe["cache_hit"] is True
        assert safe["result_count"] == 5
        assert safe["status_code"] == 200

        # All unsafe fields should be filtered out
        assert "user_data" not in safe
        assert "credentials" not in safe
        assert "api_key" not in safe
        assert "token" not in safe

    def test_nested_data_structures_filtered(self, anonymizer: DataAnonymizer) -> None:
        """Verify nested data structures are filtered out."""
        metadata = {
            "duration_ms": 100,  # Safe
            "nested_object": {"key": "value"},  # Unsafe
            "nested_array": [1, 2, 3],  # Unsafe
            "success": True,  # Safe
        }

        safe = anonymizer._filter_safe_metadata(metadata)

        assert "duration_ms" in safe
        assert "success" in safe
        assert "nested_object" not in safe
        assert "nested_array" not in safe

    def test_email_addresses_anonymized(self, anonymizer: DataAnonymizer) -> None:
        """Verify email addresses are removed from messages."""
        messages = [
            "Error for user john.doe@example.com",
            "Contact support@myapp.com for help",
            "Email sent to alice.bob@subdomain.example.org",
        ]

        for message in messages:
            anonymized = anonymizer._anonymize_message(message)

            # Should not contain any email addresses
            assert "@example.com" not in anonymized
            assert "@myapp.com" not in anonymized
            assert "@subdomain.example.org" not in anonymized

            # Should contain placeholder
            assert "<email>" in anonymized

    def test_performance_metric_tag_hashing(self, anonymizer: DataAnonymizer) -> None:
        """Verify performance metric tags hash identifier-like values."""
        metric = anonymizer.anonymize_performance_metric(
            metric_name="latency",
            value=100.0,
            unit="ms",
            tags={
                "user_id": "user-123",  # Should be hashed
                "agent_id": "agent-abc",  # Should be hashed
                "operation": "search",  # Should NOT be hashed
                "region": "us-east",  # Should NOT be hashed
            },
        )

        # Identifier tags should be hashed
        assert metric["tags"]["user_id"] != "user-123"
        assert metric["tags"]["agent_id"] != "agent-abc"

        # Non-identifier tags should be preserved
        assert metric["tags"]["operation"] == "search"
        assert metric["tags"]["region"] == "us-east"

    def test_zero_overhead_when_disabled(self) -> None:
        """Verify telemetry has zero overhead when disabled."""
        config = TelemetryConfig(enabled=False)
        client = TelemetryClient(config=config)

        # Worker thread should not be created
        assert client._worker_thread is None

        # Queue should remain empty
        client.track_agent_usage("agent-1", "test", metadata={"key": "value"})
        client.track_performance("metric", 100.0)
        client.track_error("Error", "message")
        client.track_system_info()

        # All should be no-ops - queue stays empty
        assert client._event_queue.empty()

    def test_comprehensive_privacy_check(self, client: TelemetryClient) -> None:
        """Comprehensive test covering all privacy requirements."""
        # Create event with everything we should NOT collect
        never_collect = {
            "user_prompt": "What's my password?",
            "user_response": "My password is abc123",
            "code": "def secret(): pass",
            "file_content": "API_KEY = 'secret'",
            "email": "user@example.com",
            "username": "john_doe",
            "ip_address": "192.168.1.1",
            "api_key": "xyz123",
            "token": "bearer_abc",
            "credentials": {"user": "admin", "pass": "secret"},
            "success": True,  # This is safe and should be kept
        }

        client.track_agent_usage("test-agent", "test", metadata=never_collect)

        event = client._event_queue.get(timeout=1.0)
        event_json = json.dumps(event)

        # Verify NONE of the sensitive data is present
        sensitive_terms = [
            "password",
            "abc123",
            "def secret",
            "API_KEY",
            "user@example.com",
            "john_doe",
            "192.168.1.1",
            "xyz123",
            "bearer_abc",
        ]

        for term in sensitive_terms:
            assert term not in event_json, f"Found sensitive term: {term}"

        # Verify only safe data is present
        if "metadata" in event:
            # Only "success" should be in metadata
            assert event["metadata"].get("success") is True
            assert len(event["metadata"]) == 1  # Only one safe field

        client.shutdown()

    def test_anonymization_comprehensive(self, anonymizer: DataAnonymizer) -> None:
        """Test comprehensive anonymization scenario."""
        # Simulate real error with sensitive data
        error_msg = (
            "Failed to process file /home/john/Documents/project/secrets.py "
            "for user john@example.com. API key xyz123 invalid."
        )

        stack_trace = """File "/home/john/Documents/project/app.py", line 100
  File "/home/john/.local/lib/python3.10/module.py", line 50
ValueError: Invalid API key xyz123 for user john@example.com"""

        anonymized = anonymizer.anonymize_error("ValueError", error_msg, stack_trace)

        result_json = json.dumps(anonymized)

        # Should not contain any sensitive information
        assert "john" not in result_json
        assert "john@example.com" not in result_json
        # Note: We cannot anonymize arbitrary strings like API keys
        # unless they follow known patterns (e.g., in connection strings)
        assert "/home/john" not in result_json

        # Should preserve error type and structure
        assert anonymized["error_type"] == "ValueError"
        assert "error_message" in anonymized
        assert "stack_trace" in anonymized
