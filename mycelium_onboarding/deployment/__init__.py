"""Deployment configuration generation for Mycelium.

This module provides functionality to generate deployment configurations
for Docker Compose, Kubernetes, and systemd from MyceliumConfig.

Example:
    >>> from mycelium_onboarding.config.schema import MyceliumConfig, DeploymentMethod
    >>> from mycelium_onboarding.deployment import DeploymentGenerator
    >>>
    >>> config = MyceliumConfig(project_name="my-project")
    >>> generator = DeploymentGenerator(config)
    >>> result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)
    >>> print(f"Generated {len(result.files_generated)} files")
"""

from mycelium_onboarding.deployment.generator import (
    DeploymentGenerator,
    GenerationResult,
)
from mycelium_onboarding.deployment.renderer import TemplateRenderer

__all__ = ["DeploymentGenerator", "GenerationResult", "TemplateRenderer"]
