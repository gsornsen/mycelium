# Source: deployment-integration.md
# Line: 729
# Valid syntax: True
# Has imports: True
# Has assignments: True

import pytest
from pathlib import Path

def test_deployment_generation(tmp_path):
    """Test deployment generation."""
    config = MyceliumConfig(
        project_name="test-app",
        services={"redis": {"enabled": True}}
    )

    generator = DeploymentGenerator(config, output_dir=tmp_path)
    result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

    assert result.success
    assert (tmp_path / "docker-compose.yml").exists()

def test_secrets_integration(tmp_path):
    """Test secrets generation."""
    manager = SecretsManager("test-app", secrets_dir=tmp_path)
    secrets = manager.generate_secrets(postgres=True)
    manager.save_secrets(secrets)

    # Verify secrets were saved
    assert (tmp_path / "test-app.json").exists()

    # Verify secrets can be loaded
    loaded = manager.load_secrets()
    assert loaded.postgres_password == secrets.postgres_password