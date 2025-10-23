# Source: projects/onboarding/milestones/M09_TESTING_SUITE.md
# Line: 377
# Valid syntax: True
# Has imports: True
# Has assignments: True

# tests/integration/test_full_flow.py
"""Integration tests for complete onboarding workflow."""

import pytest
from pathlib import Path
from unittest.mock import patch, Mock

from mycelium.detection import InfraDetector
from mycelium.config import ConfigManager, MyceliumConfig
from mycelium.wizard import OnboardingWizard
from mycelium.generators import DockerComposeGenerator, JustfileGenerator


@pytest.mark.integration
class TestFullOnboardingFlow:
    """Tests for complete onboarding workflow: detect → wizard → config → generate."""

    @pytest.mark.asyncio
    async def test_docker_deployment_flow(self, tmp_path, monkeypatch):
        """Test complete flow for Docker deployment method."""
        # Arrange: Mock detection results
        detection_results = Mock(
            redis=Mock(available=True, method="docker"),
            postgres=Mock(available=True, method="docker"),
            docker=Mock(available=True, version="24.0.0"),
        )

        with patch.object(InfraDetector, 'scan_all', return_value=detection_results):
            # Arrange: Mock wizard user selections
            mock_selections = {
                'services': {'redis', 'postgres', 'taskqueue'},
                'deployment_method': 'docker-compose',
                'project_local': True,
            }

            with patch('inquirer.checkbox', side_effect=[
                mock_selections['services'],  # Service selection
            ]):
                with patch('inquirer.select', return_value=mock_selections['deployment_method']):
                    with patch('inquirer.confirm', return_value=mock_selections['project_local']):
                        # Act: Run wizard
                        wizard = OnboardingWizard()
                        config = await wizard.run(config_dir=tmp_path)

        # Assert: Configuration created correctly
        assert isinstance(config, MyceliumConfig)
        assert config.services.redis.enabled
        assert config.services.postgres.enabled
        assert config.services.taskqueue.enabled
        assert config.deployment.method == "docker-compose"

        # Act: Save configuration
        config_path = ConfigManager.save(config, project_local=True, config_dir=tmp_path)

        # Assert: Configuration file exists
        assert config_path.exists()
        assert config_path.name == "config.yaml"

        # Act: Generate deployment files
        docker_gen = DockerComposeGenerator()
        docker_compose = docker_gen.generate(config)

        justfile_gen = JustfileGenerator()
        justfile = justfile_gen.generate(config)

        # Assert: Deployment files generated
        assert "services:" in docker_compose
        assert "redis:" in docker_compose
        assert "postgres:" in docker_compose
        assert "up:" in justfile
        assert "down:" in justfile

    @pytest.mark.asyncio
    async def test_native_deployment_flow(self, tmp_path, monkeypatch):
        """Test complete flow for native (Justfile) deployment method."""
        # Arrange: Mock detection results (native services)
        detection_results = Mock(
            redis=Mock(available=True, method="systemd"),
            postgres=Mock(available=True, method="systemd"),
            docker=Mock(available=False),
        )

        with patch.object(InfraDetector, 'scan_all', return_value=detection_results):
            # Arrange: Mock wizard selections
            mock_selections = {
                'services': {'redis', 'taskqueue'},
                'deployment_method': 'justfile',
                'project_local': False,
            }

            with patch('inquirer.checkbox', return_value=mock_selections['services']):
                with patch('inquirer.select', return_value=mock_selections['deployment_method']):
                    with patch('inquirer.confirm', return_value=mock_selections['project_local']):
                        # Act: Run wizard
                        wizard = OnboardingWizard()
                        config = await wizard.run(config_dir=tmp_path)

        # Assert: Configuration created for native deployment
        assert config.deployment.method == "justfile"
        assert config.services.redis.enabled
        assert config.services.taskqueue.enabled

        # Act: Generate Justfile
        justfile_gen = JustfileGenerator()
        justfile = justfile_gen.generate(config)

        # Assert: Justfile contains native service management
        assert "systemctl" in justfile
        assert "redis-cli" in justfile


@pytest.mark.integration
class TestComponentIntegration:
    """Tests for integration between specific component pairs."""

    def test_detection_to_config_mapping(self):
        """Test that detection results correctly map to configuration."""
        # Arrange
        detection_results = Mock(
            redis=Mock(available=True, method="docker", port=6379),
            postgres=Mock(available=True, method="docker", port=5432),
        )

        # Act
        config = MyceliumConfig.from_detection(detection_results)

        # Assert
        assert config.services.redis.enabled
        assert config.services.redis.port == 6379
        assert config.services.postgres.enabled
        assert config.services.postgres.port == 5432

    def test_config_to_generator_input(self, sample_config):
        """Test that configuration provides valid input for generators."""
        # Act
        docker_gen = DockerComposeGenerator()
        output = docker_gen.generate(sample_config)

        # Assert: Valid YAML structure
        import yaml
        parsed = yaml.safe_load(output)
        assert 'services' in parsed
        assert 'redis' in parsed['services']
        assert parsed['services']['redis']['image'].startswith('redis:')