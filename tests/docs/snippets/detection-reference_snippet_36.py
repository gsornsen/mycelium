# Source: detection-reference.md
# Line: 741
# Valid syntax: True
# Has imports: True
# Has assignments: True

from typing import Protocol


class Detector(Protocol):
    """Protocol for all detector functions."""

    def __call__(self) -> DetectionResult:
        """Run detection and return result."""
        ...

# Type aliases
DetectionResult = Union[
    DockerDetectionResult,
    RedisDetectionResult,
    PostgresDetectionResult,
    TemporalDetectionResult,
    GPUDetectionResult,
]

# Format types
OutputFormat = Literal["text", "json", "yaml"]
