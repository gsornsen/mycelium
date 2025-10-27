"""Tests for configuration schema migration framework.

This test suite provides comprehensive coverage of the migration system,
including migration chains, path discovery, dry-run mode, rollback, validation,
and error handling.
"""

from __future__ import annotations

import copy
from datetime import datetime

import pytest

from mycelium_onboarding.config.migrations import (
    Migration,
    Migration_1_0_to_1_1,
    Migration_1_1_to_1_2,
    MigrationError,
    MigrationHistory,
    MigrationPathError,
    MigrationRegistry,
    MigrationValidationError,
    get_default_registry,
)


class TestMigration:
    """Tests for base Migration class."""

    def test_migration_abstract_properties(self):
        """Test that Migration requires abstract properties."""
        with pytest.raises(TypeError):
            Migration()  # type: ignore

    def test_migration_description_default(self):
        """Test default description for migration."""

        class TestMigration(Migration):
            from_version = "1.0"
            to_version = "1.1"

            def migrate(self, config_dict):
                return config_dict

        migration = TestMigration()
        assert migration.description == "Migrate from 1.0 to 1.1"

    def test_migration_validate_before_success(self):
        """Test validate_before with valid config."""

        class TestMigration(Migration):
            from_version = "1.0"
            to_version = "1.1"

            def migrate(self, config_dict):
                return config_dict

        migration = TestMigration()
        config = {"version": "1.0", "data": "test"}

        # Should not raise
        migration.validate_before(config)

    def test_migration_validate_before_missing_version(self):
        """Test validate_before fails when version missing."""

        class TestMigration(Migration):
            from_version = "1.0"
            to_version = "1.1"

            def migrate(self, config_dict):
                return config_dict

        migration = TestMigration()
        config = {"data": "test"}

        with pytest.raises(MigrationValidationError) as exc_info:
            migration.validate_before(config)
        assert "missing 'version' field" in str(exc_info.value).lower()

    def test_migration_validate_before_version_mismatch(self):
        """Test validate_before fails when version mismatches."""

        class TestMigration(Migration):
            from_version = "1.0"
            to_version = "1.1"

            def migrate(self, config_dict):
                return config_dict

        migration = TestMigration()
        config = {"version": "2.0", "data": "test"}

        with pytest.raises(MigrationValidationError) as exc_info:
            migration.validate_before(config)
        assert "version mismatch" in str(exc_info.value).lower()

    def test_migration_validate_after_success(self):
        """Test validate_after with valid config."""

        class TestMigration(Migration):
            from_version = "1.0"
            to_version = "1.1"

            def migrate(self, config_dict):
                config_dict["version"] = "1.1"
                return config_dict

        migration = TestMigration()
        config = {"version": "1.1", "data": "test"}

        # Should not raise
        migration.validate_after(config)

    def test_migration_validate_after_missing_version(self):
        """Test validate_after fails when version missing."""

        class TestMigration(Migration):
            from_version = "1.0"
            to_version = "1.1"

            def migrate(self, config_dict):
                return config_dict

        migration = TestMigration()
        config = {"data": "test"}

        with pytest.raises(MigrationValidationError) as exc_info:
            migration.validate_after(config)
        assert "missing 'version' field" in str(exc_info.value).lower()

    def test_migration_validate_after_version_not_updated(self):
        """Test validate_after fails when version not updated."""

        class TestMigration(Migration):
            from_version = "1.0"
            to_version = "1.1"

            def migrate(self, config_dict):
                return config_dict

        migration = TestMigration()
        config = {"version": "1.0", "data": "test"}

        with pytest.raises(MigrationValidationError) as exc_info:
            migration.validate_after(config)
        assert "version not updated" in str(exc_info.value).lower()

    def test_migration_repr(self):
        """Test migration string representation."""

        class TestMigration(Migration):
            from_version = "1.0"
            to_version = "1.1"

            def migrate(self, config_dict):
                return config_dict

        migration = TestMigration()
        repr_str = repr(migration)
        assert "TestMigration" in repr_str
        assert "1.0" in repr_str
        assert "1.1" in repr_str


