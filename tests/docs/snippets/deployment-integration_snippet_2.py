# Source: deployment-integration.md
# Line: 66
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.config.manager import ConfigManager


def load_and_generate():
    """Load config from file and generate deployment."""
    manager = ConfigManager()

    try:
        # Load configuration
        config = manager.load()

        # Generate deployment
        generator = DeploymentGenerator(config)
        result = generator.generate(
            DeploymentMethod(config.deployment.method)
        )

        return result

    except FileNotFoundError:
        print("Configuration not found. Run: mycelium init")
        return None
