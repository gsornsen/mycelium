"""Sample rendered deployment configurations.

This script demonstrates the template rendering by creating sample
outputs for all deployment methods.
"""

from pathlib import Path

from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.deployment import TemplateRenderer


def create_sample_config() -> MyceliumConfig:
    """Create a sample configuration for demonstration."""
    return MyceliumConfig(
        project_name="mycelium-demo",
        services={
            "redis": {
                "enabled": True,
                "version": "7.0",
                "port": 6379,
                "persistence": True,
                "max_memory": "512mb",
            },
            "postgres": {
                "enabled": True,
                "version": "15",
                "port": 5432,
                "database": "mycelium",
                "max_connections": 100,
            },
            "temporal": {
                "enabled": True,
                "version": "1.22.0",
                "ui_port": 8080,
                "frontend_port": 7233,
                "namespace": "default",
            },
        },
        deployment={
            "method": "docker-compose",
            "auto_start": True,
            "healthcheck_timeout": 60,
        },
    )


def main():
    """Generate sample deployment configurations."""
    # Create output directory
    output_dir = Path(__file__).parent / "rendered_configs"
    output_dir.mkdir(exist_ok=True)

    # Create sample config
    config = create_sample_config()

    # Initialize renderer
    renderer = TemplateRenderer()

    # Render Docker Compose
    print("Rendering Docker Compose configuration...")
    docker_compose = renderer.render_docker_compose(config)
    (output_dir / "docker-compose.yml").write_text(docker_compose)
    print(f"  Saved to: {output_dir / 'docker-compose.yml'}")

    # Render Kubernetes manifests
    print("\nRendering Kubernetes manifests...")
    k8s_dir = output_dir / "kubernetes"
    k8s_dir.mkdir(exist_ok=True)

    k8s_manifests = renderer.render_kubernetes(config)
    for filename, content in k8s_manifests.items():
        filepath = k8s_dir / filename
        filepath.write_text(content)
        print(f"  Saved to: {filepath}")

    # Render systemd service files
    print("\nRendering systemd service files...")
    systemd_dir = output_dir / "systemd"
    systemd_dir.mkdir(exist_ok=True)

    systemd_services = renderer.render_systemd(config)
    for filename, content in systemd_services.items():
        filepath = systemd_dir / filename
        filepath.write_text(content)
        print(f"  Saved to: {filepath}")

    print(f"\nAll sample configurations rendered to: {output_dir}")


if __name__ == "__main__":
    main()
