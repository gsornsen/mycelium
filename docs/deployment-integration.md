# Deployment Integration Guide

Guide for integrating Mycelium deployment generation into your applications and workflows.

## Overview

The Mycelium deployment system can be integrated into your applications, CI/CD pipelines, and automation workflows. This
guide covers:

- Programmatic usage patterns
- Custom template development
- CI/CD integration
- Best practices for production

## Programmatic Usage

### Basic Integration

Integrate deployment generation into your Python application:

```python
from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.deployment.generator import (
    DeploymentGenerator,
    DeploymentMethod
)

def setup_deployment(project_name: str, services: dict) -> bool:
    """Set up deployment for a project."""
    try:
        # Create configuration
        config = MyceliumConfig(
            project_name=project_name,
            services=services,
            deployment={"method": "docker-compose"}
        )

        # Generate deployment
        generator = DeploymentGenerator(config)
        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        if result.success:
            print(f"Deployment generated at: {result.output_dir}")
            return True
        else:
            print(f"Errors: {result.errors}")
            return False

    except Exception as e:
        print(f"Failed to generate deployment: {e}")
        return False

# Usage
success = setup_deployment(
    project_name="my-microservice",
    services={
        "redis": {"enabled": True, "port": 6379},
        "postgres": {"enabled": True}
    }
)
```

### Loading Configuration

Load configuration from existing files:

```python
from mycelium_onboarding.config.manager import ConfigManager

def load_and_generate():
    """Load config from file and generate deployment."""
    manager = ConfigManager()

    try:
        # Load configuration
        config = manager.load()

        # Generate deployment
        generator = DeploymentGenerator(config)
        result = generator.generate(
            DeploymentMethod(config.deployment.method)
        )

        return result

    except FileNotFoundError:
        print("Configuration not found. Run: mycelium init")
        return None
```

### Multi-Environment Deployments

Generate deployments for multiple environments:

```python
from pathlib import Path

def generate_environments(base_config: MyceliumConfig):
    """Generate deployments for dev, staging, and production."""
    environments = {
        "dev": {
            "method": DeploymentMethod.DOCKER_COMPOSE,
            "output": Path("./deploy/dev"),
            "modifications": {
                "services": {
                    "redis": {"max_memory": "128mb"},
                    "postgres": {"max_connections": 50}
                }
            }
        },
        "staging": {
            "method": DeploymentMethod.KUBERNETES,
            "output": Path("./deploy/staging"),
            "modifications": {
                "services": {
                    "redis": {"max_memory": "512mb"},
                    "postgres": {"max_connections": 200}
                }
            }
        },
        "production": {
            "method": DeploymentMethod.KUBERNETES,
            "output": Path("./deploy/production"),
            "modifications": {
                "services": {
                    "redis": {"max_memory": "2gb"},
                    "postgres": {"max_connections": 500}
                }
            }
        }
    }

    results = {}

    for env_name, env_config in environments.items():
        # Create environment-specific config
        env_cfg = base_config.model_copy(deep=True)
        env_cfg.project_name = f"{base_config.project_name}-{env_name}"

        # Apply modifications
        for key, value in env_config["modifications"]["services"].items():
            service = getattr(env_cfg.services, key)
            for attr, val in value.items():
                setattr(service, attr, val)

        # Generate deployment
        generator = DeploymentGenerator(
            env_cfg,
            output_dir=env_config["output"]
        )
        results[env_name] = generator.generate(env_config["method"])

    return results
```

### Async Deployment Generation

For async frameworks like FastAPI or asyncio:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def generate_deployment_async(
    config: MyceliumConfig,
    method: DeploymentMethod
) -> GenerationResult:
    """Generate deployment asynchronously."""
    loop = asyncio.get_event_loop()

    def _generate():
        generator = DeploymentGenerator(config)
        return generator.generate(method)

    # Run in thread pool to avoid blocking
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, _generate)

    return result

# Usage with FastAPI
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

@app.post("/deploy/{project_name}")
async def create_deployment(
    project_name: str,
    config: dict,
    background_tasks: BackgroundTasks
):
    """API endpoint to generate deployment."""
    # Validate config
    mycelium_config = MyceliumConfig(
        project_name=project_name,
        **config
    )

    # Generate asynchronously
    result = await generate_deployment_async(
        mycelium_config,
        DeploymentMethod.DOCKER_COMPOSE
    )

    return {
        "success": result.success,
        "output_dir": str(result.output_dir),
        "files": [str(f) for f in result.files_generated]
    }
```

## Extending Templates

### Custom Template Directory

Use custom templates for specialized deployments:

```python
from mycelium_onboarding.deployment.renderer import TemplateRenderer

