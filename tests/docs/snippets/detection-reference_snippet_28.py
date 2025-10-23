# Source: detection-reference.md
# Line: 544
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: expected ':' (<unknown>, line 6)

def detect_temporal(
    host: str = "localhost",
    frontend_port: int = 7233,
    ui_port: int = 8233,
    timeout: float = 2.0
) -> TemporalDetectionResult