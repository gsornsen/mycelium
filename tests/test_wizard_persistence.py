"""Tests for wizard state persistence.

This module tests saving and loading wizard state to disk, ensuring
atomic writes and proper error handling.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from mycelium_onboarding.wizard.flow import WizardState, WizardStep
from mycelium_onboarding.wizard.persistence import (
    WizardStatePersistence,
)


class TestPersistenceBasics:
    """Test basic persistence operations."""

    def test_init_default_state_dir(self) -> None:
        """Test initialization with default state directory."""
        persistence = WizardStatePersistence()
        assert persistence.state_dir is not None
        assert persistence.state_file.name == "wizard_state.json"

    def test_init_custom_state_dir(self, tmp_path: Path) -> None:
        """Test initialization with custom state directory."""
        persistence = WizardStatePersistence(state_dir=tmp_path)
        assert persistence.state_dir == tmp_path
        assert persistence.state_file == tmp_path / "wizard_state.json"

    def test_exists_false_initially(self, tmp_path: Path) -> None:
        """Test exists returns False when no state saved."""
        persistence = WizardStatePersistence(state_dir=tmp_path)
        assert not persistence.exists()

    def test_get_state_path(self, tmp_path: Path) -> None:
        """Test getting state file path."""
        persistence = WizardStatePersistence(state_dir=tmp_path)
        path = persistence.get_state_path()
        assert isinstance(path, Path)
        assert path.name == "wizard_state.json"


class TestSaveAndLoad:
    """Test saving and loading wizard state."""

    def test_save_and_load_state(self, tmp_path: Path) -> None:
        """Test saving and loading wizard state."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        state = WizardState()
        state.current_step = WizardStep.SERVICES
        state.project_name = "test-project"
        state.services_enabled = {"redis": True}

        persistence.save(state)

        loaded = persistence.load()
        assert loaded is not None
        assert loaded.current_step == WizardStep.SERVICES
        assert loaded.project_name == "test-project"
        assert loaded.services_enabled == {"redis": True}
        assert loaded.resumed is True

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        """Test save creates state directory if it doesn't exist."""
        state_dir = tmp_path / "nested" / "dir"
        persistence = WizardStatePersistence(state_dir=state_dir)

        state = WizardState()
        persistence.save(state)

        assert state_dir.exists()
        assert persistence.state_file.exists()

    def test_load_nonexistent_state(self, tmp_path: Path) -> None:
        """Test loading when no state exists."""
        persistence = WizardStatePersistence(state_dir=tmp_path)
        assert persistence.load() is None

    def test_save_all_fields(self, tmp_path: Path) -> None:
        """Test saving all wizard state fields."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        state = WizardState()
        state.current_step = WizardStep.REVIEW
        state.project_name = "complete-project"
        state.services_enabled = {"redis": True, "postgres": True, "temporal": True}
        state.deployment_method = "kubernetes"
        state.redis_port = 6380
        state.postgres_port = 5433
        state.postgres_database = "custom_db"
        state.temporal_namespace = "test-namespace"
        state.temporal_ui_port = 8081
        state.temporal_frontend_port = 7234
        state.auto_start = False
        state.enable_persistence = False
        state.setup_mode = "custom"
        state.completed = True

        persistence.save(state)
        loaded = persistence.load()

        assert loaded is not None
        assert loaded.current_step == WizardStep.REVIEW
        assert loaded.project_name == "complete-project"
        assert loaded.services_enabled == {
            "redis": True,
            "postgres": True,
            "temporal": True,
        }
        assert loaded.deployment_method == "kubernetes"
        assert loaded.redis_port == 6380
        assert loaded.postgres_port == 5433
        assert loaded.postgres_database == "custom_db"
        assert loaded.temporal_namespace == "test-namespace"
        assert loaded.temporal_ui_port == 8081
        assert loaded.temporal_frontend_port == 7234
        assert loaded.auto_start is False
        assert loaded.enable_persistence is False
        assert loaded.setup_mode == "custom"
        assert loaded.completed is True
        assert loaded.resumed is True

    def test_save_preserves_timestamp(self, tmp_path: Path) -> None:
        """Test that started_at timestamp is preserved."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        original_time = datetime(2023, 10, 14, 12, 30, 45)
        state = WizardState()
        state.started_at = original_time

        persistence.save(state)
        loaded = persistence.load()

        assert loaded is not None
        assert loaded.started_at == original_time


