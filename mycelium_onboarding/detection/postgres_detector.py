"""PostgreSQL server detection module.

This module provides functionality to detect PostgreSQL server availability,
version, and configuration.
"""

from __future__ import annotations

import socket
import struct
from dataclasses import dataclass


@dataclass
class PostgresDetectionResult:
    """Result of PostgreSQL detection.

    Attributes:
        available: Whether PostgreSQL server is available and responding
        host: PostgreSQL host that was checked
        port: PostgreSQL port that was checked
        version: PostgreSQL version string (e.g., "16.1")
        authentication_method: Authentication method required (if detected)
        error_message: Human-readable error message if detection failed
    """

    available: bool
    host: str = "localhost"
    port: int = 5432
    version: str | None = None
    authentication_method: str | None = None
    error_message: str | None = None


def detect_postgres(
    host: str = "localhost", port: int = 5432, timeout: float = 2.0
) -> PostgresDetectionResult:
    """Detect PostgreSQL server availability.

    Args:
        host: PostgreSQL host to check
        port: PostgreSQL port to check
        timeout: Connection timeout in seconds

    Returns:
        PostgresDetectionResult with detection status

    Detection strategy:
        1. Try TCP socket connection
        2. Send PostgreSQL SSLRequest/StartupMessage
        3. Parse server response for version info
        4. Detect authentication method
    """
    sock = None
    try:
        # Establish TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))

        # Send SSL request (protocol version 1234.5679)
        # This is a standard PostgreSQL handshake to check if server supports SSL
        ssl_request = struct.pack("!II", 8, 80877103)
        sock.sendall(ssl_request)

        # Read single byte response
        # 'S' = SSL supported, 'N' = SSL not supported, 'E' = error
        response = sock.recv(1)

        if not response:
            return PostgresDetectionResult(
                available=False,
                host=host,
                port=port,
                error_message=f"No response from server at {host}:{port}. Service may not be PostgreSQL.",
            )

        # At this point we know something is listening and responding to PostgreSQL protocol
        # For a simple detection, this is sufficient
        # To get version, we would need to complete authentication which requires credentials

        # Try to get more info by sending a startup message
        # This will trigger an authentication request that contains version info
        version = _attempt_version_detection(sock, timeout)

        return PostgresDetectionResult(
            available=True,
            host=host,
            port=port,
            version=version,
            authentication_method="password" if response == b"N" else "ssl",
        )

    except TimeoutError:
        return PostgresDetectionResult(
            available=False,
            host=host,
            port=port,
            error_message=f"Connection to PostgreSQL at {host}:{port} timed out after {timeout}s. Check if PostgreSQL is running and accessible.",
        )
    except ConnectionRefusedError:
        return PostgresDetectionResult(
            available=False,
            host=host,
            port=port,
            error_message=f"Connection refused to PostgreSQL at {host}:{port}. PostgreSQL is not running on this port. Start PostgreSQL: sudo systemctl start postgresql",
        )
    except socket.gaierror:
        return PostgresDetectionResult(
            available=False,
            host=host,
            port=port,
            error_message=f"Cannot resolve hostname '{host}'. Check your network configuration.",
        )
    except OSError as e:
        return PostgresDetectionResult(
            available=False,
            host=host,
            port=port,
            error_message=f"Network error connecting to PostgreSQL at {host}:{port}: {e}",
        )
    except Exception as e:
        return PostgresDetectionResult(
            available=False,
            host=host,
            port=port,
            error_message=f"Error detecting PostgreSQL: {e}",
        )
    finally:
        if sock:
            sock.close()


def scan_common_postgres_ports(
    host: str = "localhost",
) -> list[PostgresDetectionResult]:
    """Scan common PostgreSQL ports (5432, 5433).

    Args:
        host: PostgreSQL host to scan

    Returns:
        List of detection results for each port, only including available instances
    """
    common_ports = [5432, 5433]
    results = []

    for port in common_ports:
        result = detect_postgres(host=host, port=port, timeout=1.0)
        # Only include available PostgreSQL instances
        if result.available:
            results.append(result)

    return results


def _attempt_version_detection(sock: socket.socket, timeout: float) -> str | None:
    """Attempt to detect PostgreSQL version from server response.

    Args:
        sock: Connected socket to PostgreSQL server
        timeout: Timeout for socket operations

    Returns:
        Version string or None if detection failed

    Note:
        This is a best-effort attempt. Getting the actual version
        typically requires authentication.
    """
    try:
        # Send a startup message to trigger an authentication response
        # This may contain server version information
        startup_message = _build_startup_message()
        sock.sendall(startup_message)

        # Try to read response
        sock.settimeout(timeout)
        response = sock.recv(4096)

        if response and response[0:1] == b"E":
            # Parse for error message which might contain version
            # PostgreSQL error messages start with 'E' and contain fields
            version = _parse_error_message_version(response)
            if version:
                return version

        return None

    except Exception:
        # Version detection is optional, don't fail the whole check
        return None


def _build_startup_message() -> bytes:
    """Build a PostgreSQL startup message.

    Returns:
        Startup message bytes
    """
    # Protocol version 3.0
    protocol = struct.pack("!I", 196608)

    # Parameters: user=postgres, database=postgres
    params = b"user\x00postgres\x00database\x00postgres\x00\x00"

    # Length prefix (including itself)
    length = len(protocol) + len(params) + 4
    return struct.pack("!I", length) + protocol + params


def _parse_error_message_version(response: bytes) -> str | None:
    """Parse version information from PostgreSQL error message.

    Args:
        response: Raw error message response

    Returns:
        Version string or None if not found
    """
    try:
        # PostgreSQL error messages have a specific format
        # Look for severity, code, and message fields
        # Version might be in the message text

        text = response.decode("utf-8", errors="ignore")

        # Look for version patterns like "PostgreSQL 16.1" or "server version 16.1"
        import re

        version_patterns = [
            r"PostgreSQL\s+(\d+\.\d+(?:\.\d+)?)",
            r"server\s+version\s+(\d+\.\d+(?:\.\d+)?)",
            r"version\s+(\d+\.\d+(?:\.\d+)?)",
        ]

        for pattern in version_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    except Exception:
        return None
