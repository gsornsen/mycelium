# Source: deployment-integration.md
# Line: 664
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.deployment.secrets import SecretsError
from mycelium_onboarding.config.manager import (
    ConfigLoadError,
    ConfigValidationError
)

def safe_deployment_generation(project_name: str):
    """Safely generate deployment with error handling."""
    try:
        # Load configuration
        manager = ConfigManager()
        config = manager.load()

    except FileNotFoundError:
        print("Error: Configuration file not found")
        print("Run: mycelium init")
        return None

    except ConfigLoadError as e:
        print(f"Error loading configuration: {e}")
        return None

    except ConfigValidationError as e:
        print(f"Configuration validation failed: {e}")
        return None

    try:
        # Generate deployment
        generator = DeploymentGenerator(config)
        result = generator.generate(
            DeploymentMethod(config.deployment.method)
        )

        if not result.success:
            print("Deployment generation failed:")
            for error in result.errors:
                print(f"  - {error}")
            return None

        # Generate secrets
        secrets_mgr = SecretsManager(project_name)
        secrets = secrets_mgr.generate_secrets(
            postgres=config.services.postgres.enabled,
            redis=config.services.redis.enabled
        )
        secrets_mgr.save_secrets(secrets)

        return result

    except SecretsError as e:
        print(f"Secrets error: {e}")
        return None

    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None