# Source: detection-reference.md
# Line: 353
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: expected ':' (<unknown>, line 5)

def scan_common_redis_ports(
    host: str = "localhost",
    ports: list[int] | None = None,
    timeout: float = 1.0
) -> list[RedisDetectionResult]