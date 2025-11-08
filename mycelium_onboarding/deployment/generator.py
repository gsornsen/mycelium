"""Deployment configuration generator framework.

This module provides the DeploymentGenerator class that generates deployment
configurations from MyceliumConfig using Jinja2 templates. It supports Docker
Compose, Kubernetes, and systemd deployment methods with comprehensive validation
and error handling.

Now includes smart service reuse logic through deployment plans.

Example:
    >>> from mycelium_onboarding.config.schema import MyceliumConfig
    >>> from mycelium_onboarding.deployment.generator import (
    ...     DeploymentGenerator,
    ...     DeploymentMethod
    ... )
    >>> config = MyceliumConfig(project_name="my-project")
    >>> generator = DeploymentGenerator(config)
    >>> result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)
    >>> print(f"Generated {len(result.files_generated)} files")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mycelium_onboarding.config.schema import DeploymentMethod, MyceliumConfig
from mycelium_onboarding.xdg_dirs import get_data_dir

from .renderer import TemplateRenderer
from .strategy import DeploymentPlanSummary, ServiceStrategy

# Module exports
__all__ = ["DeploymentGenerator", "DeploymentMethod", "GenerationResult"]


@dataclass
class GenerationResult:
    """Result of deployment generation.

    Attributes:
        success: Whether generation completed successfully
        method: Deployment method used
        output_dir: Directory where files were generated
        files_generated: List of paths to generated files
        errors: List of error messages (empty if successful)
        warnings: List of warning messages
    """

    success: bool
    method: DeploymentMethod
    output_dir: Path
    files_generated: list[Path]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class DeploymentGenerator:
    """Generates deployment configurations from MyceliumConfig.

    This class takes a MyceliumConfig instance and generates deployment
    configurations for the specified deployment method. It validates the
    configuration, renders templates, and creates all necessary files
    including helper scripts and documentation.

    Supports smart service reuse through deployment plans.

    Attributes:
        config: MyceliumConfig instance to generate from
        output_dir: Output directory for generated files
        renderer: TemplateRenderer instance for template rendering
        deployment_plan: Optional deployment plan for smart service reuse

    Example:
        >>> config = MyceliumConfig(project_name="test")
        >>> gen = DeploymentGenerator(config)
        >>> result = gen.generate(DeploymentMethod.DOCKER_COMPOSE)
        >>> assert result.success
        >>> assert len(result.files_generated) > 0
    """

    def __init__(
        self,
        config: MyceliumConfig,
        output_dir: Path | None = None,
        deployment_plan: DeploymentPlanSummary | None = None,
    ) -> None:
        """Initialize deployment generator.

        Args:
            config: MyceliumConfig to generate from
            output_dir: Output directory
                (defaults to XDG_DATA_HOME/deployments/<project>)
            deployment_plan: Optional deployment plan for smart service reuse

        Example:
            >>> config = MyceliumConfig(project_name="my-project")
            >>> gen = DeploymentGenerator(config)
            >>> gen = DeploymentGenerator(config, output_dir=Path("/tmp/deploy"))
        """
        self.config = config
        self.output_dir = output_dir or (get_data_dir() / "deployments" / config.project_name)
        self.renderer = TemplateRenderer()
        self.deployment_plan = deployment_plan

    def generate(self, method: DeploymentMethod) -> GenerationResult:
        """Generate deployment configuration.

        Validates the configuration, generates appropriate files for the
        deployment method, and returns the result with status and file paths.

        Args:
            method: Deployment method to use

        Returns:
            GenerationResult with status and generated files

        Example:
            >>> config = MyceliumConfig(project_name="test")
            >>> gen = DeploymentGenerator(config)
            >>> result = gen.generate(DeploymentMethod.DOCKER_COMPOSE)
            >>> if result.success:
            ...     print(f"Generated: {result.files_generated}")
            ... else:
            ...     print(f"Errors: {result.errors}")
        """
        # Validate config before generating
        errors = self._validate_config(method)
        if errors:
            return GenerationResult(
                success=False,
                method=method,
                output_dir=self.output_dir,
                files_generated=[],
                errors=errors,
            )

        # Generate based on method
        if method == DeploymentMethod.DOCKER_COMPOSE:
            return self._generate_docker_compose()
        if method == DeploymentMethod.KUBERNETES:
            return self._generate_kubernetes()
        if method == DeploymentMethod.SYSTEMD:
            return self._generate_systemd()
        return GenerationResult(
            success=False,
            method=method,
            output_dir=self.output_dir,
            files_generated=[],
            errors=[f"Unsupported deployment method: {method}"],
        )

    def _validate_config(self, method: DeploymentMethod) -> list[str]:
        """Validate config for deployment method.

        Checks that the configuration is appropriate for the specified
        deployment method. Includes general validation and method-specific
        checks.

        Args:
            method: Deployment method to validate for

        Returns:
            List of validation errors (empty if valid)

        Example:
            >>> config = MyceliumConfig(project_name="test")
            >>> gen = DeploymentGenerator(config)
            >>> errors = gen._validate_config(DeploymentMethod.DOCKER_COMPOSE)
            >>> assert len(errors) == 0
        """
        errors: list[str] = []

        # If we have a deployment plan, use it to validate
        if self.deployment_plan:
            if not self.deployment_plan.has_services_to_deploy and not self.deployment_plan.services_to_reuse:
                errors.append("No services to deploy or reuse")
        else:
            # Check at least one service is enabled
            if not any(
                [
                    self.config.services.redis.enabled,
                    self.config.services.postgres.enabled,
                    self.config.services.temporal.enabled,
                ]
            ):
                errors.append("At least one service must be enabled")

        # Method-specific validation
        if method == DeploymentMethod.KUBERNETES:
            # Kubernetes requires specific naming rules
            # (lowercase alphanumeric + hyphens)
            project_name = self.config.project_name.lower()
            if not project_name.replace("-", "").isalnum():
                errors.append(
                    f"Project name for Kubernetes must be alphanumeric with hyphens (got: {self.config.project_name})"
                )

        # systemd validation
        if method == DeploymentMethod.SYSTEMD and len(self.config.project_name) > 50:
            # systemd service names should be relatively short
            errors.append(
                "Project name for systemd should be 50 characters or less "
                f"(got: {len(self.config.project_name)} characters)"
            )

        return errors

    def _generate_docker_compose(self) -> GenerationResult:
        """Generate Docker Compose configuration.

        Creates docker-compose.yml, .env file, and README.md with
        usage instructions. Uses deployment plan to skip reused services.

        Returns:
            GenerationResult with generated files
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        files_generated: list[Path] = []
        warnings: list[str] = []

        try:
            # Render docker-compose.yml with deployment plan context
            compose_file = self.output_dir / "docker-compose.yml"
            content = self.renderer.render_docker_compose(self.config, deployment_plan=self.deployment_plan)
            compose_file.write_text(content)
            files_generated.append(compose_file)

            # Generate .env file
            env_file = self.output_dir / ".env"
            env_content = self._generate_env_file()
            env_file.write_text(env_content)
            files_generated.append(env_file)

            # Add deployment plan warnings
            if self.deployment_plan:
                warnings.extend(self.deployment_plan.warnings)

                # Add service-specific warnings
                if self.deployment_plan.services_to_reuse:
                    warnings.append(
                        f"Reusing existing services: {', '.join(self.deployment_plan.services_to_reuse)}. "
                        "Connection details in .env file."
                    )

            # Add warning about default credentials
            if self.config.services.postgres.enabled:
                warnings.append(
                    "Default PostgreSQL credentials are set in .env - please change them for production use"
                )

            # Generate README
            readme_file = self.output_dir / "README.md"
            readme_content = self._generate_readme("docker-compose")
            readme_file.write_text(readme_content)
            files_generated.append(readme_file)

            # Generate connection info file
            if self.deployment_plan:
                conn_file = self.output_dir / "CONNECTIONS.md"
                conn_content = self._generate_connection_info()
                conn_file.write_text(conn_content)
                files_generated.append(conn_file)

            return GenerationResult(
                success=True,
                method=DeploymentMethod.DOCKER_COMPOSE,
                output_dir=self.output_dir,
                files_generated=files_generated,
                warnings=warnings,
            )
        except Exception as e:
            return GenerationResult(
                success=False,
                method=DeploymentMethod.DOCKER_COMPOSE,
                output_dir=self.output_dir,
                files_generated=files_generated,
                errors=[f"Failed to generate Docker Compose files: {e}"],
            )

    def _generate_kubernetes(self) -> GenerationResult:
        """Generate Kubernetes manifests.

        Creates namespace and service manifests, kustomization.yaml,
        and README.md with usage instructions.

        Returns:
            GenerationResult with generated files
        """
        k8s_dir = self.output_dir / "kubernetes"
        k8s_dir.mkdir(parents=True, exist_ok=True)

        files_generated: list[Path] = []
        warnings: list[str] = []

        try:
            # Render all Kubernetes manifests
            manifests = self.renderer.render_kubernetes(self.config)

            # Create numbered manifest files for proper ordering
            manifest_order: dict[str, str] = {
                "namespace.yaml": "00-namespace.yaml",
                "redis.yaml": "10-redis.yaml",
                "postgres.yaml": "20-postgres.yaml",
                "temporal.yaml": "30-temporal.yaml",
            }

            for manifest_name, content in manifests.items():
                ordered_name = manifest_order.get(manifest_name, manifest_name)
                manifest_file = k8s_dir / ordered_name
                manifest_file.write_text(content)
                files_generated.append(manifest_file)

            # Generate kustomization.yaml
            kustomize_file = k8s_dir / "kustomization.yaml"
            kustomize_content = self._generate_kustomization(files_generated)
            kustomize_file.write_text(kustomize_content)
            files_generated.append(kustomize_file)

            # Add warning about secrets
            if self.config.services.postgres.enabled:
                warnings.append(
                    "PostgreSQL credentials are in ConfigMap - consider using Kubernetes Secrets for production"
                )

            # Generate README
            readme_file = k8s_dir / "README.md"
            readme_content = self._generate_readme("kubernetes")
            readme_file.write_text(readme_content)
            files_generated.append(readme_file)

            return GenerationResult(
                success=True,
                method=DeploymentMethod.KUBERNETES,
                output_dir=k8s_dir,
                files_generated=files_generated,
                warnings=warnings,
            )
        except Exception as e:
            return GenerationResult(
                success=False,
                method=DeploymentMethod.KUBERNETES,
                output_dir=k8s_dir,
                files_generated=files_generated,
                errors=[f"Failed to generate Kubernetes manifests: {e}"],
            )

    def _generate_systemd(self) -> GenerationResult:
        """Generate systemd service files.

        Creates service files for enabled services, installation script,
        and README.md with usage instructions.

        Returns:
            GenerationResult with generated files
        """
        systemd_dir = self.output_dir / "systemd"
        systemd_dir.mkdir(parents=True, exist_ok=True)

        files_generated: list[Path] = []
        warnings: list[str] = []

        try:
            # Render all systemd service files
            services = self.renderer.render_systemd(self.config)

            for service_name, content in services.items():
                service_file = systemd_dir / service_name
                service_file.write_text(content)
                files_generated.append(service_file)

            # Generate installation script
            install_script = systemd_dir / "install.sh"
            install_content = self._generate_systemd_install_script(
                [f.name for f in files_generated if f.suffix == ".service"]
            )
            install_script.write_text(install_content)
            install_script.chmod(0o755)
            files_generated.append(install_script)

            # Add warnings about systemd requirements
            warnings.append("systemd deployment requires root access to install services")
            warnings.append("Ensure service binaries (redis-server, postgres, etc.) are installed")

            # Generate README
            readme_file = systemd_dir / "README.md"
            readme_content = self._generate_readme("systemd")
            readme_file.write_text(readme_content)
            files_generated.append(readme_file)

            return GenerationResult(
                success=True,
                method=DeploymentMethod.SYSTEMD,
                output_dir=systemd_dir,
                files_generated=files_generated,
                warnings=warnings,
            )
        except Exception as e:
            return GenerationResult(
                success=False,
                method=DeploymentMethod.SYSTEMD,
                output_dir=systemd_dir,
                files_generated=files_generated,
                errors=[f"Failed to generate systemd files: {e}"],
            )

    def _generate_env_file(self) -> str:
        """Generate .env file for Docker Compose.

        Creates environment variable definitions for services,
        including database credentials and configuration.
        Uses deployment plan to add connection info for reused services.

        Returns:
            Content for .env file
        """
        lines: list[str] = [
            "# Environment variables for Mycelium deployment",
            f"# Project: {self.config.project_name}",
            "# WARNING: Change default passwords before production use!",
            "",
        ]

        if self.config.services.postgres.enabled:
            lines.extend(
                [
                    "# PostgreSQL credentials",
                    "POSTGRES_USER=postgres",
                    "POSTGRES_PASSWORD=changeme  # CHANGE THIS!",
                    f"POSTGRES_DB={self.config.services.postgres.database}",
                    "",
                ]
            )

        if self.config.services.redis.enabled:
            lines.extend(
                [
                    "# Redis configuration",
                    f"REDIS_MAX_MEMORY={self.config.services.redis.max_memory}",
                    "",
                ]
            )

        if self.config.services.temporal.enabled:
            lines.extend(
                [
                    "# Temporal configuration",
                    f"TEMPORAL_NAMESPACE={self.config.services.temporal.namespace}",
                    "",
                ]
            )

        # Add connection strings from deployment plan
        if self.deployment_plan:
            lines.extend(["# Service connection strings", ""])
            for service_name, plan in self.deployment_plan.service_plans.items():
                if plan.strategy == ServiceStrategy.REUSE:
                    lines.append(f"# {service_name.upper()} (using existing service on {plan.host}:{plan.port})")
                lines.append(f"{service_name.upper()}_URL={plan.connection_string}")
            lines.append("")

        return "\n".join(lines)

    def _generate_connection_info(self) -> str:
        """Generate connection information file.

        Creates a markdown file with detailed connection info for all services.

        Returns:
            CONNECTIONS.md content
        """
        if not self.deployment_plan:
            return ""

        lines = [
            "# Service Connection Information",
            "",
            f"Project: {self.config.project_name}",
            f"Generated: {self.deployment_plan.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Service Status",
            "",
        ]

        for service_name, plan in self.deployment_plan.service_plans.items():
            strategy_emoji = {
                ServiceStrategy.REUSE: "🔄",
                ServiceStrategy.CREATE: "✨",
                ServiceStrategy.ALONGSIDE: "🔀",
                ServiceStrategy.SKIP: "⏭️",
            }
            emoji = strategy_emoji.get(plan.strategy, "❓")

            lines.extend(
                [
                    f"### {emoji} {service_name.title()}",
                    "",
                    f"- **Strategy**: {plan.strategy.value}",
                    f"- **Host**: {plan.host}",
                    f"- **Port**: {plan.port}",
                    f"- **Version**: {plan.version}",
                    f"- **Connection**: `{plan.connection_string}`",
                    f"- **Reason**: {plan.reason}",
                    "",
                ]
            )

        # Add recommendations
        if self.deployment_plan.recommendations:
            lines.extend(["## Recommendations", ""])
            for rec in self.deployment_plan.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        # Add warnings
        if self.deployment_plan.warnings:
            lines.extend(["## Warnings", ""])
            for warn in self.deployment_plan.warnings:
                lines.append(f"- {warn}")
            lines.append("")

        return "\n".join(lines)

    def _generate_readme(self, method: str) -> str:
        """Generate README for deployment.

        Creates method-specific documentation with usage instructions,
        service information, and management commands.

        Args:
            method: Deployment method ("docker-compose", "kubernetes", "systemd")

        Returns:
            README.md content
        """
        # Build enabled services list
        enabled_services: list[str] = []
        if self.config.services.redis.enabled:
            enabled_services.append(f"- Redis (port {self.config.services.redis.port})")
        if self.config.services.postgres.enabled:
            enabled_services.append(f"- PostgreSQL (port {self.config.services.postgres.port})")
        if self.config.services.temporal.enabled:
            enabled_services.append(
                f"- Temporal (UI: {self.config.services.temporal.ui_port}, "
                f"gRPC: {self.config.services.temporal.frontend_port})"
            )

        services_section = "\n".join(enabled_services)

        # Add deployment plan info if available
        plan_section = ""
        if self.deployment_plan:
            reused = ", ".join(self.deployment_plan.services_to_reuse) or "None"
            created = ", ".join(self.deployment_plan.services_to_create) or "None"
            plan_section = f"""
## Deployment Plan

- **Reusing existing services**: {reused}
- **Creating new services**: {created}

See CONNECTIONS.md for detailed connection information.
"""

        if method == "docker-compose":
            return f"""# {self.config.project_name} - Docker Compose Deployment

## Overview

This deployment was generated automatically by Mycelium onboarding.
{plan_section}

## Quick Start

1. **Review and update credentials** in `.env` file
2. **Start services**:
   ```bash
   docker-compose up -d
   ```
3. **Check status**:
   ```bash
   docker-compose ps
   ```

## Services

{services_section}

## Management

### Stop services
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f
```

### Restart a specific service
```bash
docker-compose restart redis
```

### Remove all data (destructive)
```bash
docker-compose down -v
```

## Configuration

- Edit `docker-compose.yml` to modify service configuration
- Edit `.env` to change environment variables
- Run `docker-compose up -d` to apply changes

## Troubleshooting

### Port conflicts
If ports are already in use, edit the port mappings in `docker-compose.yml`

### Permission errors
Ensure Docker daemon is running and you have appropriate permissions

### Data persistence
Volumes are created for data persistence. Use `docker volume ls` to view them.
"""
        if method == "kubernetes":
            return f"""# {self.config.project_name} - Kubernetes Deployment

## Overview

This deployment was generated automatically by Mycelium onboarding.

## Quick Start

1. **Apply manifests**:
   ```bash
   kubectl apply -k .
   ```

2. **Check status**:
   ```bash
   kubectl get all -n {self.config.project_name}
   ```

3. **Wait for pods to be ready**:
   ```bash
   kubectl wait --for=condition=ready pod --all \
       -n {self.config.project_name} --timeout=300s
   ```

## Services

{services_section}

## Management

### View pod status
```bash
kubectl get pods -n {self.config.project_name}
```

### View logs
```bash
kubectl logs -f deployment/redis -n {self.config.project_name}
```

### Delete deployment
```bash
kubectl delete -k .
```

### Port forwarding (for local access)
```bash
kubectl port-forward svc/redis \
    {self.config.services.redis.port}:{self.config.services.redis.port} \
    -n {self.config.project_name}
```

## Configuration

- Edit manifest files to modify configuration
- Apply changes with `kubectl apply -k .`
- Use ConfigMaps and Secrets for sensitive data

## Troubleshooting

### Pods not starting
```bash
kubectl describe pod <pod-name> -n {self.config.project_name}
```

### Resource constraints
Check resource limits in manifest files and adjust based on cluster capacity

### Persistent volumes
Ensure your cluster has a default StorageClass configured
"""
        # systemd
        service_names = [
            f"{self.config.project_name}-{svc}"
            for svc in ["redis", "postgres", "temporal"]
            if getattr(self.config.services, svc.split("-")[-1]).enabled
        ]
        service_list = " ".join(service_names)

        return f"""# {self.config.project_name} - systemd Deployment

## Overview

This deployment was generated automatically by Mycelium onboarding.

## Prerequisites

Ensure the following are installed:
- Redis server (if using Redis)
- PostgreSQL (if using PostgreSQL)
- Temporal server (if using Temporal)

## Installation

Run the installation script with root privileges:
```bash
sudo ./install.sh
```

This will:
1. Copy service files to `/etc/systemd/system/`
2. Reload systemd daemon
3. Enable services to start on boot

## Quick Start

**Start all services**:
```bash
sudo systemctl start {service_list}
```

**Check status**:
```bash
systemctl status {service_list}
```

## Services

{services_section}

## Management

### Enable service on boot
```bash
sudo systemctl enable {self.config.project_name}-redis
```

### Stop a service
```bash
sudo systemctl stop {self.config.project_name}-redis
```

### Restart a service
```bash
sudo systemctl restart {self.config.project_name}-redis
```

### View logs
```bash
journalctl -u {self.config.project_name}-redis -f
```

### Disable service
```bash
sudo systemctl disable {self.config.project_name}-redis
```

## Uninstallation

1. Stop and disable services:
   ```bash
   sudo systemctl stop {service_list}
   sudo systemctl disable {service_list}
   ```

2. Remove service files:
   ```bash
   sudo rm /etc/systemd/system/{self.config.project_name}-*.service
   sudo systemctl daemon-reload
   ```

## Configuration

- Service files are located in `/etc/systemd/system/`
- Edit service files and run `systemctl daemon-reload` to apply changes
- Service-specific configuration is in respective config files
  (e.g., `/etc/redis/redis.conf`)

## Troubleshooting

### Service fails to start
```bash
journalctl -u {self.config.project_name}-redis --no-pager
```

### Permission errors
Check that service user has appropriate permissions for data directories

### Port conflicts
Edit service configuration files to change ports
"""

    def _generate_kustomization(self, manifest_files: list[Path]) -> str:
        """Generate kustomization.yaml for Kubernetes.

        Creates a Kustomize configuration file that references all
        generated manifest files.

        Args:
            manifest_files: List of manifest file paths

        Returns:
            kustomization.yaml content
        """
        resources = [f.name for f in manifest_files if f.suffix == ".yaml" and f.name != "kustomization.yaml"]

        return f"""apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: {self.config.project_name}

resources:
{chr(10).join(f"  - {r}" for r in sorted(resources))}

# commonLabels:
#   app.kubernetes.io/name: {self.config.project_name}
#   app.kubernetes.io/managed-by: mycelium

# Add configMapGenerator or secretGenerator here if needed
"""

    def _generate_systemd_install_script(self, service_files: list[str]) -> str:
        """Generate systemd installation script.

        Creates a bash script that installs systemd service files
        and enables them.

        Args:
            service_files: List of service file names

        Returns:
            install.sh content
        """
        return f"""#!/bin/bash
# systemd service installation script for {self.config.project_name}
# Generated by Mycelium onboarding

set -e

echo "Installing systemd services for {self.config.project_name}..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

# Copy service files
{chr(10).join(f"cp {s} /etc/systemd/system/" for s in service_files)}

# Reload systemd
systemctl daemon-reload

echo "Services installed successfully!"
echo ""
echo "To enable services on boot:"
{chr(10).join(f'echo "  systemctl enable {s}"' for s in service_files)}
echo ""
echo "To start services:"
{chr(10).join(f'echo "  systemctl start {s}"' for s in service_files)}
echo ""
echo "Installation complete!"
"""