class TestMigrationHistory:
    """Tests for MigrationHistory dataclass."""

    def test_history_defaults(self):
        """Test MigrationHistory with default values."""
        history = MigrationHistory(from_version="1.0", to_version="1.1")

        assert history.from_version == "1.0"
        assert history.to_version == "1.1"
        assert history.success is True
        assert history.changes == {}
        assert history.error is None
        assert isinstance(history.timestamp, datetime)

    def test_history_with_values(self):
        """Test MigrationHistory with explicit values."""
        timestamp = datetime.now(UTC)
        changes = {"added": {"monitoring": {}}}

        history = MigrationHistory(
            from_version="1.0",
            to_version="1.1",
            timestamp=timestamp,
            success=True,
            changes=changes,
        )

        assert history.from_version == "1.0"
        assert history.to_version == "1.1"
        assert history.success is True
        assert history.changes == changes
        assert history.timestamp == timestamp

    def test_history_failure(self):
        """Test MigrationHistory for failed migration."""
        history = MigrationHistory(
            from_version="1.0",
            to_version="1.1",
            success=False,
            error="Migration failed",
        )

        assert history.success is False
        assert history.error == "Migration failed"

    def test_history_to_dict(self):
        """Test MigrationHistory serialization."""
        history = MigrationHistory(
            from_version="1.0",
            to_version="1.1",
            changes={"added": {"monitoring": {}}},
        )

        history_dict = history.to_dict()

        assert history_dict["from_version"] == "1.0"
        assert history_dict["to_version"] == "1.1"
        assert history_dict["success"] is True
        assert history_dict["changes"] == {"added": {"monitoring": {}}}
        assert isinstance(history_dict["timestamp"], str)


