# Source: detection-integration.md
# Line: 37
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection import detect_all


def check_services():
    """Check if required services are available."""
    summary = detect_all()

    if not summary.has_docker:
        raise RuntimeError("Docker is required but not available")

    if not summary.has_redis:
        raise RuntimeError("Redis is required but not available")

    print("All required services available")
    return True

# Run check
check_services()
