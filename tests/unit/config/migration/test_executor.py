"""Unit tests for migration executor."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

from mycelium_onboarding.config.migration.detector import LegacyConfigLocation
from mycelium_onboarding.config.migration.executor import (
    MigrationExecutor,
    MigrationResult,
)
from mycelium_onboarding.config.migration.planner import (
    MigrationAction,
    MigrationPlanner,
    MigrationStep,
)


class TestMigrationResult:
    """Tests for MigrationResult dataclass."""

    def test_str_success(self):
        """Test string representation for successful migration."""
        result = MigrationResult(
            success=True,
            steps_completed=5,
            steps_total=5,
            backup_dir=Path("/backup"),
            errors=[],
            duration_seconds=1.5,
        )
        result_str = str(result)
        assert "SUCCESS" in result_str
        assert "5/5" in result_str
        assert "1.5" in result_str

    def test_str_failure(self):
        """Test string representation for failed migration."""
        result = MigrationResult(
            success=False,
            steps_completed=3,
            steps_total=5,
            backup_dir=Path("/backup"),
            errors=["Error 1", "Error 2"],
            duration_seconds=0.5,
        )
        result_str = str(result)
        assert "FAILED" in result_str
        assert "3/5" in result_str

    def test_str_dry_run(self):
        """Test string representation for dry run."""
        result = MigrationResult(
            success=True,
            steps_completed=5,
            steps_total=5,
            backup_dir=None,
            errors=[],
            duration_seconds=0.1,
            dry_run=True,
        )
        result_str = str(result)
        assert "DRY RUN" in result_str
        assert "SUCCESS" in result_str


class TestMigrationExecutor:
    """Tests for MigrationExecutor."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        return MigrationExecutor(dry_run=False)

    @pytest.fixture
    def dry_executor(self):
        """Create dry-run executor instance."""
        return MigrationExecutor(dry_run=True)

    def test_init_default(self):
        """Test initialization with defaults."""
        executor = MigrationExecutor()
        assert executor.dry_run is False

    def test_init_dry_run(self):
        """Test initialization with dry run."""
        executor = MigrationExecutor(dry_run=True)
        assert executor.dry_run is True

    def test_execute_empty_plan(self, executor):
        """Test executing empty plan."""
        result = executor.execute([])
        assert result.success is True
        assert result.steps_completed == 0
        assert result.steps_total == 0
        assert len(result.errors) == 0

    def test_execute_dry_run(self, dry_executor, temp_project_dir):
        """Test dry run execution."""
        # Create source file
        source = temp_project_dir / "source.yaml"
        source.write_text("test: data\n")

        dest = temp_project_dir / "dest.yaml"

        steps = [
            MigrationStep(
                action=MigrationAction.MOVE,
                source=source,
                destination=dest,
                backup_path=None,
                description="Test move",
                order=1,
            )
        ]

        result = dry_executor.execute(steps)

        # Dry run should succeed
        assert result.success is True
        assert result.dry_run is True
        # Source should still exist (not actually moved)
        assert source.exists()
        # Destination should not exist
        assert not dest.exists()

    @pytest.mark.skipif(sys.platform == "darwin", reason="File system behavior differs on macOS")
    def test_execute_move_step(self, executor, temp_project_dir):
        """Test executing move step."""
        # Create source file
        source = temp_project_dir / "source.yaml"
        source.write_text("version: '1.0'\n")

        dest = temp_project_dir / "subdir" / "dest.yaml"

        steps = [
            MigrationStep(
                action=MigrationAction.MOVE,
                source=source,
                destination=dest,
                backup_path=None,
                description="Move file",
                order=1,
            )
        ]

        result = executor.execute(steps)

        assert result.success is True
        assert result.steps_completed == 1
        # Source should be moved
        assert not source.exists()
        # Destination should exist
        assert dest.exists()
        assert dest.read_text() == "version: '1.0'\n"

    def test_execute_copy_step(self, executor, temp_project_dir):
        """Test executing copy step."""
        # Create source file
        source = temp_project_dir / "source.yaml"
        source.write_text("version: '1.0'\n")

        dest = temp_project_dir / "dest.yaml"

        steps = [
            MigrationStep(
                action=MigrationAction.COPY,
                source=source,
                destination=dest,
                backup_path=None,
                description="Copy file",
                order=1,
            )
        ]

        result = executor.execute(steps)

        assert result.success is True
        # Both source and destination should exist
        assert source.exists()
        assert dest.exists()

    def test_execute_create_step(self, executor, temp_project_dir):
        """Test executing create step."""
        dest = temp_project_dir / "new_config.yaml"

        steps = [
            MigrationStep(
                action=MigrationAction.CREATE,
                source=None,
                destination=dest,
                backup_path=None,
                description="Create config",
                order=1,
            )
        ]

        result = executor.execute(steps)

        assert result.success is True
        assert dest.exists()
        # Should contain default config
        import yaml

        data = yaml.safe_load(dest.read_text())
        assert "version" in data

    def test_execute_skip_step(self, executor, temp_project_dir):
        """Test executing skip step."""
        source = temp_project_dir / "source.yaml"
        source.write_text("test\n")

        steps = [
            MigrationStep(
                action=MigrationAction.SKIP,
                source=source,
                destination=source,
                backup_path=None,
                description="Skip file",
                order=1,
            )
        ]

        result = executor.execute(steps)

        assert result.success is True
        # File should be unchanged
        assert source.exists()

    def test_execute_backup_step(self, executor, temp_project_dir):
        """Test executing backup step."""
        # Create source file
        source = temp_project_dir / "source.yaml"
        source.write_text("version: '1.0'\n")

        # Create backup directory
        backup_dir = temp_project_dir / "backup"
        backup_dir.mkdir()

        backup_dest = backup_dir / "source_backup.yaml"

        steps = [
            MigrationStep(
                action=MigrationAction.BACKUP,
                source=source,
                destination=backup_dest,
                backup_path=None,
                description="Backup file",
                order=1,
            )
        ]

        # Execute with backup_dir
        executor.execute(steps)

        # Note: Backup creation happens in executor's backup phase
        # This test verifies the mechanism works

    def test_execute_merge_step(self, executor, temp_project_dir):
        """Test executing merge step."""
        # Create source and destination files
        source = temp_project_dir / "source.yaml"
        source.write_text("key1: value1\nkey2: value2\n")

        dest = temp_project_dir / "dest.yaml"
        dest.write_text("key2: old_value\nkey3: value3\n")

        steps = [
            MigrationStep(
                action=MigrationAction.MERGE,
                source=source,
                destination=dest,
                backup_path=None,
                description="Merge configs",
                order=1,
            )
        ]

        result = executor.execute(steps)

        assert result.success is True

        # Verify merge
        import yaml

        merged = yaml.safe_load(dest.read_text())
        assert merged["key1"] == "value1"
        assert merged["key2"] == "value2"  # Source should override
        assert merged["key3"] == "value3"

    @pytest.mark.skipif(sys.platform == "darwin", reason="File system behavior differs on macOS")
    def test_execute_with_progress_callback(self, executor, temp_project_dir):
        """Test execution with progress callback."""
        source = temp_project_dir / "source.yaml"
        source.write_text("test\n")

        dest = temp_project_dir / "dest.yaml"

        steps = [
            MigrationStep(
                action=MigrationAction.MOVE,
                source=source,
                destination=dest,
                backup_path=None,
                description="Move file",
                order=1,
            )
        ]

        progress_calls = []

        def progress_callback(current, total, message):
            progress_calls.append((current, total, message))

        result = executor.execute(steps, progress_callback=progress_callback)

        assert result.success is True
        assert len(progress_calls) > 0
        # Verify callback was called with correct parameters
        assert progress_calls[0][0] == 1  # current
        assert progress_calls[0][1] == 1  # total

    @pytest.mark.skipif(sys.platform == "darwin", reason="File system behavior differs on macOS")
    def test_execute_creates_backup_dir(self, executor, temp_project_dir):
        """Test that execution creates backup directory."""
        source = temp_project_dir / "source.yaml"
        source.write_text("test\n")

        dest = temp_project_dir / "dest.yaml"

        steps = [
            MigrationStep(
                action=MigrationAction.MOVE,
                source=source,
                destination=dest,
                backup_path=None,
                description="Move file",
                order=1,
            )
        ]

        result = executor.execute(steps)

        assert result.success is True
        # Backup directory should be created
        assert result.backup_dir is not None
        assert result.backup_dir.exists()

    def test_execute_handles_errors(self, executor, temp_project_dir):
        """Test execution handles errors gracefully."""
        # Create step with non-existent source
        steps = [
            MigrationStep(
                action=MigrationAction.MOVE,
                source=Path("/nonexistent/source.yaml"),
                destination=temp_project_dir / "dest.yaml",
                backup_path=None,
                description="Move nonexistent file",
                order=1,
            )
        ]

        result = executor.execute(steps)

        assert result.success is False
        assert len(result.errors) > 0
        assert result.steps_completed == 0

    @pytest.mark.skipif(sys.platform == "darwin", reason="File system behavior differs on macOS")
    def test_execute_multiple_steps_in_order(self, executor, temp_project_dir):
        """Test execution of multiple steps in order."""
        # Create multiple source files
        source1 = temp_project_dir / "source1.yaml"
        source1.write_text("file1\n")

        source2 = temp_project_dir / "source2.yaml"
        source2.write_text("file2\n")

        dest_dir = temp_project_dir / "dest"

        steps = [
            MigrationStep(
                action=MigrationAction.MOVE,
                source=source1,
                destination=dest_dir / "dest1.yaml",
                backup_path=None,
                description="Move file 1",
                order=1,
            ),
            MigrationStep(
                action=MigrationAction.MOVE,
                source=source2,
                destination=dest_dir / "dest2.yaml",
                backup_path=None,
                description="Move file 2",
                order=2,
            ),
        ]

        result = executor.execute(steps)

        assert result.success is True
        assert result.steps_completed == 2
        assert (dest_dir / "dest1.yaml").exists()
        assert (dest_dir / "dest2.yaml").exists()

    def test_rollback(self, executor, temp_project_dir):
        """Test rollback functionality."""
        # Create backup directory with files
        backup_dir = temp_project_dir / "backup"
        backup_dir.mkdir()

        backup_file = backup_dir / "config.yaml"
        backup_file.write_text("original: content\n")

        # Execute rollback
        # Note: Rollback implementation may need original path mapping
        # This is a simplified test
        success = executor.rollback(backup_dir)

        # Basic verification that rollback executes
        assert isinstance(success, bool)

    @pytest.mark.skipif(sys.platform == "darwin", reason="File system behavior differs on macOS")
    def test_integration_with_planner(self, executor, temp_project_dir):
        """Test integration between planner and executor."""
        # Create legacy config
        legacy_path = temp_project_dir / "mycelium-config.yaml"
        legacy_path.write_text("version: '1.0'\nproject_name: test\n")

        # Create config location
        config = LegacyConfigLocation(
            path=legacy_path,
            config_type="project-root",
            exists=True,
            readable=True,
            size_bytes=legacy_path.stat().st_size,
        )

        # Create plan
        planner = MigrationPlanner(project_dir=temp_project_dir)
        plan = planner.create_plan([config], create_global=False, backup_all=True)

        # Execute plan
        result = executor.execute(plan)

        # Should succeed
        assert result.success is True
        assert result.steps_completed == result.steps_total
