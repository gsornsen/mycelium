# Source: detection-reference.md
# Line: 207
# Valid syntax: True
# Has imports: False
# Has assignments: True

@dataclass
class DetectionSummary:
    docker: DockerDetectionResult
    redis: list[RedisDetectionResult]
    postgres: list[PostgresDetectionResult]
    temporal: TemporalDetectionResult
    gpu: GPUDetectionResult
    detection_time: float  # Total time in seconds