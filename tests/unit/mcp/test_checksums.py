"""Unit tests for agent checksum integrity verification."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mycelium.mcp.checksums import (
    generate_agent_checksum,
    generate_all_checksums,
    load_checksums,
    save_checksums,
    verify_agent_checksum,
    verify_all_checksums,
)


class TestGenerateAgentChecksum:
    """Test generate_agent_checksum function."""

    def test_generate_checksum_success(self, tmp_path: Path) -> None:
        """Test generating checksum for a valid agent file."""
        agent_file = tmp_path / "test-agent.md"
        agent_file.write_text("---\nname: test\n---\nContent here")

        checksum = generate_agent_checksum(agent_file)

        assert checksum.startswith("sha256:")
        assert len(checksum) == 71  # "sha256:" (7) + 64 hex chars

    def test_generate_checksum_consistency(self, tmp_path: Path) -> None:
        """Test that same file content produces same checksum."""
        agent_file = tmp_path / "test-agent.md"
        content = "---\nname: test\n---\nContent here"
        agent_file.write_text(content)

        checksum1 = generate_agent_checksum(agent_file)
        checksum2 = generate_agent_checksum(agent_file)

        assert checksum1 == checksum2

    def test_generate_checksum_different_content(self, tmp_path: Path) -> None:
        """Test that different content produces different checksums."""
        agent1 = tmp_path / "agent1.md"
        agent2 = tmp_path / "agent2.md"

        agent1.write_text("---\nname: agent1\n---\nContent A")
        agent2.write_text("---\nname: agent2\n---\nContent B")

        checksum1 = generate_agent_checksum(agent1)
        checksum2 = generate_agent_checksum(agent2)

        assert checksum1 != checksum2

    def test_generate_checksum_file_not_found(self, tmp_path: Path) -> None:
        """Test error when agent file doesn't exist."""
        agent_file = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError, match="Agent file not found"):
            generate_agent_checksum(agent_file)

    def test_generate_checksum_not_a_file(self, tmp_path: Path) -> None:
        """Test error when path is not a file."""
        # tmp_path is a directory, not a file
        with pytest.raises(ValueError, match="not a file"):
            generate_agent_checksum(tmp_path)

    def test_generate_checksum_large_file(self, tmp_path: Path) -> None:
        """Test checksum generation for large file (tests chunked reading)."""
        agent_file = tmp_path / "large-agent.md"
        # Create a file larger than the chunk size (4096 bytes)
        large_content = "A" * 10000
        agent_file.write_text(large_content)

        checksum = generate_agent_checksum(agent_file)

        assert checksum.startswith("sha256:")
        assert len(checksum) == 71


class TestGenerateAllChecksums:
    """Test generate_all_checksums function."""

    def test_generate_all_success(self, tmp_path: Path) -> None:
        """Test generating checksums for multiple agents."""
        # Create multiple agent files
        (tmp_path / "01-core-backend-developer.md").write_text("---\nname: backend\n---\n")
        (tmp_path / "02-language-python-pro.md").write_text("---\nname: python\n---\n")
        (tmp_path / "03-specialized-data-engineer.md").write_text("---\nname: data\n---\n")

        checksums = generate_all_checksums(tmp_path)

        assert len(checksums) == 3
        assert "backend-developer" in checksums
        assert "python-pro" in checksums
        assert "data-engineer" in checksums

        # All checksums should be valid
        for checksum in checksums.values():
            assert checksum.startswith("sha256:")
            assert len(checksum) == 71

    def test_generate_all_empty_directory(self, tmp_path: Path) -> None:
        """Test generating checksums in empty directory."""
        checksums = generate_all_checksums(tmp_path)

        assert checksums == {}

    def test_generate_all_only_md_files(self, tmp_path: Path) -> None:
        """Test that only .md files are processed."""
        (tmp_path / "agent.md").write_text("---\nname: agent\n---\n")
        (tmp_path / "readme.txt").write_text("Not an agent")
        (tmp_path / "config.yaml").write_text("config: value")

        checksums = generate_all_checksums(tmp_path)

        assert len(checksums) == 1
        assert "agent" in checksums

    def test_generate_all_directory_not_found(self, tmp_path: Path) -> None:
        """Test error when plugin directory doesn't exist."""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError, match="Plugin directory not found"):
            generate_all_checksums(nonexistent)

    def test_generate_all_not_a_directory(self, tmp_path: Path) -> None:
        """Test error when path is not a directory."""
        not_a_dir = tmp_path / "file.txt"
        not_a_dir.write_text("content")

        with pytest.raises(ValueError, match="not a directory"):
            generate_all_checksums(not_a_dir)

    def test_generate_all_skips_invalid_files(self, tmp_path: Path, capsys) -> None:
        """Test that invalid files are skipped with warning."""
        # Create a valid agent
        (tmp_path / "valid.md").write_text("---\nname: valid\n---\n")

        # Create a subdirectory that will cause an error if processed
        subdir = tmp_path / "subdir.md"
        subdir.mkdir()

        checksums = generate_all_checksums(tmp_path)

        # Should have one valid checksum
        assert len(checksums) == 1
        assert "valid" in checksums

        # Should have printed warning
        captured = capsys.readouterr()
        assert "Warning:" in captured.out


