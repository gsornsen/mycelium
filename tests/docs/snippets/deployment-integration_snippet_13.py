# Source: deployment-integration.md
# Line: 634
# Valid syntax: True
# Has imports: True
# Has assignments: True

from datetime import datetime

import git


def version_deployment(config: MyceliumConfig):
    """Version control generated deployments."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
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
