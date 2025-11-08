"""Template rendering engine for deployment configurations.

This module provides the TemplateRenderer class that generates deployment
configurations from MyceliumConfig using Jinja2 templates.

Now supports smart service reuse through deployment plans.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from mycelium_onboarding.config.schema import DeploymentMethod, MyceliumConfig

from .strategy import DeploymentPlanSummary, ServiceStrategy

# Module exports
__all__ = ["TemplateRenderer"]


class TemplateRenderer:
    """Renders deployment configuration templates.

    This class provides methods to render Docker Compose, Kubernetes,
    and systemd configurations from a MyceliumConfig instance.

    Supports smart service reuse through deployment plans.

    Attributes:
        template_dir: Directory containing Jinja2 templates
        env: Jinja2 environment for template rendering

    Example:
        >>> config = MyceliumConfig(project_name="my-project")
        >>> renderer = TemplateRenderer()
        >>> docker_compose = renderer.render_docker_compose(config)
        >>> k8s_manifests = renderer.render_kubernetes(config)
    """

    def __init__(self, template_dir: Path | None = None):
        """Initialize the template renderer.

        Args:
            template_dir: Optional custom template directory.
                         Defaults to package's templates directory.
        """
        if template_dir is None:
            # Default to package's templates directory
            self.template_dir = Path(__file__).parent / "templates"
        else:
            self.template_dir = Path(template_dir)

        if not self.template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {self.template_dir}")

        # Create Jinja2 environment with autoescape for security
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(enabled_extensions=("j2",)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Add custom filters
        self.env.filters["kebab_case"] = self._kebab_case_filter

    @staticmethod
    def _kebab_case_filter(value: str) -> str:
        """Convert string to kebab-case.

        Args:
            value: String to convert

        Returns:
            Kebab-cased string
        """
        return value.replace("_", "-").lower()

    def render_docker_compose(
        self, config: MyceliumConfig, deployment_plan: DeploymentPlanSummary | None = None
    ) -> str:
        """Render Docker Compose configuration.

        Args:
            config: MyceliumConfig instance to render
            deployment_plan: Optional deployment plan for smart service reuse

        Returns:
            Rendered docker-compose.yml content

        Example:
            >>> config = MyceliumConfig(project_name="test")
            >>> renderer = TemplateRenderer()
            >>> yaml_content = renderer.render_docker_compose(config)
        """
        template = self.env.get_template("docker-compose.yml.j2")

        # Build context with deployment plan information
        context = {"config": config}

        if deployment_plan:
            # Determine which services should be included in docker-compose
            context["deploy_redis"] = self._should_deploy_service(deployment_plan, "redis")
            context["deploy_postgres"] = self._should_deploy_service(deployment_plan, "postgres")
            context["deploy_temporal"] = self._should_deploy_service(deployment_plan, "temporal")

            # Pass service plans for custom port handling
            context["deployment_plan"] = deployment_plan
        else:
            # No plan, use config enabled flags
            context["deploy_redis"] = config.services.redis.enabled
            context["deploy_postgres"] = config.services.postgres.enabled
            context["deploy_temporal"] = config.services.temporal.enabled
            context["deployment_plan"] = None

        return template.render(**context)

    def _should_deploy_service(self, deployment_plan: DeploymentPlanSummary, service_name: str) -> bool:
        """Determine if a service should be deployed in docker-compose.

        Args:
            deployment_plan: Deployment plan
            service_name: Name of the service

        Returns:
            True if service should be deployed, False if reusing existing
        """
        service_plan = deployment_plan.get_service_plan(service_name)
        if not service_plan:
            return False

        # Only deploy if strategy is CREATE or ALONGSIDE
        return service_plan.strategy in [ServiceStrategy.CREATE, ServiceStrategy.ALONGSIDE]

    def render_kubernetes(self, config: MyceliumConfig) -> dict[str, str]:
        """Render Kubernetes manifests.

        Args:
            config: MyceliumConfig instance to render

        Returns:
            Dictionary mapping manifest names to rendered content

        Example:
            >>> config = MyceliumConfig(project_name="test")
            >>> renderer = TemplateRenderer()
            >>> manifests = renderer.render_kubernetes(config)
            >>> print(manifests['namespace.yaml'])
        """
        manifests = {}

        # Always render namespace
        template = self.env.get_template("kubernetes/namespace.yaml.j2")
        manifests["namespace.yaml"] = template.render(config=config)

        # Render service-specific manifests
        if config.services.redis.enabled:
            template = self.env.get_template("kubernetes/redis.yaml.j2")
            manifests["redis.yaml"] = template.render(config=config)

        if config.services.postgres.enabled:
            template = self.env.get_template("kubernetes/postgres.yaml.j2")
            manifests["postgres.yaml"] = template.render(config=config)

        if config.services.temporal.enabled:
            template = self.env.get_template("kubernetes/temporal.yaml.j2")
            manifests["temporal.yaml"] = template.render(config=config)

        return manifests

    def render_systemd(self, config: MyceliumConfig) -> dict[str, str]:
        """Render systemd service files.

        Args:
            config: MyceliumConfig instance to render

        Returns:
            Dictionary mapping service names to rendered content

        Example:
            >>> config = MyceliumConfig(project_name="test")
            >>> renderer = TemplateRenderer()
            >>> services = renderer.render_systemd(config)
            >>> print(services['redis.service'])
        """
        services = {}

        # Render service-specific systemd units
        if config.services.redis.enabled:
            template = self.env.get_template("systemd/redis.service.j2")
            services[f"{config.project_name}-redis.service"] = template.render(config=config)

        if config.services.postgres.enabled:
            template = self.env.get_template("systemd/postgres.service.j2")
            services[f"{config.project_name}-postgres.service"] = template.render(config=config)

        if config.services.temporal.enabled:
            template = self.env.get_template("systemd/temporal.service.j2")
            services[f"{config.project_name}-temporal.service"] = template.render(config=config)

        return services

    def render_all(self, config: MyceliumConfig) -> dict[str, Any]:
        """Render all deployment configurations.

        Args:
            config: MyceliumConfig instance to render

        Returns:
            Dictionary with all rendered configurations:
            - docker_compose: Docker Compose YAML content
            - kubernetes: Dict of K8s manifests
            - systemd: Dict of systemd service files

        Example:
            >>> config = MyceliumConfig(project_name="test")
            >>> renderer = TemplateRenderer()
            >>> all_configs = renderer.render_all(config)
        """
        return {
            "docker_compose": self.render_docker_compose(config),
            "kubernetes": self.render_kubernetes(config),
            "systemd": self.render_systemd(config),
        }

    def render_for_method(self, config: MyceliumConfig, method: DeploymentMethod | None = None) -> str | dict[str, str]:
        """Render configuration for specified deployment method.

        Args:
            config: MyceliumConfig instance to render
            method: Deployment method to use. If None, uses config.deployment.method

        Returns:
            Rendered configuration (string for docker-compose, dict for others)

        Raises:
            ValueError: If deployment method is invalid

        Example:
            >>> config = MyceliumConfig(project_name="test")
            >>> renderer = TemplateRenderer()
            >>> output = renderer.render_for_method(config, DeploymentMethod.DOCKER_COMPOSE)
        """
        if method is None:
            method = config.deployment.method

        if method == DeploymentMethod.DOCKER_COMPOSE:
            return self.render_docker_compose(config)
        if method == DeploymentMethod.KUBERNETES:
            return self.render_kubernetes(config)
        if method == DeploymentMethod.SYSTEMD:
            return self.render_systemd(config)
        if method == DeploymentMethod.MANUAL:
            # For manual deployment, return empty dict
            return {}
        raise ValueError(f"Invalid deployment method: {method}")
