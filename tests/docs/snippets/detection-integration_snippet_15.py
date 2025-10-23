# Source: detection-integration.md
# Line: 593
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection.docker_detector import detect_docker
from mycelium_onboarding.detection.redis_detector import detect_redis


def quick_check():
    """Quick check of only critical services."""
    docker = detect_docker()
    redis = detect_redis()

    if not docker.available:
        raise RuntimeError("Docker required")

    print(f"Docker: {docker.version}")
    print(f"Redis: {'available' if redis.available else 'unavailable'}")

quick_check()