class TestAtomicWrites:
    """Test atomic write behavior."""

    def test_save_uses_temp_file(self, tmp_path: Path) -> None:
        """Test that save uses temporary file for atomic writes."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        state = WizardState()
        persistence.save(state)

        # Temp file should be cleaned up after successful save
        temp_file = persistence.state_file.with_suffix(".tmp")
        assert not temp_file.exists()
        assert persistence.state_file.exists()

    def test_overwrite_existing_state(self, tmp_path: Path) -> None:
        """Test overwriting existing state file."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        # Save initial state
        state1 = WizardState()
        state1.project_name = "first"
        persistence.save(state1)

        # Save new state
        state2 = WizardState()
        state2.project_name = "second"
        persistence.save(state2)

        # Load should get the second state
        loaded = persistence.load()
        assert loaded is not None
        assert loaded.project_name == "second"


class TestClearState:
    """Test clearing saved state."""

    def test_clear_state(self, tmp_path: Path) -> None:
        """Test clearing saved state."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        state = WizardState()
        persistence.save(state)
        assert persistence.exists()

        persistence.clear()
        assert not persistence.exists()

    def test_clear_nonexistent_state(self, tmp_path: Path) -> None:
        """Test clearing when no state exists."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        # Should not raise error
        persistence.clear()
        assert not persistence.exists()

    def test_clear_then_load(self, tmp_path: Path) -> None:
        """Test loading after clearing returns None."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        state = WizardState()
        persistence.save(state)
        persistence.clear()

        loaded = persistence.load()
        assert loaded is None


class TestCorruptedState:
    """Test handling of corrupted state files."""

    def test_load_corrupted_json(self, tmp_path: Path) -> None:
        """Test handling of corrupted JSON file."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        # Write invalid JSON
        persistence.state_file.parent.mkdir(parents=True, exist_ok=True)
        persistence.state_file.write_text("{invalid json")

        loaded = persistence.load()
        assert loaded is None

    def test_load_missing_required_field(self, tmp_path: Path) -> None:
        """Test handling of state file missing required fields."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        # Write JSON missing current_step
        persistence.state_file.parent.mkdir(parents=True, exist_ok=True)
        persistence.state_file.write_text('{"project_name": "test"}')

        loaded = persistence.load()
        assert loaded is None

    def test_load_invalid_step_value(self, tmp_path: Path) -> None:
        """Test handling of invalid step value."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        # Write JSON with invalid step
        persistence.state_file.parent.mkdir(parents=True, exist_ok=True)
        state_dict = {"current_step": "invalid_step"}
        persistence.state_file.write_text(json.dumps(state_dict))

        loaded = persistence.load()
        assert loaded is None

    def test_load_invalid_data_types(self, tmp_path: Path) -> None:
        """Test handling of invalid data types."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        # Write JSON with wrong data types
        persistence.state_file.parent.mkdir(parents=True, exist_ok=True)
        state_dict = {
            "current_step": "welcome",
            "redis_port": "not_an_int",  # Should be int
        }
        persistence.state_file.write_text(json.dumps(state_dict))

        loaded = persistence.load()
        assert loaded is None

    def test_load_empty_file(self, tmp_path: Path) -> None:
        """Test handling of empty state file."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        # Write empty file
        persistence.state_file.parent.mkdir(parents=True, exist_ok=True)
        persistence.state_file.write_text("")

        loaded = persistence.load()
        assert loaded is None