class TestMigrationRegistry:
    """Tests for MigrationRegistry class."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = MigrationRegistry()
        assert registry.get_registered_migrations() == []
        assert registry.get_history() == []

    def test_register_migration(self):
        """Test registering a migration."""
        registry = MigrationRegistry()

        class TestMigration(Migration):
            from_version = "1.0"
            to_version = "1.1"

            def migrate(self, config_dict):
                return config_dict

        migration = TestMigration()
        registry.register(migration)

        migrations = registry.get_registered_migrations()
        assert len(migrations) == 1
        assert migrations[0] == migration

    def test_register_duplicate_migration(self):
        """Test registering duplicate migration raises error."""
        registry = MigrationRegistry()

        class TestMigration(Migration):
            from_version = "1.0"
            to_version = "1.1"

            def migrate(self, config_dict):
                return config_dict

        registry.register(TestMigration())

        with pytest.raises(ValueError) as exc_info:
            registry.register(TestMigration())
        assert "duplicate" in str(exc_info.value).lower()

    def test_register_invalid_migration_missing_version(self):
        """Test registering migration with missing version fails."""
        registry = MigrationRegistry()

        class TestMigration(Migration):
            from_version = ""
            to_version = "1.1"

            def migrate(self, config_dict):
                return config_dict

        with pytest.raises(ValueError) as exc_info:
            registry.register(TestMigration())
        assert "from_version and to_version" in str(exc_info.value).lower()

    def test_get_migration_path_single_step(self):
        """Test finding single-step migration path."""
        registry = MigrationRegistry()
        registry.register(Migration_1_0_to_1_1())

        path = registry.get_migration_path("1.0", "1.1")

        assert len(path) == 1
        assert path[0].from_version == "1.0"
        assert path[0].to_version == "1.1"

    def test_get_migration_path_multi_step(self):
        """Test finding multi-step migration path (chain)."""
        registry = MigrationRegistry()
        registry.register(Migration_1_0_to_1_1())
        registry.register(Migration_1_1_to_1_2())

        path = registry.get_migration_path("1.0", "1.2")

        assert len(path) == 2
        assert path[0].from_version == "1.0"
        assert path[0].to_version == "1.1"
        assert path[1].from_version == "1.1"
        assert path[1].to_version == "1.2"

    def test_get_migration_path_same_version(self):
        """Test migration path when already at target version."""
        registry = MigrationRegistry()

        path = registry.get_migration_path("1.0", "1.0")

        assert len(path) == 0

    def test_get_migration_path_not_found(self):
        """Test migration path when no path exists."""
        registry = MigrationRegistry()
        registry.register(Migration_1_0_to_1_1())

        with pytest.raises(MigrationPathError) as exc_info:
            registry.get_migration_path("1.0", "2.0")
        assert "no migration path found" in str(exc_info.value).lower()

    def test_get_migration_path_downgrade_not_supported(self):
        """Test migration path rejects downgrades."""
        registry = MigrationRegistry()

        with pytest.raises(MigrationPathError) as exc_info:
            registry.get_migration_path("1.1", "1.0")
        assert "downgrade not supported" in str(exc_info.value).lower()

    def test_get_migration_path_invalid_version_format(self):
        """Test migration path with invalid version format."""
        registry = MigrationRegistry()

        with pytest.raises(ValueError) as exc_info:
            registry.get_migration_path("invalid", "1.0")
        assert "invalid version format" in str(exc_info.value).lower()

    def test_migrate_single_step(self):
        """Test executing single migration."""
        registry = MigrationRegistry()
        registry.register(Migration_1_0_to_1_1())

        config = {"version": "1.0", "project_name": "test"}
        migrated = registry.migrate(config, "1.1")

        assert migrated["version"] == "1.1"
        assert "monitoring" in migrated
        assert migrated["project_name"] == "test"

    def test_migrate_multi_step(self):
        """Test executing migration chain."""
        registry = MigrationRegistry()
        registry.register(Migration_1_0_to_1_1())
        registry.register(Migration_1_1_to_1_2())

        config = {"version": "1.0", "project_name": "test"}
        migrated = registry.migrate(config, "1.2")

        assert migrated["version"] == "1.2"
        assert "monitoring" in migrated  # From 1.0 -> 1.1
        assert "backup" in migrated  # From 1.1 -> 1.2
        assert migrated["project_name"] == "test"

    def test_migrate_already_at_target(self):
        """Test migrating when already at target version."""
        registry = MigrationRegistry()

        config = {"version": "1.0", "project_name": "test"}
        migrated = registry.migrate(config, "1.0")

        assert migrated == config

    def test_migrate_dry_run(self):
        """Test dry-run mode doesn't modify history."""
        registry = MigrationRegistry()
        registry.register(Migration_1_0_to_1_1())

        config = {"version": "1.0", "project_name": "test"}
        original_config = copy.deepcopy(config)

        migrated = registry.migrate(config, "1.1", dry_run=True)

        # Dry run should return migrated config
        assert migrated["version"] == "1.1"
        assert "monitoring" in migrated

        # Original config should be unchanged
        assert config == original_config

        # History should be empty
        assert len(registry.get_history()) == 0

    def test_migrate_records_history(self):
        """Test migration records history."""
        registry = MigrationRegistry()
        registry.register(Migration_1_0_to_1_1())

        config = {"version": "1.0", "project_name": "test"}
        registry.migrate(config, "1.1")

        history = registry.get_history()
        assert len(history) == 1
        assert history[0].from_version == "1.0"
        assert history[0].to_version == "1.1"
        assert history[0].success is True

    def test_migrate_missing_version(self):
        """Test migration fails when config missing version."""
        registry = MigrationRegistry()

        config = {"project_name": "test"}

        with pytest.raises(MigrationValidationError) as exc_info:
            registry.migrate(config, "1.1")
        assert "missing 'version' field" in str(exc_info.value).lower()

    def test_migrate_validation_failure(self):
        """Test migration fails on validation error."""
        registry = MigrationRegistry()

        class BadMigration(Migration):
            from_version = "1.0"
            to_version = "1.1"

            def migrate(self, config_dict):
                # Don't update version - will fail validation
                return config_dict

        registry.register(BadMigration())

        config = {"version": "1.0", "project_name": "test"}

        with pytest.raises(MigrationError) as exc_info:
            registry.migrate(config, "1.1")
        assert "migration failed" in str(exc_info.value).lower()

    def test_needs_migration_true(self):
        """Test needs_migration returns True when migration needed."""
        registry = MigrationRegistry()

        config = {"version": "1.0"}
        assert registry.needs_migration(config, "1.1") is True

    def test_needs_migration_false(self):
        """Test needs_migration returns False when up to date."""
        registry = MigrationRegistry()

        config = {"version": "1.1"}
        assert registry.needs_migration(config, "1.1") is False

    def test_needs_migration_missing_version(self):
        """Test needs_migration when version missing."""
        registry = MigrationRegistry()

        config = {"project_name": "test"}
        assert registry.needs_migration(config, "1.1") is True

    def test_clear_history(self):
        """Test clearing migration history."""
        registry = MigrationRegistry()
        registry.register(Migration_1_0_to_1_1())

        config = {"version": "1.0", "project_name": "test"}
        registry.migrate(config, "1.1")

        assert len(registry.get_history()) == 1

        registry.clear_history()
        assert len(registry.get_history()) == 0

    def test_compute_diff(self):
        """Test computing differences between configurations."""
        registry = MigrationRegistry()

        before = {"version": "1.0", "existing": "value"}
        after = {
            "version": "1.1",
            "existing": "updated",
            "new_field": "new_value",
        }

        diff = registry._compute_diff(before, after)

        assert "added" in diff
        assert "new_field" in diff["added"]
        assert "modified" in diff
        assert "version" in diff["modified"]
        assert "existing" in diff["modified"]
        assert "removed" in diff

    def test_preview_migration(self):
        """Test previewing migration changes."""
        registry = MigrationRegistry()
        registry.register(Migration_1_0_to_1_1())

        config = {"version": "1.0", "project_name": "test"}
        preview = registry.preview_migration(config, "1.1")

        assert "Migration Preview" in preview
        assert "1.0" in preview
        assert "1.1" in preview
        assert "Added fields" in preview or "Modified fields" in preview

    def test_migration_idempotency(self):
        """Test migrating twice produces same result as migrating once."""
        registry1 = MigrationRegistry()
        registry1.register(Migration_1_0_to_1_1())

        registry2 = MigrationRegistry()
        registry2.register(Migration_1_0_to_1_1())

        config = {"version": "1.0", "project_name": "test"}

        # Migrate once
        migrated_once = registry1.migrate(copy.deepcopy(config), "1.1")

        # Migrate to intermediate, then to target (shouldn't change result)
        migrated_twice = registry2.migrate(copy.deepcopy(config), "1.1")

        assert migrated_once == migrated_twice


