# M03: Service Detection

## Overview

**Duration**: 3 days
**Dependencies**: M01 (Environment Isolation)
**Blocks**: M04 (Interactive Onboarding), M05 (Deployment Generation)
**Lead Agent**: devops-engineer
**Support Agents**: platform-engineer, python-pro

## Why This Milestone

Service detection enables intelligent onboarding by automatically discovering what infrastructure is already available:
- Avoids deploying duplicate services (e.g., user already has Redis running)
- Detects Docker availability for containerized deployment
- Identifies GPU presence for potential acceleration
- Provides health status for existing services
- Enables graceful fallback when services unavailable

This milestone transforms onboarding from "configure everything" to "configure what's missing", dramatically improving user experience.

## Requirements

### Functional Requirements (FR)

**FR-1**: Auto-detect service availability
- Docker Engine (version, running status)
- Redis (host, port, reachable)
- PostgreSQL (host, port, reachable, version)
- Temporal (host, port, reachable)
- GPU (NVIDIA CUDA, AMD ROCm)

**FR-2**: Non-interactive detection mode
- Run completely without user input
- Output structured data (JSON)
- Exit codes indicate detection success/failure
- Timeout protection (don't hang indefinitely)

**FR-3**: Health check utilities
- Verify service is not just running, but responding
- Check service version compatibility
- Report degraded states (running but unreachable)

### Technical Requirements (TR)

**TR-1**: Platform-agnostic detection
- Work on Linux, macOS, Windows (WSL2)
- Use cross-platform libraries where possible
- Fallback to shell commands when necessary

**TR-2**: Caching for performance
- Cache detection results (configurable TTL)
- Use XDG cache directory
- Invalidate cache on explicit re-detection

**TR-3**: Graceful failure handling
- Service not found: return "not available" (not error)
- Timeout: return "timeout" status
- Permission denied: return "permission denied" with fix instructions

### Integration Requirements (IR)

**IR-1**: Integration with M01 environment isolation
- Use XDG cache directory for caching results
- Respect environment validation

**IR-2**: Integration with M04 interactive onboarding
- Provide detected services as wizard defaults
- Allow user to override detection results
- Show detection status in wizard

### Constraints (CR)

**CR-1**: No service installation or configuration
- Detection only, no modifications
- Read-only operations
- No admin/sudo required

**CR-2**: Fast detection (<5 seconds total)
- Parallel detection where possible
- Aggressive timeouts (1-2s per service)
- Early exit on definitive results

## Tasks

### Task 3.1: Docker Detection

**Agent**: devops-engineer
**Effort**: 6 hours
**Dependencies**: M01 complete

**Description**: Implement Docker Engine detection with version and status check.

**Implementation**:

```python
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
```

**Test Plan**:

```python
# tests/test_docker_detection.py
import pytest
from mycelium_onboarding.detection.docker import detect_docker, DockerInfo


def test_detect_docker_available(monkeypatch):
    """Test detection when Docker is available."""
    # Mock docker command
    def mock_run(*args, **kwargs):
        command = args[0]
        if "--version" in command:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="Docker version 24.0.6, build ed223bc\n"
            )
        elif "ps" in command:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=""
            )
        return subprocess.CompletedProcess(args=command, returncode=1)

    monkeypatch.setattr("subprocess.run", mock_run)
    monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/docker" if x == "docker" else None)

    info = detect_docker()

    assert info.available
    assert info.version == "24.0.6"
    assert info.running


def test_detect_docker_not_installed(monkeypatch):
    """Test detection when Docker is not installed."""
    monkeypatch.setattr("shutil.which", lambda x: None)

    info = detect_docker()

    assert not info.available
    assert "not found" in info.error.lower()
```

**Acceptance Criteria**:
- [ ] Detects Docker CLI presence
- [ ] Gets Docker version correctly
- [ ] Checks if Docker daemon is running
- [ ] Detects Docker Compose (v1 and v2)
- [ ] Handles timeouts gracefully
- [ ] Returns clear error messages
- [ ] Works on Linux, macOS, Windows (WSL2)

**Deliverables**:
- `mycelium_onboarding/detection/docker.py`
- `tests/test_docker_detection.py`

---

### Task 3.2: Redis Detection

**Agent**: devops-engineer
**Effort**: 4 hours
**Dependencies**: Task 3.1 (pattern established)

**Description**: Detect Redis server availability and health.

**Implementation**:

```python
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
```

**Acceptance Criteria**:
- [ ] Detects Redis on standard port (6379)
- [ ] Supports custom host and port
- [ ] Gets Redis version via INFO command
- [ ] Handles connection timeouts
- [ ] Handles connection refused
- [ ] Can scan multiple ports
- [ ] No dependency on redis-py library

**Deliverables**:
- `mycelium_onboarding/detection/redis.py`
- `tests/test_redis_detection.py`

---

### Task 3.3: PostgreSQL & Temporal Detection

**Agent**: devops-engineer
**Effort**: 6 hours
**Dependencies**: Task 3.2 (pattern established)

**Description**: Detect PostgreSQL and Temporal servers.

**Implementation** (abbreviated for brevity):

```python
# mycelium_onboarding/detection/postgres.py
"""PostgreSQL detection."""

@dataclass
class PostgresInfo:
    available: bool
    host: str = "localhost"
    port: int = 5432
    version: Optional[str] = None
    reachable: bool = False
    error: Optional[str] = None


def detect_postgres(
    host: str = "localhost",
    port: int = 5432,
    timeout: float = 2.0
) -> PostgresInfo:
    """Detect PostgreSQL server."""
    info = PostgresInfo(available=False, host=host, port=port)

    try:
        with socket.create_connection((host, port), timeout=timeout):
            info.available = True
            info.reachable = True

            # Could attempt PostgreSQL startup message for version
            # For simplicity, just check socket connection

    except (socket.timeout, socket.error, OSError) as e:
        info.error = str(e)

    return info
```

```python
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
```

**Acceptance Criteria**:
- [ ] PostgreSQL detection via socket connection
- [ ] Temporal frontend (gRPC) and UI (HTTP) detection
- [ ] Version detection where possible
- [ ] Timeout handling
- [ ] Clear error messages

**Deliverables**:
- `mycelium_onboarding/detection/postgres.py`
- `mycelium_onboarding/detection/temporal.py`
- Tests for both

---

### Task 3.4: GPU Detection

**Agent**: platform-engineer
**Effort**: 6 hours
**Dependencies**: None (parallel with Tasks 3.1-3.3)

**Description**: Detect GPU presence and type (NVIDIA CUDA, AMD ROCm).

**Implementation**:

```python
# mycelium_onboarding/detection/gpu.py
"""GPU detection."""

import subprocess
import shutil
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class GPUType(str, Enum):
    """GPU types."""
    NVIDIA = "nvidia"
    AMD = "amd"
    UNKNOWN = "unknown"


@dataclass
class GPUInfo:
    """GPU detection result."""
    available: bool
    gpu_type: Optional[GPUType] = None
    count: int = 0
    driver_version: Optional[str] = None
    cuda_version: Optional[str] = None
    devices: list[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.devices is None:
            self.devices = []


def detect_gpu(timeout: float = 2.0) -> GPUInfo:
    """Detect GPU availability.

    Args:
        timeout: Timeout for detection commands

    Returns:
        GPUInfo with detection results
    """
    # Try NVIDIA first
    nvidia_info = _detect_nvidia_gpu(timeout)
    if nvidia_info.available:
        return nvidia_info

    # Try AMD
    amd_info = _detect_amd_gpu(timeout)
    if amd_info.available:
        return amd_info

    # No GPU found
    return GPUInfo(available=False, error="No GPU detected")


def _detect_nvidia_gpu(timeout: float) -> GPUInfo:
    """Detect NVIDIA GPU via nvidia-smi."""
    if not shutil.which("nvidia-smi"):
        return GPUInfo(available=False, error="nvidia-smi not found")

    info = GPUInfo(available=False, gpu_type=GPUType.NVIDIA)

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version",
                "--format=csv,noheader"
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            info.count = len(lines)
            info.available = info.count > 0

            for line in lines:
                parts = line.split(",")
                if len(parts) >= 1:
                    info.devices.append(parts[0].strip())
                if len(parts) >= 2 and not info.driver_version:
                    info.driver_version = parts[1].strip()

            # Get CUDA version
            info.cuda_version = _get_cuda_version(timeout)

        else:
            info.error = result.stderr.strip()

    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        info.error = str(e)

    return info


def _get_cuda_version(timeout: float) -> Optional[str]:
    """Get CUDA version from nvidia-smi."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        if result.returncode == 0:
            # Parse CUDA version from output
            # This is simplified; actual parsing may be more complex
            return result.stdout.strip().split("\n")[0]

    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass

    return None


def _detect_amd_gpu(timeout: float) -> GPUInfo:
    """Detect AMD GPU via rocm-smi."""
    if not shutil.which("rocm-smi"):
        return GPUInfo(available=False, error="rocm-smi not found")

    info = GPUInfo(available=False, gpu_type=GPUType.AMD)

    try:
        result = subprocess.run(
            ["rocm-smi", "--showproductname"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )

        if result.returncode == 0:
            # Parse AMD GPU info from output
            lines = result.stdout.strip().split("\n")
            # Simplified parsing
            info.count = len([l for l in lines if "GPU" in l])
            info.available = info.count > 0

        else:
            info.error = result.stderr.strip()

    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        info.error = str(e)

    return info
```

**Acceptance Criteria**:
- [ ] Detects NVIDIA GPUs via nvidia-smi
- [ ] Detects AMD GPUs via rocm-smi
- [ ] Counts multiple GPUs
- [ ] Gets driver and CUDA/ROCm versions
- [ ] Handles missing drivers gracefully
- [ ] Fast detection (< 2s)

**Deliverables**:
- `mycelium_onboarding/detection/gpu.py`
- `tests/test_gpu_detection.py`

---

### Task 3.5: Detection Orchestrator & Caching

**Agent**: python-pro
**Effort**: 6 hours
**Dependencies**: Tasks 3.1-3.4

**Description**: Create orchestrator that runs all detectors in parallel and caches results.

**Implementation**:

```python
# mycelium_onboarding/detection/orchestrator.py
"""Service detection orchestrator."""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import asdict
import logging

from mycelium_onboarding.xdg_dirs import get_cache_dir
from mycelium_onboarding.detection.docker import detect_docker, DockerInfo
from mycelium_onboarding.detection.redis import detect_redis, RedisInfo
from mycelium_onboarding.detection.postgres import detect_postgres, PostgresInfo
from mycelium_onboarding.detection.temporal import detect_temporal, TemporalInfo
from mycelium_onboarding.detection.gpu import detect_gpu, GPUInfo

logger = logging.getLogger(__name__)


class DetectionResults:
    """All service detection results."""

    def __init__(
        self,
        docker: DockerInfo,
        redis: RedisInfo,
        postgres: PostgresInfo,
        temporal: TemporalInfo,
        gpu: GPUInfo,
        timestamp: datetime = None
    ):
        self.docker = docker
        self.redis = redis
        self.postgres = postgres
        self.temporal = temporal
        self.gpu = gpu
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "docker": asdict(self.docker),
            "redis": asdict(self.redis),
            "postgres": asdict(self.postgres),
            "temporal": asdict(self.temporal),
            "gpu": asdict(self.gpu),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DetectionResults":
        """Load from dictionary."""
        return cls(
            docker=DockerInfo(**data["docker"]),
            redis=RedisInfo(**data["redis"]),
            postgres=PostgresInfo(**data["postgres"]),
            temporal=TemporalInfo(**data["temporal"]),
            gpu=GPUInfo(**data["gpu"]),
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


async def detect_all_services(
    use_cache: bool = True,
    cache_ttl: int = 300  # 5 minutes
) -> DetectionResults:
    """Detect all services in parallel.

    Args:
        use_cache: Use cached results if available and fresh
        cache_ttl: Cache TTL in seconds

    Returns:
        DetectionResults with all detection results
    """
    # Try to load from cache
    if use_cache:
        cached = _load_from_cache(cache_ttl)
        if cached:
            logger.info("Using cached detection results")
            return cached

    # Run all detections in parallel
    logger.info("Running service detection (parallel)...")

    docker_task = asyncio.to_thread(detect_docker)
    redis_task = asyncio.to_thread(detect_redis)
    postgres_task = asyncio.to_thread(detect_postgres)
    temporal_task = asyncio.to_thread(detect_temporal)
    gpu_task = asyncio.to_thread(detect_gpu)

    docker, redis, postgres, temporal, gpu = await asyncio.gather(
        docker_task,
        redis_task,
        postgres_task,
        temporal_task,
        gpu_task
    )

    results = DetectionResults(
        docker=docker,
        redis=redis,
        postgres=postgres,
        temporal=temporal,
        gpu=gpu
    )

    # Save to cache
    _save_to_cache(results)

    return results


def _get_cache_path() -> Path:
    """Get cache file path."""
    cache_dir = get_cache_dir()
    return cache_dir / "service-detection.json"


def _load_from_cache(ttl: int) -> Optional[DetectionResults]:
    """Load detection results from cache if fresh."""
    cache_path = _get_cache_path()

    if not cache_path.exists():
        return None

    try:
        with open(cache_path) as f:
            data = json.load(f)

        results = DetectionResults.from_dict(data)

        # Check if cache is fresh
        age = datetime.now() - results.timestamp
        if age > timedelta(seconds=ttl):
            logger.debug("Cache expired")
            return None

        return results

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f"Failed to load cache: {e}")
        return None


def _save_to_cache(results: DetectionResults) -> None:
    """Save detection results to cache."""
    cache_path = _get_cache_path()

    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        with open(cache_path, "w") as f:
            json.dump(results.to_dict(), f, indent=2)

        logger.debug(f"Saved detection results to cache: {cache_path}")

    except (OSError, TypeError) as e:
        logger.warning(f"Failed to save cache: {e}")
```

**CLI Integration**:

```python
# mycelium_onboarding/cli/detect_commands.py
"""CLI commands for service detection."""

import click
import asyncio
import json

from mycelium_onboarding.detection.orchestrator import detect_all_services


@click.command(name="detect")
@click.option(
    "--no-cache",
    is_flag=True,
    help="Skip cache, always run fresh detection"
)
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format"
)
def detect_services(no_cache: bool, format: str):
    """Detect available services."""
    use_cache = not no_cache

    # Run async detection
    results = asyncio.run(detect_all_services(use_cache=use_cache))

    if format == "json":
        click.echo(json.dumps(results.to_dict(), indent=2))
    else:
        _print_text_results(results)


def _print_text_results(results):
    """Print results in human-readable format."""
    click.echo("=== Service Detection Results ===\n")

    # Docker
    click.echo("Docker:")
    if results.docker.available:
        status = "✓ Available" if results.docker.running else "⚠ Not running"
        click.echo(f"  {status}")
        if results.docker.version:
            click.echo(f"  Version: {results.docker.version}")
        if results.docker.compose_available:
            click.echo(f"  Compose: {results.docker.compose_version or 'available'}")
    else:
        click.echo(f"  ✗ Not available ({results.docker.error})")

    # Redis
    click.echo("\nRedis:")
    if results.redis.available:
        click.echo(f"  ✓ Available at {results.redis.host}:{results.redis.port}")
        if results.redis.version:
            click.echo(f"  Version: {results.redis.version}")
    else:
        click.echo(f"  ✗ Not available ({results.redis.error})")

    # ... similar for postgres, temporal, gpu ...
```

**Acceptance Criteria**:
- [ ] Runs all detections in parallel (<5s total)
- [ ] Caches results to avoid repeated detection
- [ ] Respects cache TTL
- [ ] CLI command outputs text and JSON formats
- [ ] --no-cache flag forces fresh detection

**Deliverables**:
- `mycelium_onboarding/detection/orchestrator.py`
- `mycelium_onboarding/cli/detect_commands.py`
- `tests/test_detection_orchestrator.py`

---

## Exit Criteria

- [ ] **Service Detection**
  - [ ] Docker detection working (CLI, version, Compose)
  - [ ] Redis detection working (socket connection, version)
  - [ ] PostgreSQL detection working
  - [ ] Temporal detection working (frontend + UI)
  - [ ] GPU detection working (NVIDIA + AMD)

- [ ] **Detection Orchestrator**
  - [ ] Parallel execution (<5s total)
  - [ ] Caching implemented with configurable TTL
  - [ ] Cache invalidation working

- [ ] **CLI Integration**
  - [ ] `mycelium detect` command working
  - [ ] Text and JSON output formats
  - [ ] --no-cache flag working

- [ ] **Testing**
  - [ ] Unit tests for each detector (≥80% coverage)
  - [ ] Integration tests with mock services
  - [ ] Platform compatibility tests

- [ ] **Documentation**
  - [ ] Detection logic documented
  - [ ] Cache behavior explained
  - [ ] Troubleshooting guide for detection failures

## Deliverables

### Code Modules

- `mycelium_onboarding/detection/docker.py`
- `mycelium_onboarding/detection/redis.py`
- `mycelium_onboarding/detection/postgres.py`
- `mycelium_onboarding/detection/temporal.py`
- `mycelium_onboarding/detection/gpu.py`
- `mycelium_onboarding/detection/orchestrator.py`
- `mycelium_onboarding/cli/detect_commands.py`

### Tests

- `tests/test_docker_detection.py`
- `tests/test_redis_detection.py`
- `tests/test_postgres_detection.py`
- `tests/test_temporal_detection.py`
- `tests/test_gpu_detection.py`
- `tests/test_detection_orchestrator.py`

### Documentation

- `docs/service-detection.md`
- `docs/troubleshooting-detection.md`

## Risk Assessment

### High Risk

**Docker daemon not running**: Most common failure case
- **Mitigation**: Clear error message, instructions to start Docker
- **Contingency**: Offer Justfile deployment as fallback

**Firewall blocks service connections**: Detection may report services as unavailable when they're just firewalled
- **Mitigation**: Document common firewall issues
- **Contingency**: Allow manual override in wizard

### Medium Risk

**GPU detection inconsistent across platforms**: NVIDIA/AMD tools may not be installed even with GPU present
- **Mitigation**: Document GPU detection requirements
- **Contingency**: GPU is optional, gracefully handle absence

**Service version incompatibility**: Detected service may be too old
- **Mitigation**: Implement version checking where possible
- **Contingency**: Warn user, allow proceeding

### Low Risk

**Cache corruption**: Cached JSON may become corrupted
- **Mitigation**: Validate cache on load, discard if invalid
- **Contingency**: Fall back to fresh detection

## Dependencies for Next Milestones

### M04: Interactive Onboarding

**Depends on**:
- Detection results to pre-fill wizard defaults
- Service availability to guide user choices

**Will use**:
- `detect_all_services()` to populate wizard
- Detection results to enable/disable service options
- Error messages to help users fix issues

### M05: Deployment Generation

**Depends on**:
- Detection results to decide what to deploy

**Will use**:
- Docker availability to choose Docker Compose vs Justfile
- Service availability to skip deploying already-running services
- Port numbers from detection to avoid conflicts

---

**Milestone Version**: 1.0
**Last Updated**: 2025-10-13
**Status**: Ready for Implementation
