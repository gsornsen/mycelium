# Source: projects/onboarding/milestones/M02_CONFIGURATION_SYSTEM.md
# Line: 539
# Valid syntax: True
# Has imports: True
# Has assignments: True

# In mycelium_onboarding/config/manager.py

from mycelium_onboarding.config.migrations import migrate_config

class ConfigManager:
    @classmethod
    def load_from_path(cls, path: Path) -> MyceliumConfig:
        """Load configuration from specific path with migration."""
        # ... existing code to load YAML ...

        # Apply migrations if needed
        if data.get("version") != "1.0":
            logger.info(f"Migrating configuration from {data.get('version')} to 1.0")
            data = migrate_config(data)

        try:
            return MyceliumConfig.model_validate(data)
        except ValidationError as e:
            raise ConfigValidationError(
                f"Configuration validation failed in {path}:\n{e}"
            ) from e