# Source: detection-reference.md
# Line: 652
# Valid syntax: True
# Has imports: False
# Has assignments: True

@dataclass
class GPUDetectionResult:
    available: bool
    gpus: list[GPU]
    total_memory_mb: int
    error_message: str | None