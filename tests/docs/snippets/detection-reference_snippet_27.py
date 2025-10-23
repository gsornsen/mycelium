# Source: detection-reference.md
# Line: 518
# Valid syntax: True
# Has imports: False
# Has assignments: True

@dataclass
class PostgresDetectionResult:
    available: bool
    host: str
    port: int
    version: str | None
    authentication_method: str | None
    error_message: str | None
