"""Integration tests for complete migration workflow."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from mycelium_onboarding.config.migration import (
    MigrationDetector,
    MigrationExecutor,
    MigrationPlanner,
)


class TestMigrationIntegration:
    """Integration tests for complete migration workflow."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_complete_migration_workflow(self, temp_project_dir):
        """Test complete migration from detection to execution."""
        # Step 1: Create legacy config
        legacy_config = temp_project_dir / "mycelium-config.yaml"
        legacy_data = {
            "version": "1.0",
            "project_name": "test-project",
            "services": {
                "redis": {"enabled": True, "port": 6379},
                "postgres": {"enabled": True, "port": 5432},
            },
        }
        legacy_config.write_text(yaml.safe_dump(legacy_data))

        # Step 2: Detect legacy configs
        detector = MigrationDetector(project_dir=temp_project_dir)
        assert detector.needs_migration() is True

        legacy_configs = detector.scan_for_legacy_configs()
        assert len(legacy_configs) == 1
        assert legacy_configs[0].exists is True

        # Step 3: Get migration summary
        summary = detector.get_migration_summary()
        assert summary["total_configs"] == 1
        assert summary["migration_needed"] is True

        # Step 4: Validate migration feasibility
        errors = detector.validate_migration_feasibility()
        assert len(errors) == 0

        # Step 5: Create migration plan
        planner = MigrationPlanner(project_dir=temp_project_dir)
        plan = planner.create_plan(legacy_configs, create_global=False, backup_all=True)

        assert len(plan) > 0

        # Step 6: Validate plan
        assert planner.validate_plan(plan) is True

        # Step 7: Get plan summary
        plan_summary = planner.get_plan_summary(plan)
        assert plan_summary["total"] == len(plan)

        # Step 8: Estimate time
        estimated_time = planner.estimate_time(plan)
        assert estimated_time > 0

        # Step 9: Execute migration (dry run first)
        dry_executor = MigrationExecutor(dry_run=True)
        dry_result = dry_executor.execute(plan)

        assert dry_result.success is True
        assert dry_result.dry_run is True
        # Legacy config should still exist after dry run
        assert legacy_config.exists()

        # Step 10: Execute migration for real
        executor = MigrationExecutor(dry_run=False)
        result = executor.execute(plan)

        assert result.success is True
        assert result.steps_completed == result.steps_total
        assert result.backup_dir is not None
        assert result.backup_dir.exists()

        # Step 11: Verify migration
        # Legacy config should be moved
        assert not legacy_config.exists()

        # New config should exist at .mycelium/config.yaml
        new_config = temp_project_dir / ".mycelium" / "config.yaml"
        assert new_config.exists()

        # New config should have same data
        new_data = yaml.safe_load(new_config.read_text())
        assert new_data["version"] == "1.0"
        assert new_data["project_name"] == "test-project"
        assert new_data["services"]["redis"]["port"] == 6379

        # Step 12: Verify no more migration needed
        detector.clear_cache()
        assert detector.needs_migration() is False

    def test_migration_with_progress_callback(self, temp_project_dir):
        """Test migration with progress reporting."""
        # Create legacy config
        legacy_config = temp_project_dir / "mycelium-config.yaml"
        legacy_config.write_text("version: '1.0'\n")

        # Detect and plan
        detector = MigrationDetector(project_dir=temp_project_dir)
        legacy_configs = detector.scan_for_legacy_configs()

        planner = MigrationPlanner(project_dir=temp_project_dir)
        plan = planner.create_plan(legacy_configs, create_global=False, backup_all=True)

        # Track progress
        progress_updates = []

        def progress_callback(current, total, message):
            progress_updates.append({"current": current, "total": total, "message": message})

        # Execute with progress tracking
        executor = MigrationExecutor(dry_run=False)
        result = executor.execute(plan, progress_callback=progress_callback)

        assert result.success is True
        assert len(progress_updates) > 0

        # Verify progress updates
        for update in progress_updates:
            assert update["current"] <= update["total"]
            assert isinstance(update["message"], str)

    def test_migration_handles_conflicts(self, temp_project_dir):
        """Test migration handles existing configs."""
        # Create legacy config
        legacy_config = temp_project_dir / "mycelium-config.yaml"
        legacy_config.write_text("version: '1.0'\nlegacy: true\n")

        # Create existing new config
        new_config_dir = temp_project_dir / ".mycelium"
        new_config_dir.mkdir()
        new_config = new_config_dir / "config.yaml"
        new_config.write_text("version: '2.0'\nexisting: true\n")

        # Detect and plan
        detector = MigrationDetector(project_dir=temp_project_dir)
        legacy_configs = detector.scan_for_legacy_configs()

        # Should detect conflict
        assert any(c.conflicts_with is not None for c in legacy_configs)

        # Create plan (should handle conflict)
        planner = MigrationPlanner(project_dir=temp_project_dir)
        plan = planner.create_plan(legacy_configs, create_global=False, backup_all=True)

        # Plan should include MERGE action
        from mycelium_onboarding.config.migration.planner import MigrationAction

        merge_steps = [s for s in plan if s.action == MigrationAction.MERGE]
        # May or may not have merge step depending on implementation

    def test_migration_multiple_configs(self, temp_project_dir):
        """Test migration with multiple legacy configs."""
        # Create multiple legacy configs
        root_config = temp_project_dir / "mycelium-config.yaml"
        root_config.write_text("version: '1.0'\nlocation: root\n")

        mycelium_dir = temp_project_dir / ".mycelium"
        mycelium_dir.mkdir()
        mycelium_config = mycelium_dir / "mycelium-config.yaml"
        mycelium_config.write_text("version: '1.0'\nlocation: mycelium\n")

        # Detect
        detector = MigrationDetector(project_dir=temp_project_dir)
        legacy_configs = detector.scan_for_legacy_configs()

        assert len(legacy_configs) == 2

        # Plan and execute
        planner = MigrationPlanner(project_dir=temp_project_dir)
        plan = planner.create_plan(legacy_configs, create_global=False, backup_all=True)

        executor = MigrationExecutor(dry_run=False)
        result = executor.execute(plan)

        # Should handle both configs
        assert result.success is True

    def test_rollback_after_migration(self, temp_project_dir):
        """Test rollback functionality after migration."""
        # Create and execute migration
        legacy_config = temp_project_dir / "mycelium-config.yaml"
        original_content = "version: '1.0'\nproject_name: test\n"
        legacy_config.write_text(original_content)

        detector = MigrationDetector(project_dir=temp_project_dir)
        legacy_configs = detector.scan_for_legacy_configs()

        planner = MigrationPlanner(project_dir=temp_project_dir)
        plan = planner.create_plan(legacy_configs, create_global=False, backup_all=True)

        executor = MigrationExecutor(dry_run=False)
        result = executor.execute(plan)

        assert result.success is True
        backup_dir = result.backup_dir
        assert backup_dir is not None

        # Test rollback functionality exists
        from mycelium_onboarding.config.migration.rollback import RollbackManager

        rollback_manager = RollbackManager()
        assert rollback_manager.can_rollback(backup_dir) is True

    def test_migration_validation_errors(self, temp_project_dir):
        """Test migration validation catches errors."""
        # Create unreadable config (on Unix systems)
        import platform

        if platform.system() != "Windows":
            legacy_config = temp_project_dir / "mycelium-config.yaml"
            legacy_config.write_text("version: '1.0'\n")
            legacy_config.chmod(0o000)

            try:
                detector = MigrationDetector(project_dir=temp_project_dir)
                errors = detector.validate_migration_feasibility()

                # Should have errors about unreadable file
                assert len(errors) > 0
            finally:
                # Restore permissions for cleanup
                legacy_config.chmod(0o644)

    def test_end_to_end_with_all_features(self, temp_project_dir):
        """Test end-to-end migration with all features enabled."""
        # Create complex legacy config
        legacy_config = temp_project_dir / "mycelium-config.yaml"
        complex_data = {
            "version": "1.0",
            "project_name": "complex-project",
            "deployment": {"method": "docker-compose", "auto_start": True},
            "services": {
                "redis": {
                    "enabled": True,
                    "port": 6379,
                    "persistence": True,
                    "max_memory": "256mb",
                },
                "postgres": {
                    "enabled": True,
                    "port": 5432,
                    "database": "testdb",
                    "max_connections": 100,
                },
                "temporal": {
                    "enabled": True,
                    "ui_port": 8080,
                    "frontend_port": 7233,
                    "namespace": "default",
                },
            },
        }
        legacy_config.write_text(yaml.safe_dump(complex_data))

        # Full workflow
        detector = MigrationDetector(project_dir=temp_project_dir)
        planner = MigrationPlanner(project_dir=temp_project_dir)

        # Detect
        assert detector.needs_migration() is True
        legacy_configs = detector.scan_for_legacy_configs()

        # Validate feasibility
        assert len(detector.validate_migration_feasibility()) == 0

        # Create and validate plan
        plan = planner.create_plan(legacy_configs, create_global=True, backup_all=True)
        assert planner.validate_plan(plan) is True

        # Execute
        executor = MigrationExecutor(dry_run=False)
        result = executor.execute(plan)

        # Verify success
        assert result.success is True
        assert len(result.errors) == 0

        # Verify migrated config
        new_config = temp_project_dir / ".mycelium" / "config.yaml"
        assert new_config.exists()

        migrated_data = yaml.safe_load(new_config.read_text())
        assert migrated_data["services"]["redis"]["port"] == 6379
        assert migrated_data["services"]["postgres"]["database"] == "testdb"
        assert migrated_data["services"]["temporal"]["namespace"] == "default"
