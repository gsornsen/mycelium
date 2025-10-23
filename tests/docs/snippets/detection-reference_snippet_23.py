# Source: detection-reference.md
# Line: 454
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: expected ':' (<unknown>, line 5)

def scan_common_postgres_ports(
    host: str = "localhost",
    ports: list[int] | None = None,
    timeout: float = 2.0
) -> list[PostgresDetectionResult]