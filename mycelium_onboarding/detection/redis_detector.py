"""Redis server detection module.

This module provides functionality to detect Redis server availability,
version, and configuration.
"""

from __future__ import annotations

import socket
from dataclasses import dataclass


@dataclass
class RedisDetectionResult:
    """Result of Redis detection.

    Attributes:
        available: Whether Redis server is available and responding
        host: Redis host that was checked
        port: Redis port that was checked
        version: Redis version string (e.g., "7.2.3")
        password_required: Whether Redis requires authentication
        error_message: Human-readable error message if detection failed
    """

    available: bool
    host: str = "localhost"
    port: int = 6379
    version: str | None = None
    password_required: bool = False
    error_message: str | None = None


def detect_redis(
    host: str = "localhost", port: int = 6379, timeout: float = 2.0
) -> RedisDetectionResult:
    """Detect Redis server availability.

    Args:
        host: Redis host to check
        port: Redis port to check
        timeout: Connection timeout in seconds

    Returns:
        RedisDetectionResult with detection status

    Detection strategy:
        1. Try TCP socket connection
        2. Send PING command
        3. Parse INFO response for version
        4. Check if AUTH is required
    """
    sock = None
    try:
        # Establish TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))

        # Send PING command
        sock.sendall(b"PING\r\n")
        response = sock.recv(1024).decode("utf-8", errors="ignore")

        # Check for NOAUTH error (password required)
        if "NOAUTH" in response:
            return RedisDetectionResult(
                available=True,
                host=host,
                port=port,
                password_required=True,
                error_message="Redis requires authentication. Configure password in your Redis client.",
            )

        # Check for successful PONG response
        if "+PONG" not in response:
            return RedisDetectionResult(
                available=False,
                host=host,
                port=port,
                error_message=f"Unexpected response from Redis: {response[:50]}",
            )

        # Get Redis version via INFO command
        sock.sendall(b"INFO SERVER\r\n")
        info_response = sock.recv(4096).decode("utf-8", errors="ignore")

        version = _parse_redis_version(info_response)

        return RedisDetectionResult(
            available=True,
            host=host,
            port=port,
            version=version,
            password_required=False,
        )

    except TimeoutError:
        return RedisDetectionResult(
            available=False,
            host=host,
            port=port,
            error_message=f"Connection to Redis at {host}:{port} timed out after {timeout}s. Check if Redis is running and accessible.",
        )
    except ConnectionRefusedError:
        return RedisDetectionResult(
            available=False,
            host=host,
            port=port,
            error_message=f"Connection refused to Redis at {host}:{port}. Redis is not running on this port. Start Redis: redis-server",
        )
    except socket.gaierror:
        return RedisDetectionResult(
            available=False,
            host=host,
            port=port,
            error_message=f"Cannot resolve hostname '{host}'. Check your network configuration.",
        )
    except OSError as e:
        return RedisDetectionResult(
            available=False,
            host=host,
            port=port,
            error_message=f"Network error connecting to Redis at {host}:{port}: {e}",
        )
    except Exception as e:
        return RedisDetectionResult(
            available=False,
            host=host,
            port=port,
            error_message=f"Error detecting Redis: {e}",
        )
    finally:
        if sock:
            sock.close()


def scan_common_redis_ports(host: str = "localhost") -> list[RedisDetectionResult]:
    """Scan common Redis ports (6379, 6380, 6381).

    Args:
        host: Redis host to scan

    Returns:
        List of detection results for each port, only including available instances
    """
    common_ports = [6379, 6380, 6381]
    results = []

    for port in common_ports:
        result = detect_redis(host=host, port=port, timeout=1.0)
        # Only include available Redis instances
        if result.available:
            results.append(result)

    return results


def _parse_redis_version(info_response: str) -> str | None:
    """Parse Redis version from INFO SERVER response.

    Args:
        info_response: Raw INFO SERVER response from Redis

    Returns:
        Version string or None if not found
    """
    # Look for redis_version line in INFO response
    for line in info_response.split("\n"):
        line = line.strip()
        if line.startswith("redis_version:"):
            version = line.split(":", 1)[1].strip()
            return version

    return None
