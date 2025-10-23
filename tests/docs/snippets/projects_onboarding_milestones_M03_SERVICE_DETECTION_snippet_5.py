# Source: projects/onboarding/milestones/M03_SERVICE_DETECTION.md
# Line: 480
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/detection/temporal.py
"""Temporal detection."""

import requests

@dataclass
class TemporalInfo:
    available: bool
    host: str = "localhost"
    frontend_port: int = 7233
    ui_port: int = 8080
    version: Optional[str] = None
    reachable: bool = False
    error: Optional[str] = None


def detect_temporal(
    host: str = "localhost",
    frontend_port: int = 7233,
    ui_port: int = 8080,
    timeout: float = 2.0
) -> TemporalInfo:
    """Detect Temporal server."""
    info = TemporalInfo(
        available=False,
        host=host,
        frontend_port=frontend_port,
        ui_port=ui_port
    )

    # Check frontend port (gRPC)
    try:
        with socket.create_connection((host, frontend_port), timeout=timeout):
            info.available = True

    except (socket.timeout, socket.error, OSError):
        info.error = f"Frontend port {frontend_port} not reachable"
        return info

    # Check UI port (HTTP)
    try:
        response = requests.get(
            f"http://{host}:{ui_port}",
            timeout=timeout,
            allow_redirects=False
        )
        info.reachable = (response.status_code in [200, 302])

    except requests.RequestException as e:
        info.error = f"UI port {ui_port} not reachable: {e}"

    return info