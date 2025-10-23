# Source: detection-integration.md
# Line: 876
# Valid syntax: True
# Has imports: True
# Has assignments: True

# test_myapp.py
from unittest.mock import patch

import pytest

from mycelium_onboarding.detection.docker_detector import DockerDetectionResult


def test_with_docker_available():
    """Test behavior when Docker is available."""
    with patch("mycelium_onboarding.detection.detect_docker") as mock:
        mock.return_value = DockerDetectionResult(
            available=True,
            version="24.0.5",
            socket_path="/var/run/docker.sock",
            error_message=None
        )

        # Your test code here
        from myapp import check_docker
        assert check_docker() == True

def test_with_docker_unavailable():
    """Test behavior when Docker is unavailable."""
    with patch("mycelium_onboarding.detection.detect_docker") as mock:
        mock.return_value = DockerDetectionResult(
            available=False,
            version=None,
            socket_path=None,
            error_message="Docker not running"
        )

        # Your test code here
        from myapp import check_docker
        with pytest.raises(RuntimeError):
            check_docker()
