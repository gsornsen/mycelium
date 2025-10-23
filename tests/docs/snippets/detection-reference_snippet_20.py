# Source: detection-reference.md
# Line: 393
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: expected ':' (<unknown>, line 5)

def detect_redis(
    host: str = "localhost",
    port: int = 6379,
    timeout: float = 1.0
) -> RedisDetectionResult