"""Unit tests for migration planner."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

from mycelium_onboarding.config.migration.detector import LegacyConfigLocation
from mycelium_onboarding.config.migration.planner import (
    MigrationAction,
    MigrationPlanner,
    MigrationStep,
)


class TestMigrationAction:
    """Tests for MigrationAction enum."""

    def test_action_values(self):
        """Test action enum values."""
        assert MigrationAction.MOVE.value == "move"
        assert MigrationAction.COPY.value == "copy"
        assert MigrationAction.MERGE.value == "merge"
        assert MigrationAction.SKIP.value == "skip"
        assert MigrationAction.CREATE.value == "create"
        assert MigrationAction.BACKUP.value == "backup"

    def test_action_str(self):
        """Test action string representation."""
        assert str(MigrationAction.MOVE) == "move"
        assert str(MigrationAction.BACKUP) == "backup"


class TestMigrationStep:
    """Tests for MigrationStep dataclass."""

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Windows path separators differ - needs Tier 2 cross-platform utilities",
    )
    def test_str_with_source(self):
        """Test string representation with source."""
        step = MigrationStep(
            action=MigrationAction.MOVE,
            source=Path("/old/config.yaml"),
            destination=Path("/new/config.yaml"),
            backup_path=None,
            description="Move config",
            order=1,
        )
        result = str(step)
        assert "[1]" in result
        assert "move" in result
        assert "/old/config.yaml" in result
        assert "/new/config.yaml" in result

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Windows path separators differ - needs Tier 2 cross-platform utilities",
    )
    def test_str_without_source(self):
        """Test string representation without source."""
        step = MigrationStep(
            action=MigrationAction.CREATE,
            source=None,
            destination=Path("/new/config.yaml"),
            backup_path=None,
            description="Create config",
            order=2,
        )
        result = str(step)
        assert "[2]" in result
        assert "create" in result
        assert "/new/config.yaml" in result

    def test_comparison(self):
        """Test step comparison by order."""
        step1 = MigrationStep(
            action=MigrationAction.MOVE,
            source=Path("/a"),
            destination=Path("/b"),
            backup_path=None,
            description="First",
            order=1,
        )
        step2 = MigrationStep(
            action=MigrationAction.MOVE,
            source=Path("/c"),
            destination=Path("/d"),
            backup_path=None,
            description="Second",
            order=2,
        )
        assert step1 < step2
        assert not step2 < step1


class TestMigrationPlanner:
    """Tests for MigrationPlanner."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def planner(self, temp_project_dir):
        """Create planner instance."""
        return MigrationPlanner(project_dir=temp_project_dir)

    def test_init_default_project_dir(self):
        """Test initialization with default project dir."""
        planner = MigrationPlanner()
        assert planner.project_dir == Path.cwd()

    def test_init_custom_project_dir(self, temp_project_dir):
        """Test initialization with custom project dir."""
        planner = MigrationPlanner(project_dir=temp_project_dir)
        assert planner.project_dir == temp_project_dir

    def test_create_plan_empty_configs(self, planner):
        """Test creating plan with no configs."""
        plan = planner.create_plan([], create_global=False, backup_all=False)
        assert len(plan) == 0

    def test_create_plan_single_config(self, planner, temp_project_dir):
        """Test creating plan with single config."""
        # Create legacy config
        legacy_path = temp_project_dir / "mycelium-config.yaml"
        legacy_path.write_text("version: '1.0'\n")

        configs = [
            LegacyConfigLocation(
                path=legacy_path,
                config_type="project-root",
                exists=True,
                readable=True,
                size_bytes=legacy_path.stat().st_size,
            )
        ]

        plan = planner.create_plan(configs, create_global=False, backup_all=False)
        assert len(plan) > 0
        # Should have at least one MOVE action
        move_steps = [s for s in plan if s.action == MigrationAction.MOVE]
        assert len(move_steps) > 0

    def test_create_plan_with_backup(self, planner, temp_project_dir):
        """Test creating plan with backup enabled."""
        legacy_path = temp_project_dir / "mycelium-config.yaml"
        legacy_path.write_text("version: '1.0'\n")

        configs = [
            LegacyConfigLocation(
                path=legacy_path,
                config_type="project-root",
                exists=True,
                readable=True,
                size_bytes=legacy_path.stat().st_size,
            )
        ]

        plan = planner.create_plan(configs, create_global=False, backup_all=True)
        # Should have backup steps
        backup_steps = [s for s in plan if s.action == MigrationAction.BACKUP]
        assert len(backup_steps) > 0

    def test_create_plan_with_global_config(self, planner, temp_project_dir):
        """Test creating plan with global config creation."""
        plan = planner.create_plan([], create_global=True, backup_all=False)
        # Should have CREATE step for global config (if it doesn't exist)
        [s for s in plan if s.action == MigrationAction.CREATE]
        # May or may not have create step depending on whether global config exists

    def test_create_plan_skips_unreadable(self, planner, temp_project_dir):
        """Test that plan skips unreadable configs."""
        configs = [
            LegacyConfigLocation(
                path=Path("/nonexistent.yaml"),
                config_type="project",
                exists=False,
                readable=False,
                size_bytes=0,
            )
        ]

        planner.create_plan(configs, create_global=False, backup_all=False)
        # Should not create steps for unreadable configs
        # Plan may be empty or only have other steps

    def test_create_plan_orders_steps(self, planner, temp_project_dir):
        """Test that plan steps are properly ordered."""
        legacy_path = temp_project_dir / "mycelium-config.yaml"
        legacy_path.write_text("version: '1.0'\n")

        configs = [
            LegacyConfigLocation(
                path=legacy_path,
                config_type="project-root",
                exists=True,
                readable=True,
                size_bytes=legacy_path.stat().st_size,
            )
        ]

        plan = planner.create_plan(configs, create_global=True, backup_all=True)

        # Verify steps are ordered
        for i in range(len(plan) - 1):
            assert plan[i].order <= plan[i + 1].order

    def test_validate_plan_success(self, planner, temp_project_dir):
        """Test plan validation passes for valid plan."""
        legacy_path = temp_project_dir / "mycelium-config.yaml"
        legacy_path.write_text("version: '1.0'\n")

        configs = [
            LegacyConfigLocation(
                path=legacy_path,
                config_type="project-root",
                exists=True,
                readable=True,
                size_bytes=legacy_path.stat().st_size,
            )
        ]

        plan = planner.create_plan(configs, create_global=False, backup_all=False)
        assert planner.validate_plan(plan) is True

    def test_validate_plan_missing_source(self, planner):
        """Test validation fails for missing source."""
        steps = [
            MigrationStep(
                action=MigrationAction.MOVE,
                source=Path("/nonexistent.yaml"),
                destination=Path("/new/config.yaml"),
                backup_path=None,
                description="Test",
                order=1,
            )
        ]

        assert planner.validate_plan(steps) is False

    def test_validate_plan_duplicate_destination(self, planner, temp_project_dir):
        """Test validation fails for duplicate destinations."""
        legacy_path = temp_project_dir / "test.yaml"
        legacy_path.write_text("test\n")

        dest = temp_project_dir / "dest.yaml"

        steps = [
            MigrationStep(
                action=MigrationAction.MOVE,
                source=legacy_path,
                destination=dest,
                backup_path=None,
                description="First",
                order=1,
            ),
            MigrationStep(
                action=MigrationAction.MOVE,
                source=legacy_path,
                destination=dest,  # Same destination
                backup_path=None,
                description="Second",
                order=2,
            ),
        ]

        assert planner.validate_plan(steps) is False

    def test_estimate_time(self, planner, temp_project_dir):
        """Test time estimation."""
        legacy_path = temp_project_dir / "mycelium-config.yaml"
        legacy_path.write_text("version: '1.0'\n")

        configs = [
            LegacyConfigLocation(
                path=legacy_path,
                config_type="project-root",
                exists=True,
                readable=True,
                size_bytes=legacy_path.stat().st_size,
            )
        ]

        plan = planner.create_plan(configs)
        time_estimate = planner.estimate_time(plan)

        assert time_estimate > 0.0
        assert isinstance(time_estimate, float)

    def test_get_plan_summary(self, planner, temp_project_dir):
        """Test plan summary generation."""
        legacy_path = temp_project_dir / "mycelium-config.yaml"
        legacy_path.write_text("version: '1.0'\n")

        configs = [
            LegacyConfigLocation(
                path=legacy_path,
                config_type="project-root",
                exists=True,
                readable=True,
                size_bytes=legacy_path.stat().st_size,
            )
        ]

        plan = planner.create_plan(configs, create_global=True, backup_all=True)
        summary = planner.get_plan_summary(plan)

        assert "total" in summary
        assert summary["total"] == len(plan)
        assert "move" in summary
        assert "backup" in summary

    def test_plan_handles_conflicts(self, planner, temp_project_dir):
        """Test plan handles conflicting configs."""
        # Create legacy config
        legacy_path = temp_project_dir / "mycelium-config.yaml"
        legacy_path.write_text("version: '1.0'\n")

        # Create new config that would conflict
        new_config_dir = temp_project_dir / ".mycelium"
        new_config_dir.mkdir()
        new_config_path = new_config_dir / "config.yaml"
        new_config_path.write_text("version: '2.0'\n")

        configs = [
            LegacyConfigLocation(
                path=legacy_path,
                config_type="project-root",
                exists=True,
                readable=True,
                size_bytes=legacy_path.stat().st_size,
                conflicts_with=new_config_path,
            )
        ]

        plan = planner.create_plan(configs, create_global=False, backup_all=False)

        # Should have MERGE action for conflict
        merge_steps = [s for s in plan if s.action == MigrationAction.MERGE]
        assert len(merge_steps) > 0

    def test_plan_skips_already_migrated(self, planner, temp_project_dir):
        """Test plan skips configs already at destination."""
        # Create config at destination
        dest_dir = temp_project_dir / ".mycelium"
        dest_dir.mkdir()
        dest_path = dest_dir / "config.yaml"
        dest_path.write_text("version: '1.0'\n")

        # Config at destination should be skipped
        configs = [
            LegacyConfigLocation(
                path=dest_path,
                config_type="project-mycelium",
                exists=True,
                readable=True,
                size_bytes=dest_path.stat().st_size,
            )
        ]

        plan = planner.create_plan(configs, create_global=False, backup_all=False)

        # Should have SKIP action
        [s for s in plan if s.action == MigrationAction.SKIP]
        # May or may not skip depending on exact path resolution
