# Source: deployment-reference.md
# Line: 235
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: expected ':' (<unknown>, line 7)

def generate_secrets(
    self,
    postgres: bool = False,
    redis: bool = False,
    temporal: bool = False,
    overwrite: bool = False,
) -> DeploymentSecrets