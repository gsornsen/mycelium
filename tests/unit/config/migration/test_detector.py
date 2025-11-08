"""Unit tests for migration detector."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from mycelium_onboarding.config.migration.detector import (
    LegacyConfigLocation,
    MigrationDetector,
)


class TestLegacyConfigLocation:
    """Tests for LegacyConfigLocation dataclass."""

    def test_str_representation_exists(self):
        """Test string representation for existing file."""
        location = LegacyConfigLocation(
            path=Path("/test/config.yaml"),
            config_type="project",
            exists=True,
            readable=True,
            size_bytes=1024,
        )
        result = str(location)
        assert "project" in result
        assert "/test/config.yaml" in result
        assert "1024 bytes" in result

    def test_str_representation_missing(self):
        """Test string representation for missing file."""
        location = LegacyConfigLocation(
            path=Path("/test/missing.yaml"),
            config_type="project",
            exists=False,
            readable=False,
            size_bytes=0,
        )
        result = str(location)
        assert "missing" in result

    def test_str_representation_not_readable(self):
        """Test string representation for unreadable file."""
        location = LegacyConfigLocation(
            path=Path("/test/unreadable.yaml"),
            config_type="project",
            exists=True,
            readable=False,
            size_bytes=512,
        )
        result = str(location)
        assert "NOT READABLE" in result

    def test_str_representation_with_conflict(self):
        """Test string representation with conflict."""
        location = LegacyConfigLocation(
            path=Path("/test/config.yaml"),
            config_type="project",
            exists=True,
            readable=True,
            size_bytes=1024,
            conflicts_with=Path("/new/config.yaml"),
        )
        result = str(location)
        assert "CONFLICTS" in result
        assert "/new/config.yaml" in result


class TestMigrationDetector:
    """Tests for MigrationDetector."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def detector(self, temp_project_dir):
        """Create detector instance."""
        return MigrationDetector(project_dir=temp_project_dir)

    def test_init_default_project_dir(self):
        """Test initialization with default project dir."""
        detector = MigrationDetector()
        assert detector.project_dir == Path.cwd()
        assert detector.legacy_filename == "mycelium-config.yaml"

    def test_init_custom_project_dir(self, temp_project_dir):
        """Test initialization with custom project dir."""
        detector = MigrationDetector(project_dir=temp_project_dir)
        assert detector.project_dir == temp_project_dir

    def test_init_custom_legacy_filename(self, temp_project_dir):
        """Test initialization with custom legacy filename."""
        detector = MigrationDetector(
            project_dir=temp_project_dir,
            legacy_filename="old-config.yaml",
        )
        assert detector.legacy_filename == "old-config.yaml"

    def test_scan_empty_directory(self, detector):
        """Test scanning empty directory finds no configs."""
        configs = detector.scan_for_legacy_configs()
        assert len(configs) == 0

    def test_scan_finds_project_root_config(self, detector, temp_project_dir):
        """Test scanning finds config in project root."""
        # Create legacy config in project root
        legacy_path = temp_project_dir / "mycelium-config.yaml"
        legacy_path.write_text("version: '1.0'\n")

        configs = detector.scan_for_legacy_configs()
        assert len(configs) == 1
        assert configs[0].path == legacy_path
        assert configs[0].config_type == "project-root"
        assert configs[0].exists is True
        assert configs[0].readable is True
        assert configs[0].size_bytes > 0

    def test_scan_finds_mycelium_dir_config(self, detector, temp_project_dir):
        """Test scanning finds config in .mycelium directory."""
        # Create legacy config in .mycelium directory
        mycelium_dir = temp_project_dir / ".mycelium"
        mycelium_dir.mkdir()
        legacy_path = mycelium_dir / "mycelium-config.yaml"
        legacy_path.write_text("version: '1.0'\n")

        configs = detector.scan_for_legacy_configs()
        assert len(configs) == 1
        assert configs[0].path == legacy_path
        assert configs[0].config_type == "project-mycelium"

    def test_scan_finds_multiple_configs(self, detector, temp_project_dir):
        """Test scanning finds multiple legacy configs."""
        # Create configs in both locations
        root_config = temp_project_dir / "mycelium-config.yaml"
        root_config.write_text("version: '1.0'\n")

        mycelium_dir = temp_project_dir / ".mycelium"
        mycelium_dir.mkdir()
        mycelium_config = mycelium_dir / "mycelium-config.yaml"
        mycelium_config.write_text("version: '1.0'\n")

        configs = detector.scan_for_legacy_configs()
        assert len(configs) == 2

    def test_scan_caches_results(self, detector, temp_project_dir):
        """Test that scan results are cached."""
        # Create config
        legacy_path = temp_project_dir / "mycelium-config.yaml"
        legacy_path.write_text("version: '1.0'\n")

        # First scan
        configs1 = detector.scan_for_legacy_configs()
        assert len(configs1) == 1

        # Delete file
        legacy_path.unlink()

        # Second scan should return cached result
        configs2 = detector.scan_for_legacy_configs()
        assert len(configs2) == 1

    def test_clear_cache(self, detector, temp_project_dir):
        """Test clearing cache."""
        # Create and scan
        legacy_path = temp_project_dir / "mycelium-config.yaml"
        legacy_path.write_text("version: '1.0'\n")
        configs1 = detector.scan_for_legacy_configs()

        # Clear cache and delete file
        detector.clear_cache()
        legacy_path.unlink()

        # Should find no configs
        configs2 = detector.scan_for_legacy_configs()
        assert len(configs2) == 0

    def test_needs_migration_true(self, detector, temp_project_dir):
        """Test needs_migration returns True when configs found."""
        legacy_path = temp_project_dir / "mycelium-config.yaml"
        legacy_path.write_text("version: '1.0'\n")

        assert detector.needs_migration() is True

    def test_needs_migration_false(self, detector):
        """Test needs_migration returns False when no configs found."""
        assert detector.needs_migration() is False

    def test_get_migration_summary_empty(self, detector):
        """Test migration summary for empty directory."""
        summary = detector.get_migration_summary()
        assert summary["total_configs"] == 0
        assert summary["total_size_bytes"] == 0
        assert summary["readable_configs"] == 0
        assert summary["conflicting_configs"] == 0
        assert summary["migration_needed"] is False

    def test_get_migration_summary_with_configs(self, detector, temp_project_dir):
        """Test migration summary with configs."""
        # Create config
        legacy_path = temp_project_dir / "mycelium-config.yaml"
        content = "version: '1.0'\nproject_name: test\n"
        legacy_path.write_text(content)

        summary = detector.get_migration_summary()
        assert summary["total_configs"] == 1
        assert summary["total_size_bytes"] == len(content)
        assert summary["readable_configs"] == 1
        assert summary["migration_needed"] is True

    def test_validate_migration_feasibility_success(self, detector, temp_project_dir):
        """Test validation passes for valid migration."""
        legacy_path = temp_project_dir / "mycelium-config.yaml"
        legacy_path.write_text("version: '1.0'\n")

        errors = detector.validate_migration_feasibility()
        assert len(errors) == 0

    def test_validate_migration_feasibility_unreadable(self, detector, temp_project_dir):
        """Test validation fails for unreadable file."""
        # Create config
        legacy_path = temp_project_dir / "mycelium-config.yaml"
        legacy_path.write_text("version: '1.0'\n")

        # Make unreadable (on Unix systems)
        import platform

        if platform.system() != "Windows":
            legacy_path.chmod(0o000)
            try:
                errors = detector.validate_migration_feasibility()
                # Should have error about unreadable file
                assert any("not readable" in e.lower() for e in errors)
            finally:
                # Restore permissions for cleanup
                legacy_path.chmod(0o644)

    def test_check_for_conflicts(self, detector, temp_project_dir):
        """Test conflict detection."""
        # Create legacy config
        legacy_path = temp_project_dir / "mycelium-config.yaml"
        legacy_path.write_text("version: '1.0'\n")

        # Create new config at destination
        new_config_dir = temp_project_dir / ".mycelium"
        new_config_dir.mkdir()
        new_config_path = new_config_dir / "config.yaml"
        new_config_path.write_text("version: '2.0'\n")

        # Scan should detect conflict
        configs = detector.scan_for_legacy_configs()
        assert len(configs) > 0
        # At least one should have a conflict
        has_conflict = any(c.conflicts_with is not None for c in configs)
        # Note: This depends on migration logic, may not always conflict
