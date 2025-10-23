# Source: projects/onboarding/milestones/M03_SERVICE_DETECTION.md
# Line: 559
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/detection/gpu.py
"""GPU detection."""

import shutil
import subprocess
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
    gpu_type: GPUType | None = None
    count: int = 0
    driver_version: str | None = None
    cuda_version: str | None = None
    devices: list[str] = None
    error: str | None = None

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


def _get_cuda_version(timeout: float) -> str | None:
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
