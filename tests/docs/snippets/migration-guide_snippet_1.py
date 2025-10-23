# Source: migration-guide.md
# Line: 57
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.config.manager import ConfigManager

manager = ConfigManager()
config = manager.load_and_migrate()  # Auto-migrates to latest