class TestExampleMigrations:
    """Tests for example migration implementations."""

    def test_migration_1_0_to_1_1(self):
        """Test Migration_1_0_to_1_1 implementation."""
        migration = Migration_1_0_to_1_1()

        assert migration.from_version == "1.0"
        assert migration.to_version == "1.1"

        config = {
            "version": "1.0",
            "project_name": "test",
            "deployment": {"method": "docker-compose"},
        }

        migrated = migration.migrate(copy.deepcopy(config))

        assert migrated["version"] == "1.1"
        assert "monitoring" in migrated
        assert migrated["monitoring"]["enabled"] is False
        assert migrated["monitoring"]["metrics_port"] == 9090
        assert migrated["deployment"]["log_level"] == "INFO"

    def test_migration_1_1_to_1_2(self):
        """Test Migration_1_1_to_1_2 implementation."""
        migration = Migration_1_1_to_1_2()

        assert migration.from_version == "1.1"
        assert migration.to_version == "1.2"

        config = {
            "version": "1.1",
            "project_name": "test",
            "deployment": {"log_level": "INFO"},
        }

        migrated = migration.migrate(copy.deepcopy(config))

        assert migrated["version"] == "1.2"
        assert "backup" in migrated
        assert migrated["backup"]["enabled"] is False
        assert migrated["backup"]["retention_days"] == 30
        assert "logging_level" in migrated["deployment"]
        assert migrated["deployment"]["logging_level"] == "INFO"
        assert "log_level" not in migrated["deployment"]


class TestDefaultRegistry:
    """Tests for default registry factory."""

    def test_get_default_registry(self):
        """Test getting default registry with migrations registered."""
        registry = get_default_registry()

        migrations = registry.get_registered_migrations()
        assert len(migrations) >= 2

        # Check that expected migrations are registered
        versions = [(m.from_version, m.to_version) for m in migrations]
        assert ("1.0", "1.1") in versions
        assert ("1.1", "1.2") in versions

    def test_default_registry_can_migrate_full_chain(self):
        """Test default registry can execute full migration chain."""
        registry = get_default_registry()

        config = {"version": "1.0", "project_name": "test", "deployment": {}}
        migrated = registry.migrate(config, "1.2")

        assert migrated["version"] == "1.2"
        assert "monitoring" in migrated
        assert "backup" in migrated