class TestSaveChecksums:
    """Test save_checksums function."""

    def test_save_success(self, tmp_path: Path) -> None:
        """Test saving checksums to file."""
        checksums = {
            "agent1": "sha256:abc123",
            "agent2": "sha256:def456",
        }
        output_file = tmp_path / "checksums.json"

        save_checksums(checksums, output_file)

        assert output_file.exists()
        data = json.loads(output_file.read_text())

        assert "generated_at" in data
        assert "agents" in data
        assert data["agents"] == checksums

    def test_save_creates_parent_directory(self, tmp_path: Path) -> None:
        """Test that parent directories are created if needed."""
        checksums = {"agent": "sha256:abc123"}
        output_file = tmp_path / "subdir" / "nested" / "checksums.json"

        save_checksums(checksums, output_file)

        assert output_file.exists()
        assert output_file.parent.parent.exists()

    def test_save_overwrites_existing(self, tmp_path: Path) -> None:
        """Test that existing file is overwritten."""
        output_file = tmp_path / "checksums.json"
        output_file.write_text("old content")

        checksums = {"agent": "sha256:new123"}
        save_checksums(checksums, output_file)

        data = json.loads(output_file.read_text())
        assert data["agents"]["agent"] == "sha256:new123"

    def test_save_timestamp_format(self, tmp_path: Path) -> None:
        """Test that timestamp is in ISO format."""
        checksums = {"agent": "sha256:abc123"}
        output_file = tmp_path / "checksums.json"

        save_checksums(checksums, output_file)

        data = json.loads(output_file.read_text())
        timestamp = data["generated_at"]

        # Should be able to parse as ISO datetime
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert dt.tzinfo is not None

    def test_save_empty_checksums(self, tmp_path: Path) -> None:
        """Test saving empty checksums dict."""
        checksums: dict[str, str] = {}
        output_file = tmp_path / "checksums.json"

        save_checksums(checksums, output_file)

        data = json.loads(output_file.read_text())
        assert data["agents"] == {}


class TestLoadChecksums:
    """Test load_checksums function."""

    def test_load_success(self, tmp_path: Path) -> None:
        """Test loading checksums from file."""
        checksums_data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "agents": {
                "agent1": "sha256:abc123",
                "agent2": "sha256:def456",
            },
        }
        checksums_file = tmp_path / "checksums.json"
        checksums_file.write_text(json.dumps(checksums_data))

        checksums = load_checksums(checksums_file)

        assert len(checksums) == 2
        assert checksums["agent1"] == "sha256:abc123"
        assert checksums["agent2"] == "sha256:def456"

    def test_load_file_not_found(self, tmp_path: Path) -> None:
        """Test error when checksums file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError, match="Checksums file not found"):
            load_checksums(nonexistent)

    def test_load_invalid_json(self, tmp_path: Path) -> None:
        """Test error when file contains invalid JSON."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json {")

        with pytest.raises(ValueError, match="Invalid JSON"):
            load_checksums(invalid_file)

    def test_load_invalid_structure_not_dict(self, tmp_path: Path) -> None:
        """Test error when file doesn't contain a dict."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("[]")  # Array instead of dict

        with pytest.raises(ValueError, match="expected dict"):
            load_checksums(invalid_file)

    def test_load_missing_agents_key(self, tmp_path: Path) -> None:
        """Test error when 'agents' key is missing."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text('{"other_key": "value"}')

        with pytest.raises(ValueError, match="missing 'agents' key"):
            load_checksums(invalid_file)

    def test_load_agents_not_dict(self, tmp_path: Path) -> None:
        """Test error when 'agents' value is not a dict."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text('{"agents": ["not", "a", "dict"]}')

        with pytest.raises(ValueError, match="'agents' must be dict"):
            load_checksums(invalid_file)


class TestVerifyAgentChecksum:
    """Test verify_agent_checksum function."""

    def test_verify_success(self, tmp_path: Path) -> None:
        """Test successful checksum verification."""
        agent_file = tmp_path / "agent.md"
        agent_file.write_text("---\nname: test\n---\nContent")

        # Generate expected checksum
        expected = generate_agent_checksum(agent_file)

        # Verify should return True
        result = verify_agent_checksum("test", agent_file, expected)

        assert result is True

    def test_verify_mismatch(self, tmp_path: Path) -> None:
        """Test checksum verification fails when content changes."""
        agent_file = tmp_path / "agent.md"
        agent_file.write_text("---\nname: test\n---\nOriginal content")

        # Generate checksum
        original_checksum = generate_agent_checksum(agent_file)

        # Modify file
        agent_file.write_text("---\nname: test\n---\nModified content")

        # Verify should return False
        result = verify_agent_checksum("test", agent_file, original_checksum)

        assert result is False

    def test_verify_file_not_found(self, tmp_path: Path) -> None:
        """Test error when agent file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            verify_agent_checksum("test", nonexistent, "sha256:abc123")


