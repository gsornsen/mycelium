# Source: deployment-integration.md
# Line: 581
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.deployment.secrets import SecretsManager

def deploy_production(config: MyceliumConfig):
    """Production deployment with separate secrets."""
    # Generate deployment files
    generator = DeploymentGenerator(
        config,
        output_dir=Path("/secure/deployments")
    )
    result = generator.generate(DeploymentMethod.KUBERNETES)

    # Generate secrets separately
    secrets_mgr = SecretsManager(
        config.project_name,
        secrets_dir=Path("/secure/secrets")
    )
    secrets = secrets_mgr.generate_secrets(
        postgres=config.services.postgres.enabled,
        redis=config.services.redis.enabled
    )
    secrets_mgr.save_secrets(secrets)

    return result