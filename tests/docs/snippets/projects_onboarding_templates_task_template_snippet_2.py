# Source: projects/onboarding/templates/task_template.md
# Line: 136
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium/generators/justfile.py
"""Justfile generator for native service deployment."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from mycelium.config import MyceliumConfig


class JustfileGenerator:
    """Generates Justfile configuration from MyceliumConfig."""

    TEMPLATE_NAME = "justfile.j2"

    def __init__(self):
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate(self, config: MyceliumConfig) -> str:
        """Generate Justfile from configuration.

        Args:
            config: Configuration specifying enabled services

        Returns:
            Rendered Justfile content as string

        Raises:
            ValueError: If configuration is invalid for native deployment
        """
        if config.deployment.method != "justfile":
            raise ValueError(
                f"Config deployment method is {config.deployment.method}, "
                "expected 'justfile'"
            )

        template = self.env.get_template(self.TEMPLATE_NAME)

        context = {
            'config': config,
            'services': self._get_enabled_services(config),
        }

        return template.render(**context)

    def _get_enabled_services(self, config: MyceliumConfig) -> list[str]:
        """Extract list of enabled service names."""
        services = []
        if config.services.redis.enabled:
            services.append('redis')
        if config.services.postgres.enabled:
            services.append('postgres')
        return services
