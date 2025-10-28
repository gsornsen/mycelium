# Deployment API Reference

Complete API documentation for the Mycelium deployment system.

## Overview

The deployment system is organized into three main modules:

- **generator.py** - Core deployment generation logic
- **secrets.py** - Secure secrets management
- **renderer.py** - Template rendering engine

## Module: generator.py

### DeploymentGenerator Class

Main class for generating deployment configurations from MyceliumConfig.

```python
from mycelium_onboarding.deployment.generator import DeploymentGenerator, DeploymentMethod
from mycelium_onboarding.config.schema import MyceliumConfig

config = MyceliumConfig(project_name="my-app")
generator = DeploymentGenerator(config)
result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)
```

#### Constructor

```python
def __init__(self, config: MyceliumConfig, output_dir: Path | None = None) -> None
```

**Parameters:**

- `config` (MyceliumConfig): Configuration to generate from
- `output_dir` (Path | None): Output directory for generated files
  - Default: `{XDG_DATA_HOME}/deployments/{project_name}`

**Example:**

```python
# Use default output directory
generator = DeploymentGenerator(config)

# Use custom output directory
generator = DeploymentGenerator(config, output_dir=Path("/tmp/deploy"))
```

#### Methods

##### generate()

Generate deployment configuration for specified method.

```python
def generate(self, method: DeploymentMethod) -> GenerationResult
```

**Parameters:**

- `method` (DeploymentMethod): Deployment method to use
  - `DeploymentMethod.DOCKER_COMPOSE`
  - `DeploymentMethod.KUBERNETES`
  - `DeploymentMethod.SYSTEMD`

**Returns:**

- `GenerationResult`: Result object containing:
  - `success` (bool): Whether generation succeeded
  - `method` (DeploymentMethod): Method used
  - `output_dir` (Path): Output directory path
  - `files_generated` (list\[Path\]): List of generated file paths
  - `errors` (list\[str\]): Error messages (empty if successful)
  - `warnings` (list\[str\]): Warning messages

**Example:**

```python
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
```

##### \_validate_config() (Internal)

Validate configuration for deployment method.

```python
def _validate_config(self, method: DeploymentMethod) -> list[str]
```

**Parameters:**

- `method` (DeploymentMethod): Deployment method to validate for

**Returns:**

- `list[str]`: List of validation errors (empty if valid)

**Validation Rules:**

*General:*

- At least one service must be enabled

*Kubernetes:*

- Project name must be lowercase alphanumeric with hyphens
- No special characters or underscores

*systemd:*

- Project name should be 50 characters or less

**Example:**

```python
errors = generator._validate_config(DeploymentMethod.KUBERNETES)
if errors:
    for error in errors:
        print(f"Validation error: {error}")
```

### GenerationResult Dataclass

Result of deployment generation operation.

```python
@dataclass
class GenerationResult:
    success: bool
    method: DeploymentMethod
    output_dir: Path
    files_generated: list[Path]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
```

**Attributes:**

- `success` (bool): Whether generation completed successfully
- `method` (DeploymentMethod): Deployment method used
- `output_dir` (Path): Directory where files were generated
- `files_generated` (list\[Path\]): Paths to all generated files
- `errors` (list\[str\]): Error messages if generation failed
- `warnings` (list\[str\]): Warning messages (even on success)

**Example:**

```python
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
```

### DeploymentMethod Enum

Supported deployment methods.

```python
class DeploymentMethod(str, Enum):
    DOCKER_COMPOSE = "docker-compose"
    KUBERNETES = "kubernetes"
    SYSTEMD = "systemd"
    MANUAL = "manual"
```

**Usage:**

```python
from mycelium_onboarding.deployment.generator import DeploymentMethod

# Use enum values
method = DeploymentMethod.KUBERNETES
print(method.value)  # "kubernetes"

# Create from string
method = DeploymentMethod("docker-compose")

# Compare
if method == DeploymentMethod.DOCKER_COMPOSE:
    print("Using Docker Compose")
```

## Module: secrets.py

### SecretsManager Class

Manages deployment secrets with cryptographic security.

```python
from mycelium_onboarding.deployment.secrets import SecretsManager

manager = SecretsManager("my-project")
secrets = manager.generate_secrets(postgres=True, redis=True)
manager.save_secrets(secrets)
```

#### Constructor

```python
def __init__(self, project_name: str, secrets_dir: Path | None = None) -> None
```

**Parameters:**

- `project_name` (str): Project name for secrets
- `secrets_dir` (Path | None): Directory for secrets storage
  - Default: `{XDG_STATE_HOME}/secrets`

**Example:**

```python
# Use default directory
manager = SecretsManager("my-app")

# Use custom directory
manager = SecretsManager("my-app", secrets_dir=Path("/secure/location"))
```

#### Methods

##### generate_secrets()

Generate new secrets for enabled services.

```python
def generate_secrets(
    self,
    postgres: bool = False,
    redis: bool = False,
    temporal: bool = False,
    overwrite: bool = False,
) -> DeploymentSecrets
```

