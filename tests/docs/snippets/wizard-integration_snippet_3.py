# Source: wizard-integration.md
# Line: 248
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.wizard.flow import WizardState
from mycelium_onboarding.wizard.validation import WizardValidator


def headless_wizard(answers: dict):
    """Run wizard with predefined answers (for CI/CD)."""
    state = WizardState()

    # Apply answers
    state.project_name = answers.get("project_name", "mycelium-project")
    state.setup_mode = answers.get("setup_mode", "quick")
    state.services_enabled = answers.get("services", {
        "redis": True,
        "postgres": True,
        "temporal": False,
    })
    state.deployment_method = answers.get("deployment", "docker-compose")
    state.postgres_database = answers.get("postgres_database", "mycelium")
    state.auto_start = answers.get("auto_start", True)
    state.enable_persistence = answers.get("enable_persistence", True)

    # Advanced settings
    if "redis_port" in answers:
        state.redis_port = answers["redis_port"]
    if "postgres_port" in answers:
        state.postgres_port = answers["postgres_port"]

    # Validate
    validator = WizardValidator(state)
    if not validator.validate_state():
        raise ValueError(f"Invalid configuration: {validator.get_error_messages()}")

    # Convert and return
    return state.to_config()

# Usage in CI/CD
answers = {
    "project_name": "ci-test-project",
    "services": {"redis": True, "postgres": False, "temporal": False},
    "deployment": "systemd",
}

config = headless_wizard(answers)
