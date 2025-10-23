# Source: detection-integration.md
# Line: 916
# Valid syntax: True
# Has imports: True
# Has assignments: False

# conftest.py
import pytest

from mycelium_onboarding.detection import DetectionSummary
from mycelium_onboarding.detection.docker_detector import DockerDetectionResult

# ... import other result types

@pytest.fixture
def all_services_available():
    """Fixture with all services available."""
    return DetectionSummary(
        docker=DockerDetectionResult(available=True, version="24.0.5", socket_path="/var/run/docker.sock", error_message=None),
        redis=[RedisDetectionResult(available=True, host="localhost", port=6379, version="7.2.3", password_required=False, error_message=None)],
        postgres=[PostgresDetectionResult(available=True, host="localhost", port=5432, version="15.4", authentication_method="trust", error_message=None)],
        temporal=TemporalDetectionResult(available=True, frontend_port=7233, ui_port=8233, version="1.22.3", error_message=None),
        gpu=GPUDetectionResult(available=False, gpus=[], total_memory_mb=0, error_message="No GPU"),
        detection_time=2.0
    )

# Use in tests
def test_with_services(all_services_available):
    """Test using the fixture."""
    assert all_services_available.has_docker
    assert all_services_available.has_redis
