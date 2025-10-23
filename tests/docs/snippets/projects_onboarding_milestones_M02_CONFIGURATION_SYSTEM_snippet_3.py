# Source: projects/onboarding/milestones/M02_CONFIGURATION_SYSTEM.md
# Line: 372
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Load configuration (auto-detects location)
config = ConfigManager.load()

# Modify configuration
config.deployment.method = DeploymentMethod.JUSTFILE
config.services.redis.port = 6380

# Save to user-global config
ConfigManager.save(config, project_local=False)

# Save to project-local config
ConfigManager.save(config, project_local=True)