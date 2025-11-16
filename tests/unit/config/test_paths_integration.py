"""Integration tests for XDG paths and migration utilities."""

from __future__ import annotations

from pathlib import Path

from mycelium_onboarding.config.path_utils import (
    atomic_move,
    find_legacy_configs,
    safe_read_yaml,
    safe_write_yaml,
)
from mycelium_onboarding.config.paths import (
    ensure_dir_exists,
    get_global_config_path,
    get_project_config_path,
)


class TestIntegration:
    """Test integration between paths and path_utils modules."""

    def test_full_migration_workflow(self, tmp_path: Path) -> None:
        """Test complete migration workflow from legacy to new location."""
        # Setup: Create legacy config
        legacy_dir = tmp_path / "legacy"
        legacy_dir.mkdir()
        legacy_config = legacy_dir / "mycelium-config.yaml"

        legacy_data = {
            "project_name": "legacy-project",
            "services": {
                "redis": {"port": 6379},
            },
        }
        safe_write_yaml(legacy_config, legacy_data, backup=False)

        # Find legacy configs
        found = find_legacy_configs([legacy_dir])
        assert len(found) == 1
        assert found[0] == legacy_config

        # Migrate to new location
        new_dir = tmp_path / "new"
        ensure_dir_exists(new_dir)
        new_config = new_dir / "config.yaml"

        atomic_move(legacy_config, new_config, backup=False)

        # Verify migration
        assert not legacy_config.exists()
        assert new_config.exists()

        # Verify data integrity
        migrated_data = safe_read_yaml(new_config)
        assert migrated_data == legacy_data

    def test_project_config_workflow(self, tmp_path: Path) -> None:
        """Test creating and reading project config."""
        project_root = tmp_path / "my-project"
        project_root.mkdir()

        config_path = get_project_config_path(project_root)
        assert not config_path.exists()

        # Create config directory
        ensure_dir_exists(config_path.parent)

        # Write config
        config_data = {
            "project_name": "my-project",
            "services": {
                "postgres": {"port": 5432, "database": "mydb"},
            },
        }
        safe_write_yaml(config_path, config_data, backup=False)

        # Read config back
        read_data = safe_read_yaml(config_path)
        assert read_data == config_data

    def test_global_config_path_structure(self) -> None:
        """Test that global config path follows XDG structure."""
        global_path = get_global_config_path()

        # Should be absolute
        assert global_path.is_absolute()

        # Should end with config.yaml
        assert global_path.name == "config.yaml"

        # Parent should be mycelium
        assert global_path.parent.name == "mycelium"

    def test_backup_workflow(self, tmp_path: Path) -> None:
        """Test workflow with backups."""
        # Create original config
        config_file = tmp_path / "config.yaml"
        original_data = {"version": 1, "name": "original"}
        safe_write_yaml(config_file, original_data, backup=False)

        # Update with backup
        updated_data = {"version": 2, "name": "updated"}
        safe_write_yaml(config_file, updated_data, backup=True)

        # Current config should have updated data
        current_data = safe_read_yaml(config_file)
        assert current_data == updated_data

        # Backup should exist (we can't easily verify content without knowing backup location)

    def test_atomic_move_with_directory_creation(self, tmp_path: Path) -> None:
        """Test atomic move creates destination directories."""
        src = tmp_path / "source.yaml"
        src.write_text("test: data\n")

        # Destination in nested directory that doesn't exist
        dst = tmp_path / "nested" / "path" / "dest.yaml"

        atomic_move(src, dst, backup=False)

        assert dst.exists()
        assert dst.parent.exists()
        assert not src.exists()

    def test_roundtrip_with_complex_data(self, tmp_path: Path) -> None:
        """Test roundtrip with complex nested data."""
        config_file = tmp_path / "complex.yaml"

        complex_data = {
            "project_name": "test",
            "schema_version": "1.0.0",
            "services": {
                "redis": {
                    "port": 6379,
                    "host": "localhost",
                    "enabled": True,
                },
                "postgres": {
                    "port": 5432,
                    "database": "mydb",
                    "user": "postgres",
                    "ssl": False,
                },
            },
            "deployment": {
                "method": "docker-compose",
                "healthcheck_timeout": 30,
            },
            "features": ["feature1", "feature2"],
        }

        # Write and read back
        safe_write_yaml(config_file, complex_data, backup=False)
        read_data = safe_read_yaml(config_file)

        assert read_data == complex_data
