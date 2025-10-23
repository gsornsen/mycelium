# Source: detection-reference.md
# Line: 487
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: expected ':' (<unknown>, line 5)

def detect_postgres(
    host: str = "localhost",
    port: int = 5432,
    timeout: float = 2.0
) -> PostgresDetectionResult