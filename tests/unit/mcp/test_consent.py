"""Tests for user consent management.

This module tests the ConsentManager and ConsentRecord classes,
including consent persistence, checksum validation, and CLI prompts.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from mycelium.mcp.consent import ConsentManager, ConsentRecord


class TestConsentRecord:
    """Test ConsentRecord dataclass."""

    def test_create_record(self):
        """Test creating a consent record."""
        record = ConsentRecord(
            agent_name="test-agent", checksum="sha256:abc123", risk_level="high", granted_at="2025-01-01T00:00:00Z"
        )
        assert record.agent_name == "test-agent"
        assert record.checksum == "sha256:abc123"
        assert record.risk_level == "high"
        assert record.granted_at == "2025-01-01T00:00:00Z"
        assert record.expires_at is None

    def test_create_record_with_expiration(self):
        """Test creating a consent record with expiration."""
        record = ConsentRecord(
            agent_name="test-agent",
            checksum="sha256:abc123",
            risk_level="medium",
            granted_at="2025-01-01T00:00:00Z",
            expires_at="2025-12-31T23:59:59Z",
        )
        assert record.expires_at == "2025-12-31T23:59:59Z"


class TestConsentManager:
    """Test ConsentManager class."""

    @pytest.fixture
    def temp_consent_file(self, tmp_path):
        """Create a temporary consent file path."""
        return tmp_path / "agent_consents.json"

    @pytest.fixture
    def manager(self, temp_consent_file):
        """Create a ConsentManager with temp file."""
        return ConsentManager(consent_file=temp_consent_file)

    @pytest.fixture
    def mock_agent_file(self, tmp_path):
        """Create a mock agent file for testing."""
        agent_file = tmp_path / "test-agent.md"
        agent_file.write_text("# Test Agent\nThis is a test agent.")
        return agent_file

    def test_init_default_path(self):
        """Test initialization with default consent file path."""
        manager = ConsentManager()
        expected_path = Path.home() / ".mycelium" / "agent_consents.json"
        assert manager.consent_file == expected_path

    def test_init_custom_path(self, temp_consent_file):
        """Test initialization with custom consent file path."""
        manager = ConsentManager(consent_file=temp_consent_file)
        assert manager.consent_file == temp_consent_file

    def test_grant_consent(self, manager, mock_agent_file, temp_consent_file):
        """Test granting consent for an agent."""
        manager.grant_consent("test-agent", mock_agent_file, "high")

        # Verify consent was saved
        assert temp_consent_file.exists()

        # Load and verify content
        with temp_consent_file.open() as f:
            data = json.load(f)

        assert "test-agent" in data
        record = data["test-agent"]
        assert record["agent_name"] == "test-agent"
        assert record["risk_level"] == "high"
        assert record["checksum"].startswith("sha256:")
        assert "granted_at" in record

    def test_grant_consent_multiple_agents(self, manager, tmp_path, temp_consent_file):
        """Test granting consent for multiple agents."""
        agent1 = tmp_path / "agent1.md"
        agent1.write_text("Agent 1 content")
        agent2 = tmp_path / "agent2.md"
        agent2.write_text("Agent 2 content")

        manager.grant_consent("agent1", agent1, "high")
        manager.grant_consent("agent2", agent2, "medium")

        # Load and verify both consents
        with temp_consent_file.open() as f:
            data = json.load(f)

        assert "agent1" in data
        assert "agent2" in data
        assert data["agent1"]["risk_level"] == "high"
        assert data["agent2"]["risk_level"] == "medium"

    def test_check_consent_not_granted(self, manager, mock_agent_file):
        """Test checking consent that was never granted."""
        result = manager.check_consent("test-agent", mock_agent_file, "high")
        assert result is False

    def test_check_consent_granted_valid(self, manager, mock_agent_file):
        """Test checking valid consent."""
        # Grant consent first
        manager.grant_consent("test-agent", mock_agent_file, "high")

        # Check consent
        result = manager.check_consent("test-agent", mock_agent_file, "high")
        assert result is True

    def test_check_consent_checksum_mismatch(self, manager, mock_agent_file):
        """Test that consent is invalid when file changes (checksum mismatch)."""
        # Grant consent
        manager.grant_consent("test-agent", mock_agent_file, "high")

        # Modify the agent file
        mock_agent_file.write_text("# Modified Agent\nContent changed!")

        # Check consent - should fail due to checksum mismatch
        result = manager.check_consent("test-agent", mock_agent_file, "high")
        assert result is False

    def test_check_consent_expired(self, manager, mock_agent_file, temp_consent_file):
        """Test checking expired consent."""
        # Create expired consent manually
        checksum = "sha256:abc123"
        past_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        expired_record = ConsentRecord(
            agent_name="test-agent",
            checksum=checksum,
            risk_level="high",
            granted_at=past_time,
            expires_at=past_time,  # Already expired
        )

        # Save to file
        consents = {"test-agent": expired_record}
        manager._save_consents(consents)

        # Check consent - should fail due to expiration
        result = manager.check_consent("test-agent", mock_agent_file, "high")
        assert result is False

    def test_check_consent_not_expired(self, manager, mock_agent_file, temp_consent_file):
        """Test checking non-expired consent."""
        # Grant consent
        manager.grant_consent("test-agent", mock_agent_file, "high")

        # Load and add future expiration
        consents = manager._load_consents()
        future_time = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        consents["test-agent"].expires_at = future_time
        manager._save_consents(consents)

        # Check consent - should pass
        result = manager.check_consent("test-agent", mock_agent_file, "high")
        assert result is True

    def test_revoke_consent(self, manager, mock_agent_file, temp_consent_file):
        """Test revoking consent."""
        # Grant consent first
        manager.grant_consent("test-agent", mock_agent_file, "high")
        assert manager.check_consent("test-agent", mock_agent_file, "high")

        # Revoke consent
        manager.revoke_consent("test-agent")

        # Verify consent is removed
        result = manager.check_consent("test-agent", mock_agent_file, "high")
        assert result is False

        # Verify file doesn't contain the agent
        with temp_consent_file.open() as f:
            data = json.load(f)
        assert "test-agent" not in data

    def test_revoke_consent_nonexistent(self, manager):
        """Test revoking consent that doesn't exist (should not error)."""
        # Should not raise an error
        manager.revoke_consent("nonexistent-agent")

    def test_list_consents_empty(self, manager):
        """Test listing consents when none exist."""
        consents = manager.list_consents()
        assert consents == []

    def test_list_consents_multiple(self, manager, tmp_path):
        """Test listing multiple consents."""
        agent1 = tmp_path / "agent1.md"
        agent1.write_text("Agent 1")
        agent2 = tmp_path / "agent2.md"
        agent2.write_text("Agent 2")

        manager.grant_consent("agent1", agent1, "high")
        manager.grant_consent("agent2", agent2, "medium")

        consents = manager.list_consents()
        assert len(consents) == 2

        agent_names = {c.agent_name for c in consents}
        assert "agent1" in agent_names
        assert "agent2" in agent_names

    def test_load_consents_no_file(self, manager):
        """Test loading consents when file doesn't exist."""
        consents = manager._load_consents()
        assert consents == {}

    def test_load_consents_valid_file(self, manager, temp_consent_file):
        """Test loading consents from valid file."""
        # Create valid consent file
        data = {
            "test-agent": {
                "agent_name": "test-agent",
                "checksum": "sha256:abc123",
                "risk_level": "high",
                "granted_at": "2025-01-01T00:00:00Z",
            }
        }
        with temp_consent_file.open("w") as f:
            json.dump(data, f)

        # Load consents
        consents = manager._load_consents()
        assert len(consents) == 1
        assert "test-agent" in consents
        assert consents["test-agent"].agent_name == "test-agent"

    def test_load_consents_corrupted_file(self, manager, temp_consent_file):
        """Test loading consents from corrupted JSON file."""
        # Create corrupted file
        temp_consent_file.write_text("{invalid json")

        # Should return empty dict on corrupted file
        consents = manager._load_consents()
        assert consents == {}

    def test_load_consents_invalid_structure(self, manager, temp_consent_file):
        """Test loading consents with invalid data structure."""
        # Create file with invalid structure (not a dict at top level)
        data = ["not", "a", "dict"]
        with temp_consent_file.open("w") as f:
            json.dump(data, f)

        # Should return empty dict on invalid structure
        consents = manager._load_consents()
        assert consents == {}

    def test_save_consents(self, manager, temp_consent_file):
        """Test saving consents to file."""
        record = ConsentRecord(
            agent_name="test-agent", checksum="sha256:abc123", risk_level="high", granted_at="2025-01-01T00:00:00Z"
        )
        consents = {"test-agent": record}

        manager._save_consents(consents)

        # Verify file was created
        assert temp_consent_file.exists()

        # Verify content
        with temp_consent_file.open() as f:
            data = json.load(f)

        assert "test-agent" in data
        assert data["test-agent"]["agent_name"] == "test-agent"

    @patch("builtins.input")
    def test_request_consent_granted_yes(self, mock_input, manager, mock_agent_file):
        """Test requesting consent with 'yes' response."""
        mock_input.return_value = "yes"

        result = manager.request_consent("test-agent", mock_agent_file, "high", ["Bash(*)", "Write(*)"])

        assert result is True
        assert mock_input.called

        # Verify consent was saved
        assert manager.check_consent("test-agent", mock_agent_file, "high")

    @patch("builtins.input")
    def test_request_consent_granted_y(self, mock_input, manager, mock_agent_file):
        """Test requesting consent with 'y' response."""
        mock_input.return_value = "y"

        result = manager.request_consent("test-agent", mock_agent_file, "high", ["Bash(*)"])

        assert result is True

    @patch("builtins.input")
    def test_request_consent_denied_no(self, mock_input, manager, mock_agent_file):
        """Test requesting consent with 'no' response."""
        mock_input.return_value = "no"

        result = manager.request_consent("test-agent", mock_agent_file, "high", ["Bash(*)"])

        assert result is False

        # Verify consent was not saved
        assert not manager.check_consent("test-agent", mock_agent_file, "high")

    @patch("builtins.input")
    def test_request_consent_denied_invalid(self, mock_input, manager, mock_agent_file):
        """Test requesting consent with invalid response (defaults to deny)."""
        mock_input.return_value = "maybe"

        result = manager.request_consent("test-agent", mock_agent_file, "high", ["Bash(*)"])

        assert result is False

    @patch("builtins.input")
    def test_request_consent_interrupted(self, mock_input, manager, mock_agent_file):
        """Test requesting consent with keyboard interrupt."""
        mock_input.side_effect = KeyboardInterrupt()

        result = manager.request_consent("test-agent", mock_agent_file, "high", ["Bash(*)"])

        assert result is False

    @patch("builtins.input")
    def test_request_consent_eof(self, mock_input, manager, mock_agent_file):
        """Test requesting consent with EOF error."""
        mock_input.side_effect = EOFError()

        result = manager.request_consent("test-agent", mock_agent_file, "high", ["Bash(*)"])

        assert result is False

    @patch("builtins.print")
    @patch("builtins.input")
    def test_request_consent_high_risk_warning(self, mock_input, mock_print, manager, mock_agent_file):
        """Test that high-risk warning is displayed."""
        mock_input.return_value = "yes"

        manager.request_consent("test-agent", mock_agent_file, "high", ["Bash(*)", "Write(*)"])

        # Verify warning was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("SECURITY WARNING" in str(call) for call in print_calls)
        assert any("HIGH" in str(call) for call in print_calls)

    @patch("builtins.print")
    @patch("builtins.input")
    def test_request_consent_medium_risk_warning(self, mock_input, mock_print, manager, mock_agent_file):
        """Test that medium-risk warning is displayed."""
        mock_input.return_value = "yes"

        manager.request_consent("test-agent", mock_agent_file, "medium", ["Read(*)"])

        # Verify warning was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("MEDIUM" in str(call) for call in print_calls)

    @patch("builtins.print")
    @patch("builtins.input")
    def test_request_consent_low_risk_warning(self, mock_input, mock_print, manager, mock_agent_file):
        """Test that low-risk warning is displayed."""
        mock_input.return_value = "yes"

        manager.request_consent("test-agent", mock_agent_file, "low", ["Read"])

        # Verify warning was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("LOW" in str(call) for call in print_calls)

    def test_check_consent_file_not_found(self, manager, tmp_path):
        """Test checking consent when agent file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.md"

        result = manager.check_consent("test-agent", nonexistent, "high")
        assert result is False

    def test_grant_consent_preserves_existing(self, manager, tmp_path):
        """Test that granting consent preserves existing consents."""
        agent1 = tmp_path / "agent1.md"
        agent1.write_text("Agent 1")
        agent2 = tmp_path / "agent2.md"
        agent2.write_text("Agent 2")

        # Grant consent for agent1
        manager.grant_consent("agent1", agent1, "high")

        # Grant consent for agent2
        manager.grant_consent("agent2", agent2, "medium")

        # Verify both exist
        consents = manager._load_consents()
        assert "agent1" in consents
        assert "agent2" in consents
