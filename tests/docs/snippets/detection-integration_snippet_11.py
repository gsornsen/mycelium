# Source: detection-integration.md
# Line: 402
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection import detect_all


def initialize_services_with_fallback():
    """Initialize services with fallback strategies."""
    summary = detect_all()
    services = {}

    # Docker - required
    if not summary.has_docker:
        raise RuntimeError(
            "Docker is required for this application. "
            "Please install Docker and try again."
        )
    services["docker"] = summary.docker

    # Redis - optional with fallback
    if summary.has_redis:
        services["cache"] = "redis"
        print("Using Redis for caching")
    else:
        services["cache"] = "memory"
        print("Warning: Redis not available, using in-memory cache")

    # PostgreSQL - optional with fallback
    if summary.has_postgres:
        services["database"] = "postgresql"
        print("Using PostgreSQL database")
    else:
        services["database"] = "sqlite"
        print("Warning: PostgreSQL not available, using SQLite")

    return services

try:
    services = initialize_services_with_fallback()
except RuntimeError as e:
    print(f"Fatal error: {e}")
    exit(1)