class TestVerifyAllChecksums:
    """Test verify_all_checksums function."""

    def test_verify_all_success(self, tmp_path: Path) -> None:
        """Test successful verification of all agents."""
        # Create agent files
        agent1 = tmp_path / "01-core-backend-developer.md"
        agent2 = tmp_path / "02-language-python-pro.md"
        agent1.write_text("---\nname: backend\n---\n")
        agent2.write_text("---\nname: python\n---\n")

        # Generate checksums
        checksums = generate_all_checksums(tmp_path)
        checksums_file = tmp_path / "checksums.json"
        save_checksums(checksums, checksums_file)

        # Verify all
        failed = verify_all_checksums(tmp_path, checksums_file)

        assert failed == []

    def test_verify_all_detects_modified_file(self, tmp_path: Path, capsys) -> None:
        """Test detection of modified agent file."""
        # Create agent file
        agent = tmp_path / "01-core-backend-developer.md"
        agent.write_text("---\nname: backend\n---\nOriginal")

        # Generate checksums
        checksums = generate_all_checksums(tmp_path)
        checksums_file = tmp_path / "checksums.json"
        save_checksums(checksums, checksums_file)

        # Modify file
        agent.write_text("---\nname: backend\n---\nModified")

        # Verify all
        failed = verify_all_checksums(tmp_path, checksums_file)

        assert len(failed) == 1
        assert "backend-developer" in failed

        # Check warning message
        captured = capsys.readouterr()
        assert "Checksum mismatch" in captured.out

    def test_verify_all_detects_missing_file(self, tmp_path: Path, capsys) -> None:
        """Test detection of missing agent file."""
        # Create agent file
        agent = tmp_path / "01-core-backend-developer.md"
        agent.write_text("---\nname: backend\n---\n")

        # Generate checksums
        checksums = generate_all_checksums(tmp_path)
        checksums_file = tmp_path / "checksums.json"
        save_checksums(checksums, checksums_file)

        # Delete file
        agent.unlink()

        # Verify all
        failed = verify_all_checksums(tmp_path, checksums_file)

        assert len(failed) == 1
        assert "backend-developer" in failed

        # Check warning message
        captured = capsys.readouterr()
        assert "missing" in captured.out

    def test_verify_all_detects_new_agent(self, tmp_path: Path, capsys) -> None:
        """Test detection of new agent not in checksums."""
        # Create and checksum one agent
        agent1 = tmp_path / "01-core-backend-developer.md"
        agent1.write_text("---\nname: backend\n---\n")

        checksums = generate_all_checksums(tmp_path)
        checksums_file = tmp_path / "checksums.json"
        save_checksums(checksums, checksums_file)

        # Add new agent
        agent2 = tmp_path / "02-language-python-pro.md"
        agent2.write_text("---\nname: python\n---\n")

        # Verify all
        failed = verify_all_checksums(tmp_path, checksums_file)

        assert len(failed) == 1
        assert "python-pro" in failed

        # Check warning message
        captured = capsys.readouterr()
        assert "New agent detected" in captured.out

    def test_verify_all_checksums_file_not_found(self, tmp_path: Path) -> None:
        """Test error when checksums file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            verify_all_checksums(tmp_path, nonexistent)

    def test_verify_all_plugin_dir_not_found(self, tmp_path: Path) -> None:
        """Test error when plugin directory doesn't exist."""
        # Create checksums file
        checksums_file = tmp_path / "checksums.json"
        save_checksums({}, checksums_file)

        nonexistent_dir = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError):
            verify_all_checksums(nonexistent_dir, checksums_file)

    def test_verify_all_multiple_failures(self, tmp_path: Path) -> None:
        """Test detection of multiple integrity issues."""
        # Create three agents
        agent1 = tmp_path / "01-core-backend.md"
        agent2 = tmp_path / "02-language-python.md"
        agent3 = tmp_path / "03-specialized-data.md"

        agent1.write_text("---\nname: backend\n---\n")
        agent2.write_text("---\nname: python\n---\n")
        agent3.write_text("---\nname: data\n---\n")

        # Generate checksums
        checksums = generate_all_checksums(tmp_path)
        checksums_file = tmp_path / "checksums.json"
        save_checksums(checksums, checksums_file)

        # Modify agent1
        agent1.write_text("---\nname: backend\n---\nModified")

        # Delete agent2
        agent2.unlink()

        # Add new agent4
        agent4 = tmp_path / "04-developer-new.md"
        agent4.write_text("---\nname: new\n---\n")

        # Verify all - should detect 3 failures
        failed = verify_all_checksums(tmp_path, checksums_file)

        assert len(failed) == 3
        assert "backend" in failed
        assert "python" in failed
        assert "new" in failed