**Parameters:**

- `postgres` (bool): Generate PostgreSQL password
- `redis` (bool): Generate Redis password
- `temporal` (bool): Generate Temporal admin password
- `overwrite` (bool): Overwrite existing secrets

**Returns:**

- `DeploymentSecrets`: Generated secrets object

**Example:**

```python
# Generate secrets for PostgreSQL and Redis
secrets = manager.generate_secrets(postgres=True, redis=True)

# Preserve existing secrets (default)
secrets = manager.generate_secrets(postgres=True, overwrite=False)

# Force regenerate all secrets
secrets = manager.generate_secrets(
    postgres=True,
    redis=True,
    temporal=True,
    overwrite=True
)
```

##### save_secrets()

Save secrets to encrypted storage with secure permissions.

```python
def save_secrets(self, secrets_obj: DeploymentSecrets) -> None
```

**Parameters:**

- `secrets_obj` (DeploymentSecrets): Secrets to save

**Raises:**

- `SecretsError`: If save operation fails

**Security:**

- Directory permissions: `0o700` (owner only)
- File permissions: `0o600` (owner read/write only)

**Example:**

```python
secrets = manager.generate_secrets(postgres=True)

try:
    manager.save_secrets(secrets)
    print("Secrets saved securely")
except SecretsError as e:
    print(f"Failed to save: {e}")
```

##### load_secrets()

Load secrets from storage.

```python
def load_secrets(self) -> DeploymentSecrets | None
```

**Returns:**

- `DeploymentSecrets | None`: Loaded secrets or None if not found

**Example:**

```python
secrets = manager.load_secrets()

if secrets:
    print(f"Loaded secrets for: {secrets.project_name}")
    env_vars = secrets.to_env_vars()
else:
    print("No secrets found")
```

##### rotate_secret()

Rotate a specific secret while preserving others.

```python
def rotate_secret(self, secret_type: str) -> DeploymentSecrets
```

**Parameters:**

- `secret_type` (str): Type of secret to rotate
  - `"postgres"` - PostgreSQL password
  - `"redis"` - Redis password
  - `"temporal"` - Temporal admin password

**Returns:**

- `DeploymentSecrets`: Updated secrets object

**Raises:**

- `ValueError`: If no existing secrets or invalid type
- `SecretsError`: If rotation fails

**Example:**

```python
# Rotate PostgreSQL password
try:
    rotated = manager.rotate_secret("postgres")
    print("Password rotated successfully")
except ValueError as e:
    print(f"Rotation failed: {e}")
```

##### delete_secrets()

Delete stored secrets.

```python
def delete_secrets(self) -> bool
```

**Returns:**

- `bool`: True if deleted, False if not found

**Example:**

```python
if manager.delete_secrets():
    print("Secrets deleted")
else:
    print("No secrets to delete")
```

### DeploymentSecrets Dataclass

Container for deployment secrets.

```python
@dataclass
class DeploymentSecrets:
    project_name: str
    postgres_password: str | None = None
    redis_password: str | None = None
    temporal_admin_password: str | None = None
```

**Attributes:**

- `project_name` (str): Project name
- `postgres_password` (str | None): PostgreSQL password
- `redis_password` (str | None): Redis password
- `temporal_admin_password` (str | None): Temporal admin password

#### Methods

##### to_env_vars()

Convert secrets to environment variable dictionary.

```python
def to_env_vars(self) -> dict[str, str]
```

**Returns:**

- `dict[str, str]`: Environment variables (excludes None values)

**Example:**

```python
secrets = DeploymentSecrets(
    project_name="my-app",
    postgres_password="secret123",
    redis_password="secret456"
)

env_vars = secrets.to_env_vars()
# {
#     "POSTGRES_PASSWORD": "secret123",
#     "REDIS_PASSWORD": "secret456"
# }

# Use in deployment
import os
for key, value in env_vars.items():
    os.environ[key] = value
```

### Utility Functions

#### generate_env_file()

Generate .env file from secrets.

```python
def generate_env_file(secrets: DeploymentSecrets, output_path: Path) -> None
```

**Parameters:**

- `secrets` (DeploymentSecrets): Secrets to write
- `output_path` (Path): Path to .env file

**Raises:**

- `SecretsError`: If file creation fails

**Example:**

```python
from mycelium_onboarding.deployment.secrets import generate_env_file

secrets = manager.load_secrets()
generate_env_file(secrets, Path(".env"))
```

### SecretsError Exception

Exception raised when secrets operations fail.

```python
class SecretsError(Exception):
    pass
```

**Example:**

```python
from mycelium_onboarding.deployment.secrets import SecretsError

try:
    manager.save_secrets(secrets)
except SecretsError as e:
    print(f"Secrets operation failed: {e}")
    # Handle error...
```

## Module: renderer.py

### TemplateRenderer Class

Renders Jinja2 templates for deployment configurations.

