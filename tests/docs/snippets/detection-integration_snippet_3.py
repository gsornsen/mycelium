# Source: detection-integration.md
# Line: 92
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection import detect_all
from packaging import version

def check_postgres_version(min_version="15.0"):
    """Ensure PostgreSQL meets minimum version requirement."""
    summary = detect_all()

    if not summary.has_postgres:
        raise RuntimeError("PostgreSQL not available")

    pg_instance = summary.postgres[0]
    if pg_instance.version:
        detected_version = version.parse(pg_instance.version)
        required_version = version.parse(min_version)

        if detected_version < required_version:
            raise RuntimeError(
                f"PostgreSQL {min_version}+ required, found {pg_instance.version}"
            )

    print(f"PostgreSQL {pg_instance.version} meets requirements")
    return True

check_postgres_version()