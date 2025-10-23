# Source: migration-guide.md
# Line: 508
# Valid syntax: True
# Has imports: True
# Has assignments: True

import pytest
from mycelium_onboarding.config.migrations import Migration_1_2_to_1_3

def test_migration_1_2_to_1_3():
    """Test migration from 1.2 to 1.3."""
    # Setup: 1.2 config
    config_1_2 = {
        "version": "1.2",
        "project_name": "test",
        "deployment": {"method": "docker-compose"},
    }

    # Execute migration
    migration = Migration_1_2_to_1_3()
    migrated = migration.migrate(config_1_2.copy())

    # Verify: security section added
    assert "security" in migrated
    assert migrated["security"]["ssl_enabled"] is False

    # Verify: version updated
    assert migrated["version"] == "1.3"

    # Verify: existing fields preserved
    assert migrated["project_name"] == "test"
    assert migrated["deployment"]["method"] == "docker-compose"