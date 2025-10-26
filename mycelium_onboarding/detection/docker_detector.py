"""Docker daemon detection module.

This module provides functionality to detect Docker daemon availability,
version, and permissions.
"""

from __future__ import annotations

import os
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DockerDetectionResult:
    """Result of Docker daemon detection.

    Attributes:
        available: Whether Docker daemon is available and running
        version: Docker version string (e.g., "24.0.7")
        socket_path: Path to Docker socket (Unix) or pipe name (Windows)
        error_message: Human-readable error message if detection failed
    """

    available: bool
    version: str | None = None
    socket_path: str | None = None
    error_message: str | None = None


def detect_docker() -> DockerDetectionResult:
    """Detect Docker daemon availability and version.

    Returns:
        DockerDetectionResult with detection status

    Detection strategy:
        1. Check if docker CLI exists
        2. Check if daemon is running (docker info)
        3. Extract version information
        4. Detect socket path (/var/run/docker.sock or Windows named pipe)
    """
    # Check if docker CLI is available
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
        if result.returncode != 0:
            return DockerDetectionResult(
                available=False,
                error_message="Docker CLI not found. Install Docker from https://docs.docker.com/get-docker/",
            )

        # Extract version from output like "Docker version 24.0.7, build afdd53b"
        version_output = result.stdout.strip()
        version = None
        if "version" in version_output:
            parts = version_output.split()
            for i, part in enumerate(parts):
                if part == "version" and i + 1 < len(parts):
                    version = parts[i + 1].rstrip(",")
                    break

    except FileNotFoundError:
        return DockerDetectionResult(
            available=False,
            error_message="Docker CLI not found. Install Docker from https://docs.docker.com/get-docker/",
        )
    except subprocess.TimeoutExpired:
        return DockerDetectionResult(
            available=False,
            error_message="Docker CLI command timed out. Check your Docker installation.",
        )
    except Exception as e:
        return DockerDetectionResult(
            available=False,
            error_message=f"Error checking Docker CLI: {e}",
        )

    # Check if daemon is running
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            if "permission denied" in error_msg.lower():
                return DockerDetectionResult(
                    available=False,
                    version=version,
                    error_message=(
                    "Docker daemon is running but you don't have permissions. "
                    "Add your user to the 'docker' group: sudo usermod -aG docker $USER"
                ),
                )
            if (
                "cannot connect" in error_msg.lower()
                or "connection refused" in error_msg.lower()
            ):
                return DockerDetectionResult(
                    available=False,
                    version=version,
                    error_message=(
                        "Docker daemon is not running. "
                        "Start Docker daemon: sudo systemctl start docker"
                    ),
                )
            return DockerDetectionResult(
                available=False,
                version=version,
                error_message=f"Docker daemon check failed: {error_msg}",
            )
    except subprocess.TimeoutExpired:
        return DockerDetectionResult(
            available=False,
            version=version,
            error_message="Docker daemon check timed out. The daemon may be unresponsive.",
        )
    except Exception as e:
        return DockerDetectionResult(
            available=False,
            version=version,
            error_message=f"Error checking Docker daemon: {e}",
        )

    # Detect socket path
    socket_path = _detect_docker_socket()

    return DockerDetectionResult(
        available=True,
        version=version,
        socket_path=socket_path,
    )


def verify_docker_permissions() -> tuple[bool, str | None]:
    """Verify current user has Docker permissions.

    Returns:
        (has_permission, error_message)

    This function attempts to run a simple docker command to verify
    that the current user has the necessary permissions to interact
    with the Docker daemon.
    """
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
        if result.returncode == 0:
            return (True, None)

        error_msg = result.stderr.strip()
        if "permission denied" in error_msg.lower():
            return (
                False,
                "Permission denied. Add your user to the 'docker' group: sudo usermod -aG docker $USER\n"
                "Then log out and back in, or run: newgrp docker",
            )
        if (
            "cannot connect" in error_msg.lower()
            or "connection refused" in error_msg.lower()
        ):
            return (
                False,
                "Cannot connect to Docker daemon. Ensure Docker is running: sudo systemctl start docker",
            )
        return (False, f"Docker permission check failed: {error_msg}")

    except FileNotFoundError:
        return (
            False,
            "Docker CLI not found. Install Docker from https://docs.docker.com/get-docker/",
        )
    except subprocess.TimeoutExpired:
        return (False, "Docker command timed out. The daemon may be unresponsive.")
    except Exception as e:
        return (False, f"Error verifying Docker permissions: {e}")


def _detect_docker_socket() -> str | None:
    """Detect Docker socket path based on platform.

    Returns:
        Socket path string or None if not found
    """
    system = platform.system()

    if system == "Windows":
        # Windows uses named pipe
        return "npipe:////./pipe/docker_engine"

    # Unix-like systems (Linux, macOS, WSL)
    common_paths: list[str | Path] = [
        "/var/run/docker.sock",
        Path.home() / ".docker" / "run" / "docker.sock",  # Docker Desktop on macOS
        "/run/docker.sock",
    ]

    for path in common_paths:
        path_obj = Path(path) if isinstance(path, str) else path
        if path_obj.exists():
            return str(path_obj)

    # Check environment variable
    docker_host = os.environ.get("DOCKER_HOST")
    if docker_host:
        return docker_host

    return None
