# Source: projects/onboarding/milestones/M08_DOCUMENTATION.md
# Line: 744
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.config.manager import ConfigManager

# Load configuration
config = ConfigManager.load()
print(f"Project: {config.project_name}")