class TestBackupAndRestore:
    """Test backup and restore functionality."""

    def test_backup_creates_file(self, tmp_path: Path) -> None:
        """Test backup creates backup file."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        state = WizardState()
        state.project_name = "test-backup"
        persistence.save(state)

        backup_path = persistence.backup()
        assert backup_path is not None
        assert backup_path.exists()
        assert "wizard_state_backup_" in backup_path.name

    def test_backup_nonexistent_state(self, tmp_path: Path) -> None:
        """Test backup when no state exists."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        backup_path = persistence.backup()
        assert backup_path is None

    def test_backup_preserves_content(self, tmp_path: Path) -> None:
        """Test backup preserves state content."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        state = WizardState()
        state.project_name = "backup-test"
        state.services_enabled = {"redis": True, "postgres": True}
        persistence.save(state)

        backup_path = persistence.backup()
        assert backup_path is not None

        # Load from backup file
        with open(backup_path) as f:
            backup_data = json.load(f)

        assert backup_data["project_name"] == "backup-test"
        assert backup_data["services_enabled"] == {"redis": True, "postgres": True}

    def test_restore_from_backup(self, tmp_path: Path) -> None:
        """Test restoring state from backup."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        # Save and backup initial state
        state = WizardState()
        state.project_name = "original"
        persistence.save(state)
        backup_path = persistence.backup()
        assert backup_path is not None

        # Clear current state
        persistence.clear()
        assert not persistence.exists()

        # Restore from backup
        persistence.restore_from_backup(backup_path)
        assert persistence.exists()

        loaded = persistence.load()
        assert loaded is not None
        assert loaded.project_name == "original"

    def test_restore_from_nonexistent_backup(self, tmp_path: Path) -> None:
        """Test restoring from nonexistent backup file."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        fake_backup = tmp_path / "nonexistent_backup.json"

        with pytest.raises(FileNotFoundError):
            persistence.restore_from_backup(fake_backup)

    def test_restore_creates_directory(self, tmp_path: Path) -> None:
        """Test restore creates state directory if needed."""
        # Create backup in one location
        persistence1 = WizardStatePersistence(state_dir=tmp_path / "original")
        state = WizardState()
        state.project_name = "test"
        persistence1.save(state)
        backup_path = persistence1.backup()
        assert backup_path is not None

        # Restore to new location
        new_dir = tmp_path / "new" / "nested" / "dir"
        persistence2 = WizardStatePersistence(state_dir=new_dir)

        persistence2.restore_from_backup(backup_path)
        assert new_dir.exists()
        assert persistence2.exists()


class TestSerializationDeserialization:
    """Test internal serialization/deserialization methods."""

    def test_serialize_state(self, tmp_path: Path) -> None:
        """Test state serialization."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        state = WizardState()
        state.project_name = "test"
        state.services_enabled = {"redis": True}

        state_dict = persistence._serialize_state(state)

        assert isinstance(state_dict, dict)
        assert state_dict["project_name"] == "test"
        assert state_dict["services_enabled"] == {"redis": True}
        assert "current_step" in state_dict
        assert "started_at" in state_dict

    def test_deserialize_state(self, tmp_path: Path) -> None:
        """Test state deserialization."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        state_dict = {
            "current_step": "services",
            "started_at": datetime.now(UTC).isoformat(),
            "project_name": "test",
            "services_enabled": {"redis": True},
            "deployment_method": "docker-compose",
            "redis_port": 6379,
            "postgres_port": 5432,
            "postgres_database": "test_db",
            "temporal_namespace": "default",
            "temporal_ui_port": 8080,
            "temporal_frontend_port": 7233,
            "auto_start": True,
            "enable_persistence": True,
            "setup_mode": "quick",
            "completed": False,
            "resumed": False,
        }

        state = persistence._deserialize_state(state_dict)

        assert isinstance(state, WizardState)
        assert state.project_name == "test"
        assert state.services_enabled == {"redis": True}
        assert state.current_step == WizardStep.SERVICES
        assert state.resumed is True  # Always marked as resumed

    def test_deserialize_missing_required_field(self, tmp_path: Path) -> None:
        """Test deserialization with missing required field."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        state_dict = {"project_name": "test"}  # Missing current_step

        with pytest.raises(ValueError, match="Missing required field"):
            persistence._deserialize_state(state_dict)

    def test_deserialize_uses_defaults(self, tmp_path: Path) -> None:
        """Test deserialization uses defaults for missing optional fields."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        state_dict = {
            "current_step": "welcome",
            # All other fields missing
        }

        state = persistence._deserialize_state(state_dict)

        assert state.project_name == ""
        assert state.redis_port == 6379
        assert state.postgres_port == 5432
        assert state.deployment_method == "docker-compose"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_save_with_empty_state(self, tmp_path: Path) -> None:
        """Test saving state with empty/default values."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        state = WizardState()
        # Leave everything at defaults

        persistence.save(state)
        loaded = persistence.load()

        assert loaded is not None
        assert loaded.current_step == WizardStep.WELCOME

    def test_multiple_saves_and_loads(self, tmp_path: Path) -> None:
        """Test multiple save/load cycles."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        for i in range(5):
            state = WizardState()
            state.project_name = f"project-{i}"
            persistence.save(state)

            loaded = persistence.load()
            assert loaded is not None
            assert loaded.project_name == f"project-{i}"

    def test_unicode_in_state(self, tmp_path: Path) -> None:
        """Test saving state with unicode characters."""
        persistence = WizardStatePersistence(state_dir=tmp_path)

        state = WizardState()
        state.project_name = "test-проект-项目"
        persistence.save(state)

        loaded = persistence.load()
        assert loaded is not None
        assert loaded.project_name == "test-проект-项目"
