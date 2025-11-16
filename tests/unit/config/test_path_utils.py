"""Unit tests for path migration utilities."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from mycelium_onboarding.config.path_utils import (
    PathMigrationError,
    SymlinkError,
    YAMLError,
    atomic_move,
    check_write_permission,
    create_backup,
    find_legacy_configs,
    is_symlink_safe,
    safe_read_yaml,
    safe_write_yaml,
)


class TestFindLegacyConfigs:
    """Test finding legacy configuration files."""

    def test_find_legacy_configs_empty_directories(self, tmp_path: Path) -> None:
        """Test finding configs in empty directories returns empty list."""
        search_paths = [tmp_path]
        result = find_legacy_configs(search_paths)
        assert result == []

    def test_find_legacy_configs_finds_file(self, tmp_path: Path) -> None:
        """Test finding legacy config files."""
        legacy_file = tmp_path / "mycelium-config.yaml"
        legacy_file.touch()

        result = find_legacy_configs([tmp_path])

        assert len(result) == 1
        assert result[0] == legacy_file

    def test_find_legacy_configs_multiple_directories(self, tmp_path: Path) -> None:
        """Test finding configs in multiple directories."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        (dir1 / "mycelium-config.yaml").touch()
        (dir2 / "mycelium-config.yaml").touch()

        result = find_legacy_configs([dir1, dir2])

        assert len(result) == 2
        assert all(p.exists() for p in result)

    def test_find_legacy_configs_custom_filename(self, tmp_path: Path) -> None:
        """Test finding configs with custom filename."""
        custom_file = tmp_path / "custom-config.yaml"
        custom_file.touch()

        result = find_legacy_configs([tmp_path], legacy_filename="custom-config.yaml")

        assert len(result) == 1
        assert result[0] == custom_file

    def test_find_legacy_configs_ignores_nonexistent_dirs(self, tmp_path: Path) -> None:
        """Test that nonexistent directories are ignored."""
        nonexistent = tmp_path / "nonexistent"

        # Should not raise, just return empty list
        result = find_legacy_configs([nonexistent])
        assert result == []

    def test_find_legacy_configs_default_search_paths(self) -> None:
        """Test finding configs with default search paths."""
        # Should not raise, even if no configs found
        result = find_legacy_configs()
        assert isinstance(result, list)


class TestCheckWritePermission:
    """Test write permission checking."""

    def test_check_write_permission_existing_writable_file(self, tmp_path: Path) -> None:
        """Test permission check for existing writable file."""
        test_file = tmp_path / "test.txt"
        test_file.touch()

        assert check_write_permission(test_file) is True

    def test_check_write_permission_nonexistent_file_writable_dir(self, tmp_path: Path) -> None:
        """Test permission check for non-existent file in writable directory."""
        test_file = tmp_path / "nonexistent.txt"

        assert check_write_permission(test_file) is True

    def test_check_write_permission_readonly_file(self, tmp_path: Path) -> None:
        """Test permission check for read-only file."""
        if os.name != "posix":
            pytest.skip("Read-only test only works on POSIX systems")

        test_file = tmp_path / "readonly.txt"
        test_file.touch()
        test_file.chmod(0o444)

        try:
            assert check_write_permission(test_file) is False
        finally:
            # Restore write permission for cleanup
            test_file.chmod(0o644)


class TestIsSymlinkSafe:
    """Test symlink safety checking."""

    def test_is_symlink_safe_regular_file(self, tmp_path: Path) -> None:
        """Test that regular files are safe."""
        test_file = tmp_path / "regular.txt"
        test_file.touch()

        assert is_symlink_safe(test_file) is True

    def test_is_symlink_safe_nonexistent_path(self, tmp_path: Path) -> None:
        """Test that non-existent paths are safe."""
        nonexistent = tmp_path / "nonexistent.txt"

        assert is_symlink_safe(nonexistent) is True

    def test_is_symlink_safe_rejects_symlink_by_default(self, tmp_path: Path) -> None:
        """Test that symlinks are rejected by default."""
        if os.name == "nt":
            pytest.skip("Symlink test not reliable on Windows")

        target = tmp_path / "target.txt"
        target.touch()

        link = tmp_path / "link.txt"
        link.symlink_to(target)

        with pytest.raises(SymlinkError, match="symlink"):
            is_symlink_safe(link)

    def test_is_symlink_safe_allows_symlink_when_enabled(self, tmp_path: Path) -> None:
        """Test that symlinks can be allowed."""
        if os.name == "nt":
            pytest.skip("Symlink test not reliable on Windows")

        target = tmp_path / "target.txt"
        target.touch()

        link = tmp_path / "link.txt"
        link.symlink_to(target)

        assert is_symlink_safe(link, allow_symlinks=True) is True