class TestMigrationErrorHandling:
    """Tests for migration error handling and edge cases."""

    def test_migration_preserves_original_config(self):
        """Test that migration doesn't modify original config."""
        registry = MigrationRegistry()
        registry.register(Migration_1_0_to_1_1())

        config = {"version": "1.0", "project_name": "test"}
        original_config = copy.deepcopy(config)

        registry.migrate(config, "1.1")

        # Original should be unchanged
        assert config == original_config

    def test_migration_failure_records_history(self):
        """Test that failed migration records error in history."""
        registry = MigrationRegistry()

        class FailingMigration(Migration):
            from_version = "1.0"
            to_version = "1.1"

            def migrate(self, config_dict):
                raise ValueError("Intentional failure")

        registry.register(FailingMigration())

        config = {"version": "1.0", "project_name": "test"}

        with pytest.raises(MigrationError):
            registry.migrate(config, "1.1")

        history = registry.get_history()
        assert len(history) == 1
        assert history[0].success is False
        assert history[0].error is not None

    def test_migration_with_empty_config(self):
        """Test migration handling empty config dict."""
        registry = MigrationRegistry()

        config = {"version": "1.0"}

        with pytest.raises(MigrationError):
            # Should fail because no path exists
            registry.migrate(config, "2.0")

    def test_migration_circular_dependency_detection(self):
        """Test that circular migration dependencies are handled."""
        registry = MigrationRegistry()

        class CircularMigration1(Migration):
            from_version = "1.0"
            to_version = "1.1"

            def migrate(self, config_dict):
                config_dict["version"] = "1.1"
                return config_dict

        class CircularMigration2(Migration):
            from_version = "1.1"
            to_version = "1.0"  # Circular!

            def migrate(self, config_dict):
                config_dict["version"] = "1.0"
                return config_dict

        registry.register(CircularMigration1())
        registry.register(CircularMigration2())


        # Should still work (BFS doesn't loop infinitely)
        path = registry.get_migration_path("1.0", "1.1")
        assert len(path) == 1


class TestMigrationIntegration:
    """Integration tests for complete migration workflows."""

    def test_full_migration_workflow(self):
        """Test complete migration workflow from 1.0 to 1.2."""
        registry = get_default_registry()

        # Start with 1.0 config
        config = {
            "version": "1.0",
            "project_name": "mycelium",
            "deployment": {
                "method": "docker-compose",
                "auto_start": True,
            },
            "services": {
                "redis": {"enabled": True, "port": 6379},
                "postgres": {"enabled": True, "port": 5432},
            },
        }

        # Check migration is needed
        assert registry.needs_migration(config, "1.2") is True

        # Preview migration
        preview = registry.preview_migration(config, "1.2")
        assert "Migration Preview" in preview
        assert "1.0" in preview
        assert "1.2" in preview

        # Get migration path
        path = registry.get_migration_path("1.0", "1.2")
        assert len(path) == 2

        # Execute migration
        migrated = registry.migrate(config, "1.2")

        # Verify final state
        assert migrated["version"] == "1.2"
        assert migrated["project_name"] == "mycelium"
        assert migrated["services"]["redis"]["port"] == 6379

        # Check new fields from 1.0 -> 1.1
        assert "monitoring" in migrated
        assert migrated["monitoring"]["enabled"] is False

        # Check new fields from 1.1 -> 1.2
        assert "backup" in migrated
        assert migrated["backup"]["enabled"] is False

        # Check field rename from 1.1 -> 1.2
        assert "logging_level" in migrated["deployment"]
        assert "log_level" not in migrated["deployment"]

        # Verify migration history
        history = registry.get_history()
        assert len(history) == 2
        assert all(record.success for record in history)

    def test_migration_path_discovery_complex(self):
        """Test migration path discovery in complex graph."""
        registry = MigrationRegistry()

        # Create a graph with multiple paths using valid version numbers
        class Mig_1_0_to_1_1(Migration):
            from_version = "1.0"
            to_version = "1.1"

            def migrate(self, config_dict):
                config_dict["version"] = "1.1"
                return config_dict

        class Mig_1_1_to_1_3(Migration):
            from_version = "1.1"
            to_version = "1.3"

            def migrate(self, config_dict):
                config_dict["version"] = "1.3"
                return config_dict

        class Mig_1_0_to_1_2(Migration):
            from_version = "1.0"
            to_version = "1.2"

            def migrate(self, config_dict):
                config_dict["version"] = "1.2"
                return config_dict

        class Mig_1_2_to_1_3(Migration):
            from_version = "1.2"
            to_version = "1.3"

            def migrate(self, config_dict):
                config_dict["version"] = "1.3"
                return config_dict

        registry.register(Mig_1_0_to_1_1())
        registry.register(Mig_1_1_to_1_3())
        registry.register(Mig_1_0_to_1_2())
        registry.register(Mig_1_2_to_1_3())

        # Should find shortest path (1.0 -> 1.1 -> 1.3 or 1.0 -> 1.2 -> 1.3)
        path = registry.get_migration_path("1.0", "1.3")
        assert len(path) == 2
        assert path[0].from_version == "1.0"
        assert path[-1].to_version == "1.3"
