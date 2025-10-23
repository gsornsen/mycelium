# Source: deployment-reference.md
# Line: 116
# Valid syntax: True
# Has imports: False
# Has assignments: True

errors = generator._validate_config(DeploymentMethod.KUBERNETES)
if errors:
    for error in errors:
        print(f"Validation error: {error}")
