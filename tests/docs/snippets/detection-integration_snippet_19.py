# Source: detection-integration.md
# Line: 762
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection import detect_all

def determine_environment():
    """Determine environment type based on detected services."""
    summary = detect_all()

    # Development environment
    if summary.has_docker and summary.has_redis and summary.has_postgres:
        if len(summary.redis) == 1 and len(summary.postgres) == 1:
            return "development"

    # Production environment
    if summary.has_redis and summary.has_postgres and summary.has_temporal:
        if len(summary.redis) > 1 or len(summary.postgres) > 1:
            return "production"

    # CI environment
    if summary.has_docker and not summary.has_gpu:
        return "ci"

    return "unknown"

env = determine_environment()
print(f"Detected environment: {env}")