# Source: detection-reference.md
# Line: 586
# Valid syntax: True
# Has imports: False
# Has assignments: True

@dataclass
class TemporalDetectionResult:
    available: bool
    frontend_port: int
    ui_port: int
    version: str | None
    error_message: str | None
