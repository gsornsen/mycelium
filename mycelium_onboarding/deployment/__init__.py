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

from typing import Any

# Lazy imports to avoid triggering datetime.now() during Temporal workflow sandbox loading
# Import these explicitly when needed rather than at module load time
__all__ = ["DeploymentGenerator", "GenerationResult", "TemplateRenderer"]


def __getattr__(name: str) -> Any:
    """Lazy load module attributes to avoid importing datetime.now() at load time.

    This is critical for Temporal workflow compatibility - the workflow sandbox
    restricts datetime.now() calls, so we must avoid importing modules that use
    it during the initial package load.

    Args:
        name: Name of the attribute to load

    Returns:
        The requested module attribute

    Raises:
        AttributeError: If the attribute name is not recognized
    """
    if name == "DeploymentGenerator":
        from mycelium_onboarding.deployment.generator import DeploymentGenerator

        return DeploymentGenerator
    if name == "GenerationResult":
        from mycelium_onboarding.deployment.generator import GenerationResult

        return GenerationResult
    if name == "TemplateRenderer":
        from mycelium_onboarding.deployment.renderer import TemplateRenderer

        return TemplateRenderer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
