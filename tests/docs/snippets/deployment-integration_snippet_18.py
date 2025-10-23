# Source: deployment-integration.md
# Line: 868
# Valid syntax: True
# Has imports: False
# Has assignments: True

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