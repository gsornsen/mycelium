# Source: projects/onboarding/milestones/M03_SERVICE_DETECTION.md
# Line: 444
# Valid syntax: True
# Has imports: False
# Has assignments: True

# mycelium_onboarding/detection/postgres.py
"""PostgreSQL detection."""

@dataclass
class PostgresInfo:
    available: bool
    host: str = "localhost"
    port: int = 5432
    version: Optional[str] = None
    reachable: bool = False
    error: Optional[str] = None


def detect_postgres(
    host: str = "localhost",
    port: int = 5432,
    timeout: float = 2.0
) -> PostgresInfo:
    """Detect PostgreSQL server."""
    info = PostgresInfo(available=False, host=host, port=port)

    try:
        with socket.create_connection((host, port), timeout=timeout):
            info.available = True
            info.reachable = True

            # Could attempt PostgreSQL startup message for version
            # For simplicity, just check socket connection

    except (socket.timeout, socket.error, OSError) as e:
        info.error = str(e)

    return info