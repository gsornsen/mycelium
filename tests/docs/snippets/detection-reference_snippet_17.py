# Source: detection-reference.md
# Line: 329
# Valid syntax: True
# Has imports: False
# Has assignments: True

@dataclass
class DockerDetectionResult:
    available: bool
    version: str | None
    socket_path: str | None
    error_message: str | None
