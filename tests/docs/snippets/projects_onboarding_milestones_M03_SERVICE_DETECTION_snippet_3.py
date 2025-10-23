# Source: projects/onboarding/milestones/M03_SERVICE_DETECTION.md
# Line: 325
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/detection/redis.py
"""Redis detection and health checking."""

import socket
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RedisInfo:
    """Redis detection result."""
    available: bool
    host: str = "localhost"
    port: int = 6379
    version: Optional[str] = None
    reachable: bool = False
    error: Optional[str] = None


def detect_redis(
    host: str = "localhost",
    port: int = 6379,
    timeout: float = 2.0
) -> RedisInfo:
    """Detect Redis server availability.

    Args:
        host: Redis host
        port: Redis port
        timeout: Connection timeout

    Returns:
        RedisInfo with detection results
    """
    info = RedisInfo(available=False, host=host, port=port)

    # Try socket connection first
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            info.available = True
            info.reachable = True

            # Try to get Redis version via INFO command
            sock.sendall(b"INFO server\r\n")
            response = sock.recv(1024).decode("utf-8", errors="ignore")

            # Parse version from "redis_version:7.0.12"
            for line in response.split("\r\n"):
                if line.startswith("redis_version:"):
                    info.version = line.split(":", 1)[1]
                    break

    except socket.timeout:
        info.error = f"Connection timeout to {host}:{port}"
        logger.debug(f"Redis connection timeout: {host}:{port}")

    except (socket.error, OSError) as e:
        info.error = f"Cannot connect to {host}:{port}: {e}"
        logger.debug(f"Redis connection failed: {host}:{port} - {e}")

    return info


def scan_redis_ports(
    host: str = "localhost",
    ports: list[int] = None,
    timeout: float = 1.0
) -> list[RedisInfo]:
    """Scan multiple ports for Redis servers.

    Args:
        host: Redis host to scan
        ports: List of ports to check (default: common Redis ports)
        timeout: Connection timeout per port

    Returns:
        List of RedisInfo for available Redis servers
    """
    if ports is None:
        ports = [6379, 6380, 6381]  # Common Redis ports

    results = []
    for port in ports:
        info = detect_redis(host, port, timeout)
        if info.available:
            results.append(info)

    return results