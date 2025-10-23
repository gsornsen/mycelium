# Source: deployment-integration.md
# Line: 609
# Valid syntax: True
# Has imports: False
# Has assignments: True

def validate_and_deploy(config: MyceliumConfig) -> bool:
    """Validate configuration before deploying."""
    # Validate configuration
    generator = DeploymentGenerator(config)
    errors = generator._validate_config(
        DeploymentMethod(config.deployment.method)
    )

    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
        return False

    # Generate deployment
    result = generator.generate(
        DeploymentMethod(config.deployment.method)
    )

    return result.success