class TestCreateBackup:
    """Test backup creation."""

    def test_create_backup_creates_file(self, tmp_path: Path) -> None:
        """Test that create_backup creates a backup file."""
        original = tmp_path / "original.txt"
        original.write_text("content")

        backup = create_backup(original, backup_dir=tmp_path)

        assert backup.exists()
        assert backup.read_text() == "content"
        assert backup != original

    def test_create_backup_with_timestamp(self, tmp_path: Path) -> None:
        """Test that create_backup adds timestamp."""
        original = tmp_path / "original.txt"
        original.write_text("content")

        backup = create_backup(original, backup_dir=tmp_path, timestamp=True)

        # Backup filename should contain timestamp
        assert "original" in backup.stem
        assert backup.suffix == ".txt"

    def test_create_backup_without_timestamp(self, tmp_path: Path) -> None:
        """Test that create_backup without timestamp."""
        original = tmp_path / "original.txt"
        original.write_text("content")

        backup = create_backup(original, backup_dir=tmp_path, timestamp=False)

        assert backup.name == "original.txt.bak"

    def test_create_backup_handles_collisions(self, tmp_path: Path) -> None:
        """Test that create_backup handles filename collisions."""
        original = tmp_path / "original.txt"
        original.write_text("content")

        # Create first backup
        backup1 = create_backup(original, backup_dir=tmp_path, timestamp=False)

        # Create second backup (should use different name)
        backup2 = create_backup(original, backup_dir=tmp_path, timestamp=False)

        assert backup1 != backup2
        assert backup1.exists()
        assert backup2.exists()

    def test_create_backup_raises_on_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that create_backup raises error for non-existent file."""
        nonexistent = tmp_path / "nonexistent.txt"

        with pytest.raises(PathMigrationError, match="non-existent"):
            create_backup(nonexistent)


class TestAtomicMove:
    """Test atomic file move operations."""

    def test_atomic_move_basic(self, tmp_path: Path) -> None:
        """Test basic atomic move operation."""
        src = tmp_path / "source.txt"
        src.write_text("content")

        dst = tmp_path / "dest.txt"

        result = atomic_move(src, dst, backup=False)

        assert result == dst
        assert dst.exists()
        assert not src.exists()
        assert dst.read_text() == "content"

    def test_atomic_move_with_backup(self, tmp_path: Path) -> None:
        """Test atomic move with backup of existing destination."""
        src = tmp_path / "source.txt"
        src.write_text("new content")

        dst = tmp_path / "dest.txt"
        dst.write_text("old content")

        result = atomic_move(src, dst, backup=True)

        assert result == dst
        assert dst.read_text() == "new content"
        assert not src.exists()

        # Backup should exist somewhere
        # (we can't easily verify the exact backup location without mocking)

    def test_atomic_move_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Test that atomic move creates parent directories."""
        src = tmp_path / "source.txt"
        src.write_text("content")

        dst = tmp_path / "nested" / "dir" / "dest.txt"

        result = atomic_move(src, dst, backup=False)

        assert result == dst
        assert dst.exists()
        assert dst.parent.exists()

    def test_atomic_move_raises_on_nonexistent_source(self, tmp_path: Path) -> None:
        """Test that atomic move raises error for non-existent source."""
        src = tmp_path / "nonexistent.txt"
        dst = tmp_path / "dest.txt"

        with pytest.raises(PathMigrationError, match="does not exist"):
            atomic_move(src, dst)

    def test_atomic_move_raises_on_directory_source(self, tmp_path: Path) -> None:
        """Test that atomic move raises error for directory source."""
        src = tmp_path / "source_dir"
        src.mkdir()

        dst = tmp_path / "dest.txt"

        with pytest.raises(PathMigrationError, match="not a file"):
            atomic_move(src, dst)


