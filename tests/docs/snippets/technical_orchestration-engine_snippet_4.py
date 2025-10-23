# Source: technical/orchestration-engine.md
# Line: 127
# Valid syntax: True
# Has imports: False
# Has assignments: True

@dataclass
class RetryPolicy:
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0