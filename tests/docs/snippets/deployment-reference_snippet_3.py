# Source: deployment-reference.md
# Line: 40
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Use default output directory
generator = DeploymentGenerator(config)

# Use custom output directory
generator = DeploymentGenerator(config, output_dir=Path("/tmp/deploy"))
