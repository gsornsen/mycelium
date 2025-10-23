# Source: projects/onboarding/milestones/M03_SERVICE_DETECTION.md
# Line: 96
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/detection/docker.py
"""Docker detection and health checking."""

import subprocess
import shutil
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DockerInfo:
    """Docker detection result."""
    available: bool
    version: Optional[str] = None
    running: bool = False
    compose_available: bool = False
    compose_version: Optional[str] = None
    error: Optional[str] = None


def detect_docker(timeout: float = 2.0) -> DockerInfo:
    """Detect Docker Engine availability and status.

    Args:
        timeout: Timeout in seconds for detection commands

    Returns:
        DockerInfo with detection results
    """
    # Check if docker command exists
    if not shutil.which("docker"):
        return DockerInfo(
            available=False,
            error="docker command not found in PATH"
        )

    info = DockerInfo(available=True)

    # Get Docker version
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        if result.returncode == 0:
            # Parse version from "Docker version 24.0.6, build ed223bc"
            version_line = result.stdout.strip()
            if "version" in version_line.lower():
                parts = version_line.split()
                version_idx = parts.index("version") if "version" in parts else -1
                if version_idx >= 0 and version_idx + 1 < len(parts):
                    info.version = parts[version_idx + 1].rstrip(",")

    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        logger.warning(f"Failed to get Docker version: {e}")

    # Check if Docker daemon is running
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        info.running = (result.returncode == 0)
        if not info.running:
            info.error = "Docker daemon not running"

    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        logger.warning(f"Failed to check Docker status: {e}")
        info.running = False
        info.error = str(e)

    # Check Docker Compose
    info.compose_available = _detect_docker_compose(timeout)
    if info.compose_available:
        info.compose_version = _get_compose_version(timeout)

    return info


def _detect_docker_compose(timeout: float) -> bool:
    """Check if Docker Compose is available."""
    # Try docker compose (v2, plugin)
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            timeout=timeout,
            check=False
        )
        if result.returncode == 0:
            return True
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass

    # Try docker-compose (v1, standalone)
    if shutil.which("docker-compose"):
        try:
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                timeout=timeout,
                check=False
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass

    return False


def _get_compose_version(timeout: float) -> Optional[str]:
    """Get Docker Compose version."""
    # Try docker compose (v2)
    try:
        result = subprocess.run(
            ["docker", "compose", "version", "--short"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass

    # Try docker-compose (v1)
    if shutil.which("docker-compose"):
        try:
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            if result.returncode == 0:
                # Parse "docker-compose version 1.29.2, build 5becea4c"
                parts = result.stdout.split()
                if len(parts) >= 3:
                    return parts[2].rstrip(",")
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass

    return None