# Point to custom templates
renderer = TemplateRenderer(
    templates_dir=Path("./my-templates")
)

# Render with custom templates
content = renderer.render_docker_compose(config)
```

### Template Structure

Create custom templates following the same structure:

```
my-templates/
├── docker-compose.yml.j2
├── kubernetes/
│   ├── namespace.yaml.j2
│   ├── redis.yaml.j2
│   ├── postgres.yaml.j2
│   └── temporal.yaml.j2
└── systemd/
    ├── redis.service.j2
    ├── postgres.service.j2
    └── temporal.service.j2
```

### Custom Template Example

Create a custom Docker Compose template with additional features:

```jinja2
{# my-templates/docker-compose.yml.j2 #}
version: '3.8'

services:
  {% if config.services.redis.enabled %}
  redis:
    image: redis:{{ config.services.redis.version or '7-alpine' }}
    ports:
      - "{{ config.services.redis.port }}:6379"
    volumes:
      - redis-data:/data
    # Custom: Add healthcheck
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    # Custom: Resource limits
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: {{ config.services.redis.max_memory }}
  {% endif %}

  # Custom: Add monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

volumes:
  {% if config.services.redis.enabled %}
  redis-data:
  {% endif %}
  prometheus-data:
```

### Template Variables

Available variables in templates:

```python
# In Jinja2 templates, access:
{{ config.project_name }}              # Project name
{{ config.services.redis.enabled }}    # Service enabled status
{{ config.services.redis.port }}       # Redis port
{{ config.services.redis.max_memory }} # Redis memory limit
{{ config.services.postgres.database }}# PostgreSQL database name
{{ config.deployment.method }}         # Deployment method
```

### Template Filters

Add custom Jinja2 filters:

```python
from jinja2 import Environment, FileSystemLoader

def create_custom_renderer():
    """Create renderer with custom filters."""
    env = Environment(
        loader=FileSystemLoader("./my-templates"),
        trim_blocks=True,
        lstrip_blocks=True
    )

    # Add custom filter
    def to_memory_mb(memory_str: str) -> int:
        """Convert memory string to MB."""
        units = {'kb': 1/1024, 'mb': 1, 'gb': 1024}
        value = int(''.join(filter(str.isdigit, memory_str)))
        unit = ''.join(filter(str.isalpha, memory_str)).lower()
        return int(value * units.get(unit, 1))

    env.filters['to_mb'] = to_memory_mb

    return env

# Use in template:
# Memory limit: {{ config.services.redis.max_memory|to_mb }} MB
```

## Custom Deployment Methods

Add support for new deployment methods:

### 1. Define New Method

```python
# In your code
class CustomDeploymentMethod(str, Enum):
    DOCKER_SWARM = "docker-swarm"
    NOMAD = "nomad"
    LAMBDA = "lambda"
```

### 2. Extend Generator

```python
from mycelium_onboarding.deployment.generator import DeploymentGenerator

class ExtendedDeploymentGenerator(DeploymentGenerator):
    """Extended generator with custom methods."""

    def generate(self, method: DeploymentMethod) -> GenerationResult:
        """Generate with support for custom methods."""
        if method == "docker-swarm":
            return self._generate_docker_swarm()
        elif method == "nomad":
            return self._generate_nomad()
        else:
            # Fall back to standard methods
            return super().generate(method)

    def _generate_docker_swarm(self) -> GenerationResult:
        """Generate Docker Swarm stack file."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        files_generated = []

        try:
            # Render stack file
            stack_file = self.output_dir / "docker-stack.yml"
            content = self._render_swarm_stack()
            stack_file.write_text(content)
            files_generated.append(stack_file)

            return GenerationResult(
                success=True,
                method="docker-swarm",
                output_dir=self.output_dir,
                files_generated=files_generated
            )
        except Exception as e:
            return GenerationResult(
                success=False,
                method="docker-swarm",
                output_dir=self.output_dir,
                files_generated=files_generated,
                errors=[str(e)]
            )

    def _render_swarm_stack(self) -> str:
        """Render Docker Swarm stack."""
        # Your rendering logic here
        pass
```

### 3. Use Extended Generator

```python
config = MyceliumConfig(project_name="swarm-app")
generator = ExtendedDeploymentGenerator(config)
result = generator.generate("docker-swarm")
```

## CI/CD Integration

### GitHub Actions

Integrate deployment generation in GitHub Actions:

```yaml
# .github/workflows/deploy.yml
name: Generate Deployment

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Mycelium
        run: |
          pip install mycelium-onboarding

      - name: Generate Deployment
        run: |
          # Create config from environment
          cat > config.yaml << EOF
          project_name: ${{ github.event.repository.name }}
          services:
            redis:
              enabled: true
            postgres:
              enabled: true
          deployment:
            method: kubernetes
          EOF

          # Generate deployment
          mycelium deploy generate --output ./deploy

      - name: Upload Artifacts
        uses: actions/upload-artifact@v3
        with:
          name: deployment-manifests
          path: ./deploy/

      - name: Deploy to Kubernetes
        if: github.ref == 'refs/heads/main'
        run: |
          kubectl apply -k ./deploy/kubernetes/
```

### GitLab CI

Integrate with GitLab CI/CD:

```yaml
# .gitlab-ci.yml
stages:
  - generate
  - deploy

variables:
  DEPLOYMENT_METHOD: "kubernetes"

generate_deployment:
  stage: generate
  image: python:3.11
  script:
    - pip install mycelium-onboarding
    - |
      cat > config.yaml << EOF
      project_name: ${CI_PROJECT_NAME}
      services:
        redis:
          enabled: true
        postgres:
          enabled: true
      deployment:
        method: ${DEPLOYMENT_METHOD}
      EOF
    - mycelium deploy generate --output ./deploy
  artifacts:
    paths:
      - deploy/
    expire_in: 1 week

deploy_kubernetes:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl apply -k ./deploy/kubernetes/
  only:
    - main
  dependencies:
    - generate_deployment
```

### Jenkins Pipeline

Integrate with Jenkins:

```groovy
// Jenkinsfile
pipeline {
    agent any

    environment {
        PROJECT_NAME = "${env.JOB_NAME}"
        DEPLOYMENT_METHOD = "kubernetes"
    }

    stages {
        stage('Setup') {
            steps {
                sh 'pip install mycelium-onboarding'
            }
        }

        stage('Generate Deployment') {
            steps {
                script {
                    // Create configuration
                    writeFile file: 'config.yaml', text: """
project_name: ${PROJECT_NAME}
services:
  redis:
    enabled: true
  postgres:
    enabled: true
deployment:
  method: ${DEPLOYMENT_METHOD}
"""

                    // Generate deployment
                    sh 'mycelium deploy generate --output ./deploy'
                }
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh 'kubectl apply -k ./deploy/kubernetes/'
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'deploy/**', fingerprint: true
        }
    }
}
```

## Best Practices

### Production Deployments

#### 1. Separate Secrets from Config

```python
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
```

#### 2. Validate Before Deploying

```python
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
```

#### 3. Version Control Deployments

```python
import git
from datetime import datetime

def version_deployment(config: MyceliumConfig):
    """Version control generated deployments."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    output_dir = Path(f"./deployments/{timestamp}")

    # Generate deployment
    generator = DeploymentGenerator(config, output_dir=output_dir)
    result = generator.generate(
        DeploymentMethod(config.deployment.method)
    )

    if result.success:
        # Commit to git
        repo = git.Repo(".")
        repo.index.add([str(output_dir)])
        repo.index.commit(
            f"Generated deployment for {config.project_name} at {timestamp}"
        )

    return result
```

### Error Handling

Implement robust error handling:

```python
from mycelium_onboarding.deployment.secrets import SecretsError
from mycelium_onboarding.config.manager import (
    ConfigLoadError,
    ConfigValidationError
)

def safe_deployment_generation(project_name: str):
    """Safely generate deployment with error handling."""
    try:
        # Load configuration
        manager = ConfigManager()
        config = manager.load()

    except FileNotFoundError:
        print("Error: Configuration file not found")
        print("Run: mycelium init")
        return None

    except ConfigLoadError as e:
        print(f"Error loading configuration: {e}")
        return None

    except ConfigValidationError as e:
        print(f"Configuration validation failed: {e}")
        return None

    try:
        # Generate deployment
        generator = DeploymentGenerator(config)
        result = generator.generate(
            DeploymentMethod(config.deployment.method)
        )

        if not result.success:
            print("Deployment generation failed:")
            for error in result.errors:
                print(f"  - {error}")
            return None

        # Generate secrets
        secrets_mgr = SecretsManager(project_name)
        secrets = secrets_mgr.generate_secrets(
            postgres=config.services.postgres.enabled,
            redis=config.services.redis.enabled
        )
        secrets_mgr.save_secrets(secrets)

        return result

    except SecretsError as e:
        print(f"Secrets error: {e}")
        return None

    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None
```

### Testing Integrations

Test your deployment integration:

```python
import pytest
from pathlib import Path

def test_deployment_generation(tmp_path):
    """Test deployment generation."""
    config = MyceliumConfig(
        project_name="test-app",
        services={"redis": {"enabled": True}}
    )

    generator = DeploymentGenerator(config, output_dir=tmp_path)
    result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

    assert result.success
    assert (tmp_path / "docker-compose.yml").exists()

def test_secrets_integration(tmp_path):
    """Test secrets generation."""
    manager = SecretsManager("test-app", secrets_dir=tmp_path)
    secrets = manager.generate_secrets(postgres=True)
    manager.save_secrets(secrets)

    # Verify secrets were saved
    assert (tmp_path / "test-app.json").exists()

    # Verify secrets can be loaded
    loaded = manager.load_secrets()
    assert loaded.postgres_password == secrets.postgres_password
```

## Integration Patterns

### Factory Pattern

Create deployments using factory pattern:

```python
class DeploymentFactory:
    """Factory for creating deployments."""

    @staticmethod
    def create_development(project_name: str) -> GenerationResult:
        """Create development deployment."""
        config = MyceliumConfig(
            project_name=project_name,
            services={
                "redis": {"enabled": True, "max_memory": "128mb"},
                "postgres": {"enabled": True, "max_connections": 50}
            },
            deployment={"method": "docker-compose"}
        )

        generator = DeploymentGenerator(config)
        return generator.generate(DeploymentMethod.DOCKER_COMPOSE)

    @staticmethod
    def create_production(project_name: str) -> GenerationResult:
        """Create production deployment."""
        config = MyceliumConfig(
            project_name=project_name,
            services={
                "redis": {"enabled": True, "max_memory": "2gb"},
                "postgres": {"enabled": True, "max_connections": 500}
            },
            deployment={
                "method": "kubernetes",
                "healthcheck_timeout": 120
            }
        )

        generator = DeploymentGenerator(config)
        return generator.generate(DeploymentMethod.KUBERNETES)

# Usage
dev_result = DeploymentFactory.create_development("my-app")
prod_result = DeploymentFactory.create_production("my-app")
```

### Builder Pattern

Build complex configurations:

```python
class DeploymentBuilder:
    """Builder for deployment configurations."""

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.services = {}
        self.deployment_config = {}

    def with_redis(self, port: int = 6379, **kwargs) -> 'DeploymentBuilder':
        """Add Redis service."""
        self.services["redis"] = {"enabled": True, "port": port, **kwargs}
        return self

    def with_postgres(self, database: str = "mydb", **kwargs) -> 'DeploymentBuilder':
        """Add PostgreSQL service."""
        self.services["postgres"] = {
            "enabled": True,
            "database": database,
            **kwargs
        }
        return self

    def with_method(self, method: str) -> 'DeploymentBuilder':
        """Set deployment method."""
        self.deployment_config["method"] = method
        return self

    def build(self) -> MyceliumConfig:
        """Build configuration."""
        return MyceliumConfig(
            project_name=self.project_name,
            services=self.services,
            deployment=self.deployment_config
        )

    def generate(self) -> GenerationResult:
        """Build and generate deployment."""
        config = self.build()
        generator = DeploymentGenerator(config)
        return generator.generate(
            DeploymentMethod(self.deployment_config.get("method", "docker-compose"))
        )

# Usage
result = (DeploymentBuilder("my-app")
    .with_redis(port=6380, max_memory="512mb")
    .with_postgres(database="production")
    .with_method("kubernetes")
    .generate())
```

## Monitoring and Observability

Add monitoring to generated deployments:

```python
def generate_with_monitoring(config: MyceliumConfig):
    """Generate deployment with monitoring stack."""
    # Generate base deployment
    generator = DeploymentGenerator(config)
    result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

    if result.success:
        # Add monitoring services
        compose_file = result.output_dir / "docker-compose.yml"
        compose_config = yaml.safe_load(compose_file.read_text())

        # Add Prometheus
        compose_config["services"]["prometheus"] = {
            "image": "prom/prometheus:latest",
            "ports": ["9090:9090"],
            "volumes": ["./prometheus.yml:/etc/prometheus/prometheus.yml"]
        }

        # Add Grafana
        compose_config["services"]["grafana"] = {
            "image": "grafana/grafana:latest",
            "ports": ["3000:3000"],
            "environment": {
                "GF_SECURITY_ADMIN_PASSWORD": "admin"
            }
        }

        # Write updated config
        compose_file.write_text(yaml.dump(compose_config))

    return result
```

## See Also

- [Deployment Guide](deployment-guide.md) - User guide
- [API Reference](deployment-reference.md) - Complete API documentation
- [Configuration Schema](../mycelium_onboarding/config/schema.py) - Config structure

______________________________________________________________________

*Integration Guide for Mycelium Deployment System*
