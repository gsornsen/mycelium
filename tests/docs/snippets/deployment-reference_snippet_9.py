# Source: deployment-reference.md
# Line: 147
# Valid syntax: True
# Has imports: False
# Has assignments: True

result = generator.generate(DeploymentMethod.KUBERNETES)

# Check result
if result.success:
    print(f"Success! Generated {len(result.files_generated)} files:")
    for file in result.files_generated:
        print(f"  - {file.name}")

    # Handle warnings
    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  ! {warning}")
else:
    print("Generation failed:")
    for error in result.errors:
        print(f"  × {error}")