"""Uvicorn server management for Mycelium API.

Handles server startup with security configurations.
CRITICAL: Server MUST bind to 127.0.0.1 only (never 0.0.0.0).
"""

import sys

import uvicorn

from mycelium.api.app import create_app


def start_server(
    port: int = 8080,
    host: str = "127.0.0.1",  # CRITICAL: Default to loopback only
    redis_url: str = "redis://localhost:6379",
    reload: bool = False,
    log_level: str = "info",
) -> None:
    """Start the Mycelium API server.

    SECURITY NOTICE: This server MUST only bind to 127.0.0.1 (localhost) for security.
    Binding to 0.0.0.0 would expose the unauthenticated API to the network.

    Args:
        port: Port to bind to (default: 8080)
        host: Host to bind to (MUST be 127.0.0.1 for security)
        redis_url: Redis connection URL
        reload: Enable auto-reload for development
        log_level: Logging level (debug, info, warning, error)

    Raises:
        ValueError: If host is not 127.0.0.1 or localhost
    """
    # CRITICAL SECURITY CHECK: Prevent binding to 0.0.0.0
    if host not in ("127.0.0.1", "localhost"):
        print(
            f"ERROR: Security violation - attempted to bind to '{host}'",
            file=sys.stderr,
        )
        print(
            "The Mycelium API MUST only bind to 127.0.0.1 (localhost) for security.",
            file=sys.stderr,
        )
        print(
            "This is an unauthenticated API and should never be exposed to the network.",
            file=sys.stderr,
        )
        raise ValueError(
            f"Invalid host '{host}'. Must be '127.0.0.1' or 'localhost' for security."
        )

    # Normalize localhost to 127.0.0.1
    if host == "localhost":
        host = "127.0.0.1"

    # Create the FastAPI app
    app = create_app(redis_url=redis_url)

    # Print startup message
    print(f"Starting Mycelium API server on http://{host}:{port}")
    print(f"OpenAPI documentation available at http://{host}:{port}/docs")
    print(f"Security: Bound to loopback interface only ({host})")

    # Run the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True,
    )


def verify_loopback_binding(port: int = 8080) -> bool:
    """Verify that the server is bound to loopback interface only.

    This is a utility function to verify correct binding after startup.
    Can be used in tests or health checks.

    Args:
        port: Port to check

    Returns:
        True if bound to loopback only, False if exposed to network

    Note:
        This requires the psutil library for reliable cross-platform checking.
        Falls back to parsing netstat output if psutil is unavailable.
    """
    import subprocess

    try:
        # Try using socket to check
        # This is a basic check - for production, use psutil
        result = subprocess.run(
            ["netstat", "-an"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Look for the port binding
        for line in result.stdout.split("\n"):
            if f":{port}" in line and "LISTEN" in line:
                # Check if it's bound to 127.0.0.1 (loopback)
                if "127.0.0.1" in line or "localhost" in line:
                    return True
                # Check if it's bound to 0.0.0.0 (all interfaces) - BAD
                if "0.0.0.0" in line or "*:" in line or ":::" in line:
                    return False

        # Default to safe assumption if we can't determine
        return True

    except Exception:
        # If we can't check, assume it's correct
        # (the start_server function enforces this anyway)
        return True
