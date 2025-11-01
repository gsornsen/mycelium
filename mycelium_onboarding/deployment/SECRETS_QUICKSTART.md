# Secrets Management Quick Start

## Installation

No additional dependencies required - uses Python standard library only.

## Basic Usage

### 1. Generate Secrets

```python
from mycelium_onboarding.deployment.secrets import SecretsManager

# Create manager for your project
manager = SecretsManager("my-temporal-app")

# Generate secrets for services you need
secrets = manager.generate_secrets(
    postgres=True,   # PostgreSQL database
    redis=True,      # Redis cache
    temporal=True    # Temporal workflow engine
)

# Save to secure storage (~/.local/state/mycelium/secrets/)
manager.save_secrets(secrets)
```

### 2. Load Existing Secrets

```python
# Load previously saved secrets
manager = SecretsManager("my-temporal-app")
secrets = manager.load_secrets()

if secrets:
    print(f"Loaded secrets for: {secrets.project_name}")
else:
    print("No secrets found - generate new ones")
```

### 3. Create .env File

```python
from pathlib import Path
from mycelium_onboarding.deployment.secrets import generate_env_file

# Generate .env file with secure permissions
env_file = Path(".env")
generate_env_file(secrets, env_file)

# Result: .env file with 0o600 permissions
# POSTGRES_PASSWORD=...
# REDIS_PASSWORD=...
# TEMPORAL_ADMIN_PASSWORD=...
```

### 4. Use in Application

```python
import os

# Load secrets
manager = SecretsManager("my-temporal-app")
secrets = manager.load_secrets()

# Convert to environment variables
env_vars = secrets.to_env_vars()

# Set in environment
os.environ.update(env_vars)

# Or use directly
db_url = f"postgresql://user:{secrets.postgres_password}@localhost/db"
```

### 5. Rotate Secrets

```python
# Rotate a specific secret (e.g., after potential compromise)
manager = SecretsManager("my-temporal-app")

# Rotate PostgreSQL password
new_secrets = manager.rotate_secret("postgres")

# Automatically saved - update your services
print(f"New password generated and saved")
```

## Common Patterns

### Development vs Production

```python
import os

# Use different secrets for each environment
env = os.getenv("ENV", "development")
manager = SecretsManager(f"myapp-{env}")

secrets = manager.load_secrets()
if not secrets:
    # First time - generate new secrets
    secrets = manager.generate_secrets(
        postgres=True,
        redis=True,
        temporal=True
    )
    manager.save_secrets(secrets)
```

### Docker Compose Integration

```python
from mycelium_onboarding.deployment.secrets import (
    SecretsManager,
    generate_env_file,
)
from pathlib import Path

# Generate secrets
manager = SecretsManager("docker-app")
secrets = manager.generate_secrets(postgres=True, redis=True)
manager.save_secrets(secrets)

# Create .env for docker-compose
generate_env_file(secrets, Path(".env"))

# Now run: docker-compose up
# Services will use environment variables from .env
```

### Automated Secret Rotation

```python
from datetime import datetime, timedelta

def rotate_if_old(manager: SecretsManager, max_age_days: int = 90) -> None:
    """Rotate secrets if older than max_age_days."""
    secrets_file = manager.secrets_file

    if not secrets_file.exists():
        return

    # Check file modification time
    mtime = datetime.fromtimestamp(secrets_file.stat().st_mtime)
    age = datetime.now(UTC) - mtime

    if age > timedelta(days=max_age_days):
        print(f"Secrets are {age.days} days old - rotating")
        for secret_type in ["postgres", "redis", "temporal"]:
            try:
                manager.rotate_secret(secret_type)
                print(f"Rotated {secret_type}")
            except ValueError:
                pass  # Secret doesn't exist

# Usage
manager = SecretsManager("production-app")
rotate_if_old(manager, max_age_days=90)
```

## Security Checklist

- [ ] Secrets stored in `.gitignore`
- [ ] File permissions are 0o600 (check with `ls -la`)
- [ ] Using `secrets` module (not `random`)
- [ ] Separate secrets per environment
- [ ] Rotation schedule defined (e.g., quarterly)
- [ ] Incident response plan documented
- [ ] No secrets in logs or error messages
- [ ] Production uses external secrets manager (Vault, AWS, etc.)

## Troubleshooting

### Permissions Error

```python
# Problem: Permission denied when saving
# Solution: Check directory permissions

import stat
dir_mode = manager.secrets_dir.stat().st_mode
print(f"Directory permissions: {oct(stat.S_IMODE(dir_mode))}")

# Should be 0o700 - if not, fix:
manager.secrets_dir.chmod(0o700)
```

### Cannot Load Secrets

```python
# Problem: load_secrets() returns None
# Possible causes:

# 1. File doesn't exist
if not manager.secrets_file.exists():
    print("Secrets file not found - generate new secrets")

# 2. Corrupted JSON
try:
    import json
    with manager.secrets_file.open() as f:
        data = json.load(f)
except json.JSONDecodeError:
    print("Corrupted secrets file - regenerate")
    manager.delete_secrets()
    secrets = manager.generate_secrets(postgres=True)
    manager.save_secrets(secrets)
```

### Missing Secret Type

```python
# Problem: Need to add new secret type
# Current limitation: Only postgres, redis, temporal supported

# Workaround: Use custom storage
secrets = manager.load_secrets()
if secrets:
    # Store additional secrets in environment
    os.environ["CUSTOM_SECRET"] = generate_custom_secret()
```

## Examples

See `/home/gerald/git/mycelium/examples/secrets_example.py` for complete working examples.

## Documentation

- **Security Guide**: `SECRETS_SECURITY.md`
- **API Reference**: Module docstrings
- **Implementation**: `secrets.py`

## Support

- File issues on GitHub
- Email: security@mycelium.dev (for security concerns)
