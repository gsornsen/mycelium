# Source: wizard-integration.md
# Line: 177
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.wizard.flow import WizardState
from mycelium_onboarding.wizard.validation import WizardValidator
from mycelium_onboarding.config.manager import ConfigManager

def create_config_from_template(template_name: str):
    """Create configuration from predefined template."""
    # Define templates
    templates = {
        "minimal": {
            "project_name": "minimal-project",
            "services": {"redis": True, "postgres": False, "temporal": False},
            "deployment": "docker-compose",
        },
        "full-stack": {
            "project_name": "full-stack-project",
            "services": {"redis": True, "postgres": True, "temporal": True},
            "deployment": "kubernetes",
            "postgres_database": "fullstack_db",
            "temporal_namespace": "production",
        },
        "development": {
            "project_name": "dev-project",
            "services": {"redis": True, "postgres": True, "temporal": False},
            "deployment": "docker-compose",
            "postgres_database": "dev_db",
            "auto_start": False,
        },
    }

    if template_name not in templates:
        raise ValueError(f"Unknown template: {template_name}")

    template = templates[template_name]

    # Build state
    state = WizardState()
    state.project_name = template["project_name"]
    state.services_enabled = template["services"]
    state.deployment_method = template["deployment"]

    if "postgres_database" in template:
        state.postgres_database = template["postgres_database"]
    if "temporal_namespace" in template:
        state.temporal_namespace = template["temporal_namespace"]
    if "auto_start" in template:
        state.auto_start = template["auto_start"]

    # Validate
    validator = WizardValidator(state)
    if not validator.validate_state():
        raise ValueError(f"Invalid template: {validator.get_error_messages()}")

    # Convert to config
    config = state.to_config()

    # Save
    manager = ConfigManager()
    manager.save(config)

    return config

# Usage
config = create_config_from_template("full-stack")
print(f"Created config: {config.project_name}")