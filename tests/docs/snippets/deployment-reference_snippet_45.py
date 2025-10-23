# Source: deployment-reference.md
# Line: 673
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.deployment.secrets import SecretsError

try:
    # Generate deployment
    result = generator.generate(DeploymentMethod.KUBERNETES)

    if not result.success:
        print("Validation errors:")
        for error in result.errors:
            print(f"  - {error}")
        sys.exit(1)

    # Generate secrets
    manager = SecretsManager(config.project_name)
    secrets = manager.generate_secrets(postgres=True)
    manager.save_secrets(secrets)

except SecretsError as e:
    print(f"Secrets error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
    raise