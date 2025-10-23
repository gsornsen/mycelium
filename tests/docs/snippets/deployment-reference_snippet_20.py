# Source: deployment-reference.md
# Line: 312
# Valid syntax: True
# Has imports: False
# Has assignments: True

secrets = manager.load_secrets()

if secrets:
    print(f"Loaded secrets for: {secrets.project_name}")
    env_vars = secrets.to_env_vars()
else:
    print("No secrets found")