```python
from mycelium_onboarding.deployment.renderer import TemplateRenderer

renderer = TemplateRenderer()
content = renderer.render_docker_compose(config)
```

#### Constructor

```python
def __init__(self, templates_dir: Path | None = None) -> None
```

**Parameters:**

- `templates_dir` (Path | None): Custom templates directory
  - Default: Built-in templates directory

**Example:**

```python
# Use built-in templates
renderer = TemplateRenderer()

# Use custom templates
renderer = TemplateRenderer(templates_dir=Path("./my-templates"))
```

#### Methods

##### render_docker_compose()

Render Docker Compose configuration.

```python
def render_docker_compose(self, config: MyceliumConfig) -> str
```

**Parameters:**

- `config` (MyceliumConfig): Configuration to render

**Returns:**

- `str`: Rendered docker-compose.yml content

**Example:**

```python
config = MyceliumConfig(
    project_name="my-app",
    services={"redis": {"enabled": True}}
)

compose_yaml = renderer.render_docker_compose(config)
Path("docker-compose.yml").write_text(compose_yaml)
```

##### render_kubernetes()

Render Kubernetes manifests.

```python
def render_kubernetes(self, config: MyceliumConfig) -> dict[str, str]
```

**Parameters:**

- `config` (MyceliumConfig): Configuration to render

**Returns:**

- `dict[str, str]`: Mapping of filename to manifest content

**Example:**

```python
manifests = renderer.render_kubernetes(config)

for filename, content in manifests.items():
    output_path = Path(f"kubernetes/{filename}")
    output_path.write_text(content)
```

##### render_systemd()

Render systemd service files.

```python
def render_systemd(self, config: MyceliumConfig) -> dict[str, str]
```

**Parameters:**

- `config` (MyceliumConfig): Configuration to render

**Returns:**

- `dict[str, str]`: Mapping of service filename to content

**Example:**

```python
services = renderer.render_systemd(config)

for service_name, content in services.items():
    output_path = Path(f"systemd/{service_name}")
    output_path.write_text(content)
```

## Usage Examples

### Basic Deployment Generation

```python
from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.deployment.generator import (
    DeploymentGenerator,
    DeploymentMethod
)

# Create configuration
config = MyceliumConfig(
    project_name="my-app",
    services={
        "redis": {"enabled": True, "port": 6379},
        "postgres": {"enabled": True, "database": "mydb"}
    },
    deployment={"method": "docker-compose"}
)

# Generate deployment
generator = DeploymentGenerator(config)
result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

if result.success:
    print(f"Generated files in: {result.output_dir}")
    for file in result.files_generated:
        print(f"  - {file}")
else:
    print(f"Failed: {result.errors}")
```

### Secrets Management

```python
from mycelium_onboarding.deployment.secrets import SecretsManager

# Initialize manager
manager = SecretsManager("my-app")

# Generate secrets
secrets = manager.generate_secrets(
    postgres=True,
    redis=True,
    temporal=True
)

# Save securely
manager.save_secrets(secrets)

# Load later
loaded = manager.load_secrets()
if loaded:
    env_vars = loaded.to_env_vars()
    print("Environment variables:", env_vars.keys())
```

### Multiple Deployment Methods

```python
from pathlib import Path

config = MyceliumConfig(project_name="multi-deploy")

# Generate Docker Compose
generator = DeploymentGenerator(config, output_dir=Path("./compose"))
compose_result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

# Generate Kubernetes
generator = DeploymentGenerator(config, output_dir=Path("./k8s"))
k8s_result = generator.generate(DeploymentMethod.KUBERNETES)

# Generate systemd
generator = DeploymentGenerator(config, output_dir=Path("./systemd"))
systemd_result = generator.generate(DeploymentMethod.SYSTEMD)
```

### Custom Template Rendering

```python
from mycelium_onboarding.deployment.renderer import TemplateRenderer

renderer = TemplateRenderer()

# Render Docker Compose
compose_content = renderer.render_docker_compose(config)

# Render Kubernetes
k8s_manifests = renderer.render_kubernetes(config)

# Process manifests
for name, content in k8s_manifests.items():
    print(f"Manifest: {name}")
    print(f"Size: {len(content)} bytes")
```

### Error Handling

```python
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
```

## Type Hints and Imports

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

from mycelium_onboarding.config.schema import (
    MyceliumConfig,
    DeploymentMethod,
    ServicesConfig,
)
from mycelium_onboarding.deployment.generator import (
    DeploymentGenerator,
    GenerationResult,
)
from mycelium_onboarding.deployment.secrets import (
    SecretsManager,
    DeploymentSecrets,
    SecretsError,
    generate_env_file,
)
from mycelium_onboarding.deployment.renderer import TemplateRenderer
```

## See Also

- [Deployment Guide](deployment-guide.md) - User-facing documentation
- [Integration Guide](deployment-integration.md) - Integration patterns
- [Configuration Schema](../mycelium_onboarding/config/schema.py) - Config reference

______________________________________________________________________

*API Reference for Mycelium Deployment System*
