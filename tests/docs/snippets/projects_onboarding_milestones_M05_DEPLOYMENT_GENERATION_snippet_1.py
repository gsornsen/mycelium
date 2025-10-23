# Source: projects/onboarding/milestones/M05_DEPLOYMENT_GENERATION.md
# Line: 253
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/generators/docker_compose.py
"""Docker Compose file generator."""

from pathlib import Path

import jinja2
import yaml

from mycelium_onboarding.config.schema import MyceliumConfig


class DockerComposeGenerator:
    """Generates Docker Compose configuration from MyceliumConfig."""

    TEMPLATE_NAME = "docker-compose.yml.j2"

    def __init__(self, template_dir: Path | None = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"

        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            autoescape=False,  # YAML doesn't need escaping
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self, config: MyceliumConfig) -> str:
        """
        Generate Docker Compose YAML from configuration.

        Args:
            config: Mycelium configuration

        Returns:
            Docker Compose YAML content as string
        """
        template = self.env.get_template(self.TEMPLATE_NAME)

        # Prepare context with version information
        context = {
            'config': config,
            'redis_version': '7-alpine',
            'postgres_version': '16-alpine',
            'temporal_version': '1.22.4',
        }

        rendered = template.render(**context)

        # Validate YAML syntax
        try:
            yaml.safe_load(rendered)
        except yaml.YAMLError as e:
            raise ValueError(f"Generated invalid YAML: {e}") from e

        return rendered

    def generate_to_file(
        self,
        config: MyceliumConfig,
        output_path: Path,
        overwrite: bool = False
    ) -> Path:
        """
        Generate Docker Compose file to disk.

        Args:
            config: Mycelium configuration
            output_path: Where to write docker-compose.yml
            overwrite: If True, overwrite existing file

        Returns:
            Path to generated file

        Raises:
            FileExistsError: If file exists and overwrite=False
        """
        if output_path.exists() and not overwrite:
            raise FileExistsError(
                f"{output_path} already exists. Use overwrite=True to replace."
            )

        content = self.generate(config)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)

        return output_path

    def generate_env_example(self, config: MyceliumConfig) -> str:
        """
        Generate .env.example file with documented variables.

        Args:
            config: Mycelium configuration

        Returns:
            .env file content
        """
        lines = [
            "# Mycelium Environment Configuration",
            "# Copy this file to .env and fill in your values",
            "",
        ]

        if config.services.postgres.enabled:
            lines.extend([
                "# PostgreSQL Configuration",
                "POSTGRES_USER=mycelium",
                "POSTGRES_PASSWORD=<generate-secure-password>",
                "POSTGRES_DB=mycelium",
                "",
            ])

        if config.services.temporal.enabled:
            lines.extend([
                "# Temporal Configuration",
                "# (Uses PostgreSQL credentials above)",
                "",
            ])

        lines.extend([
            "# Project Configuration",
            f"PROJECT_NAME={config.project_name}",
            "",
        ])

        return "\n".join(lines)

def validate_docker_compose(compose_file: Path) -> tuple[bool, str | None]:
    """
    Validate Docker Compose file using docker-compose config.

    Args:
        compose_file: Path to docker-compose.yml

    Returns:
        (is_valid, error_message) tuple
    """
    import subprocess

    try:
        result = subprocess.run(
            ['docker-compose', '-f', str(compose_file), 'config'],
            capture_output=True,
            text=True,
            check=True,
        )
        return True, None
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except FileNotFoundError:
        # docker-compose not installed
        return False, "docker-compose command not found"
