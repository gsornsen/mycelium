# Source: migration-guide.md
# Line: 487
# Valid syntax: True
# Has imports: False
# Has assignments: True

# In mycelium_onboarding/config/migrations.py

def get_default_registry() -> MigrationRegistry:
    """Get default migration registry with all migrations."""
    registry = MigrationRegistry()

    # Existing migrations
    registry.register(Migration_1_0_to_1_1())
    registry.register(Migration_1_1_to_1_2())

    # Your custom migration
    registry.register(Migration_1_2_to_1_3())

    return registry
