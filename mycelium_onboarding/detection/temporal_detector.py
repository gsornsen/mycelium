"""Temporal server detection module.

This module provides functionality to detect Temporal server availability
and configuration.
"""

from __future__ import annotations

import socket
from dataclasses import dataclass


@dataclass
class TemporalDetectionResult:
    """Result of Temporal detection.

    Attributes:
        available: Whether Temporal server is available and responding
        frontend_port: Frontend gRPC port that was checked
        ui_port: Web UI port that was checked
        version: Temporal version string (if detected)
        namespace: Default namespace
        error_message: Human-readable error message if detection failed
    """

    available: bool
    frontend_port: int = 7233
    ui_port: int = 8080
    version: str | None = None
    namespace: str = "default"
    error_message: str | None = None


def detect_temporal(
    frontend_port: int = 7233, ui_port: int = 8080, timeout: float = 2.0
) -> TemporalDetectionResult:
    """Detect Temporal server availability.

    Args:
        frontend_port: Temporal frontend gRPC port to check
        ui_port: Temporal web UI port to check
        timeout: Connection timeout in seconds

    Returns:
        TemporalDetectionResult with detection status

    Detection strategy:
        1. Check if frontend gRPC port is open (7233)
        2. Check if UI port is responding (8080)
        3. Attempt to detect version from UI
    """
    frontend_available = _check_port_open("localhost", frontend_port, timeout)
    ui_available = _check_port_open("localhost", ui_port, timeout)

    # At minimum, frontend must be available
    if not frontend_available:
        return TemporalDetectionResult(
            available=False,
            frontend_port=frontend_port,
            ui_port=ui_port,
            error_message=f"Temporal frontend not responding on port {frontend_port}. Start Temporal: temporal server start-dev",
        )

    # If frontend is available, consider Temporal as available
    # UI is optional (might be disabled in some deployments)
    version = None
    if ui_available:
        version = _attempt_version_from_ui(ui_port, timeout)

    return TemporalDetectionResult(
        available=True,
        frontend_port=frontend_port,
        ui_port=ui_port,
        version=version,
    )


def _check_port_open(host: str, port: int, timeout: float) -> bool:
    """Check if a port is open and accepting connections.

    Args:
        host: Host to check
        port: Port to check
        timeout: Connection timeout in seconds

    Returns:
        True if port is open, False otherwise
    """
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        return result == 0
    except Exception:
        return False
    finally:
        if sock:
            sock.close()


def _attempt_version_from_ui(ui_port: int, timeout: float) -> str | None:
    """Attempt to detect Temporal version from web UI.

    Args:
        ui_port: Web UI port
        timeout: Connection timeout

    Returns:
        Version string or None if detection failed

    Note:
        This is a best-effort attempt using HTTP request to the UI.
        The UI might return version information in headers or response body.
    """
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(("localhost", ui_port))

        # Send simple HTTP GET request
        request = b"GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n"
        sock.sendall(request)

        # Read response headers
        response = sock.recv(4096).decode("utf-8", errors="ignore")

        # Look for version information in headers or response
        return _parse_temporal_version(response)

    except Exception:
        # Version detection is optional
        return None
    finally:
        if sock:
            sock.close()


def _parse_temporal_version(response: str) -> str | None:
    """Parse Temporal version from HTTP response.

    Args:
        response: Raw HTTP response

    Returns:
        Version string or None if not found
    """
    try:
        # Look for version patterns in headers or HTML
        import re

        # Common patterns in Temporal UI responses
        version_patterns = [
            r"temporal[/-]server[/-]v?(\d+\.\d+\.\d+)",
            r"version[\":\s]+v?(\d+\.\d+\.\d+)",
            r"Temporal\s+v?(\d+\.\d+\.\d+)",
        ]

        for pattern in version_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    except Exception:
        return None
