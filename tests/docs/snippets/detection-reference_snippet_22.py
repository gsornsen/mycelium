# Source: detection-reference.md
# Line: 426
# Valid syntax: True
# Has imports: False
# Has assignments: True

@dataclass
class RedisDetectionResult:
    available: bool
    host: str
    port: int
    version: str | None
    password_required: bool
    error_message: str | None