class TestSafeReadYAML:
    """Test safe YAML reading."""

    def test_safe_read_yaml_basic(self, tmp_path: Path) -> None:
        """Test basic YAML reading."""
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text("key: value\nnumber: 42\n")

        data = safe_read_yaml(yaml_file)

        assert data == {"key": "value", "number": 42}

    def test_safe_read_yaml_empty_file(self, tmp_path: Path) -> None:
        """Test reading empty YAML file."""
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("")

        data = safe_read_yaml(yaml_file)

        assert data == {}

    def test_safe_read_yaml_nested_structure(self, tmp_path: Path) -> None:
        """Test reading nested YAML structure."""
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text("""
services:
  redis:
    port: 6379
    host: localhost
""")

        data = safe_read_yaml(yaml_file)

        assert data["services"]["redis"]["port"] == 6379

    def test_safe_read_yaml_raises_on_nonexistent(self, tmp_path: Path) -> None:
        """Test that safe_read_yaml raises error for non-existent file."""
        nonexistent = tmp_path / "nonexistent.yaml"

        with pytest.raises(PathMigrationError, match="does not exist"):
            safe_read_yaml(nonexistent)

    def test_safe_read_yaml_raises_on_invalid_yaml(self, tmp_path: Path) -> None:
        """Test that safe_read_yaml raises error for invalid YAML."""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text("key: [invalid\n")

        with pytest.raises(YAMLError):
            safe_read_yaml(yaml_file)


class TestSafeWriteYAML:
    """Test safe YAML writing."""

    def test_safe_write_yaml_basic(self, tmp_path: Path) -> None:
        """Test basic YAML writing."""
        yaml_file = tmp_path / "config.yaml"
        data = {"key": "value", "number": 42}

        result = safe_write_yaml(yaml_file, data, backup=False)

        assert result == yaml_file
        assert yaml_file.exists()

        # Verify content
        content = yaml_file.read_text()
        assert "key: value" in content
        assert "number: 42" in content

    def test_safe_write_yaml_nested_structure(self, tmp_path: Path) -> None:
        """Test writing nested YAML structure."""
        yaml_file = tmp_path / "config.yaml"
        data = {
            "services": {
                "redis": {"port": 6379, "host": "localhost"},
            }
        }

        safe_write_yaml(yaml_file, data, backup=False)

        # Read back and verify
        read_data = safe_read_yaml(yaml_file)
        assert read_data == data

    def test_safe_write_yaml_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Test that safe_write_yaml creates parent directories."""
        yaml_file = tmp_path / "nested" / "dir" / "config.yaml"
        data = {"key": "value"}

        safe_write_yaml(yaml_file, data, backup=False)

        assert yaml_file.exists()
        assert yaml_file.parent.exists()

    def test_safe_write_yaml_with_backup(self, tmp_path: Path) -> None:
        """Test writing YAML with backup of existing file."""
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text("old: content\n")

        data = {"new": "content"}

        safe_write_yaml(yaml_file, data, backup=True)

        assert yaml_file.exists()
        read_data = safe_read_yaml(yaml_file)
        assert read_data == data

    def test_safe_write_yaml_atomic_by_default(self, tmp_path: Path) -> None:
        """Test that safe_write_yaml uses atomic writes by default."""
        yaml_file = tmp_path / "config.yaml"
        data = {"key": "value"}

        # Should complete without error
        result = safe_write_yaml(yaml_file, data, backup=False, atomic=True)

        assert result.exists()

    def test_safe_write_yaml_non_atomic(self, tmp_path: Path) -> None:
        """Test safe_write_yaml with non-atomic write."""
        yaml_file = tmp_path / "config.yaml"
        data = {"key": "value"}

        result = safe_write_yaml(yaml_file, data, backup=False, atomic=False)

        assert result.exists()
        read_data = safe_read_yaml(yaml_file)
        assert read_data == data


class TestRoundTripYAML:
    """Test YAML round-trip consistency."""

    def test_yaml_roundtrip(self, tmp_path: Path) -> None:
        """Test that YAML data survives write-read cycle."""
        yaml_file = tmp_path / "config.yaml"
        original_data = {
            "project_name": "test-project",
            "services": {
                "redis": {"port": 6379, "host": "localhost"},
                "postgres": {"port": 5432, "database": "mycelium"},
            },
            "enabled": True,
            "count": 42,
        }

        safe_write_yaml(yaml_file, original_data, backup=False)
        read_data = safe_read_yaml(yaml_file)

        assert read_data == original_data
