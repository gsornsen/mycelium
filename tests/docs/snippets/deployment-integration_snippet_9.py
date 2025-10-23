# Source: deployment-integration.md
# Line: 354
# Valid syntax: True
# Has imports: True
# Has assignments: True

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