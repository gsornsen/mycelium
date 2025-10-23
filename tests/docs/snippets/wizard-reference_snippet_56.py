# Source: wizard-reference.md
# Line: 1195
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.wizard.flow import WizardState

# Build state programmatically
state = WizardState()
state.project_name = "my-project"
state.setup_mode = "quick"
state.services_enabled = {
    "redis": True,
    "postgres": True,
    "temporal": False,
}
state.deployment_method = "docker-compose"
state.postgres_database = "my_db"
state.auto_start = True

# Convert to config
config = state.to_config()

# Save config
from mycelium_onboarding.config.manager import ConfigManager
manager = ConfigManager()
manager.save(config)