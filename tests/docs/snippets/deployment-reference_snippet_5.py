# Source: deployment-reference.md
# Line: 74
# Valid syntax: True
# Has imports: False
# Has assignments: True

result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

if result.success:
    print(f"Generated {len(result.files_generated)} files")
    print(f"Output: {result.output_dir}")
else:
    print("Errors:", result.errors)

# Check warnings
if result.warnings:
    for warning in result.warnings:
        print(f"Warning: {warning}")
