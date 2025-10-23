# Source: deployment-integration.md
# Line: 94
# Valid syntax: True
# Has imports: True
# Has assignments: True

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