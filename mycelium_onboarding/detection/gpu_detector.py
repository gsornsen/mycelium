"""GPU detection for Mycelium onboarding.

This module provides cross-platform GPU detection supporting NVIDIA, AMD,
and Intel GPUs.
Detection is performed using vendor-specific tools (nvidia-smi, rocm-smi) and system
utilities (lspci, wmic, system_profiler).

The detection process:
1. Attempts NVIDIA GPU detection via nvidia-smi
2. Attempts AMD GPU detection via rocm-smi
3. Falls back to system tools for Intel/generic GPUs
4. Aggregates results with driver and runtime versions

Example:
    >>> from mycelium_onboarding.detection.gpu_detector import detect_gpus
    >>> result = detect_gpus()
    >>> if result.available:
    ...     print(f"Found {len(result.gpus)} GPU(s)")
    ...     for gpu in result.gpus:
    ...         print(f"  {gpu.vendor}: {gpu.model} ({gpu.memory_mb}MB)")
"""

from __future__ import annotations

import logging
import platform
import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Final

# Module logger
logger = logging.getLogger(__name__)

# Constants
DETECTION_TIMEOUT: Final[int] = 5  # seconds
NVIDIA_SMI_CMD: Final[str] = "nvidia-smi"
ROCM_SMI_CMD: Final[str] = "rocm-smi"
NVCC_CMD: Final[str] = "nvcc"

# Export list
__all__ = [
    "GPUVendor",
    "GPUInfo",
    "GPUDetectionResult",
    "detect_gpus",
    "detect_nvidia_gpus",
    "detect_amd_gpus",
    "detect_intel_gpus",
    "get_cuda_version",
    "get_rocm_version",
]


class GPUVendor(str, Enum):
    """Supported GPU vendors.

    Attributes:
        NVIDIA: NVIDIA GPUs (GeForce, Quadro, Tesla)
        AMD: AMD GPUs (Radeon, Instinct)
        INTEL: Intel GPUs (UHD, Iris, Arc)
        UNKNOWN: Unknown or unsupported GPU vendor
    """

    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    UNKNOWN = "unknown"


@dataclass
class GPUInfo:
    """Information about a detected GPU.

    Attributes:
        vendor: GPU vendor (NVIDIA, AMD, Intel, etc.)
        model: GPU model name
        memory_mb: GPU memory in megabytes (if available)
        driver_version: Driver version string (if available)
        cuda_version: CUDA version for NVIDIA GPUs (if available)
        rocm_version: ROCm version for AMD GPUs (if available)
        index: GPU index for multi-GPU systems
    """

    vendor: GPUVendor
    model: str
    memory_mb: int | None = None
    driver_version: str | None = None
    cuda_version: str | None = None
    rocm_version: str | None = None
    index: int = 0


@dataclass
class GPUDetectionResult:
    """Result of GPU detection.

    Attributes:
        available: True if any GPUs were detected
        gpus: List of detected GPUs
        total_memory_mb: Total GPU memory across all GPUs (MB)
        error_message: Error message if detection failed
    """

    available: bool
    gpus: list[GPUInfo] = field(default_factory=list)
    total_memory_mb: int = 0
    error_message: str | None = None


def detect_gpus() -> GPUDetectionResult:
    """Detect all available GPUs on the system.

    This function attempts to detect GPUs from all supported vendors:
    1. NVIDIA GPUs via nvidia-smi
    2. AMD GPUs via rocm-smi
    3. Intel GPUs via system tools

    Returns:
        GPUDetectionResult with all detected GPUs and aggregate information

    Example:
        >>> result = detect_gpus()
        >>> if result.available:
        ...     print(f"Total GPU memory: {result.total_memory_mb}MB")
    """
    all_gpus: list[GPUInfo] = []
    errors: list[str] = []

    # Detect NVIDIA GPUs
    try:
        nvidia_gpus = detect_nvidia_gpus()
        if nvidia_gpus:
            logger.info(f"Detected {len(nvidia_gpus)} NVIDIA GPU(s)")
            all_gpus.extend(nvidia_gpus)
    except Exception as e:
        error_msg = f"NVIDIA detection error: {e}"
        logger.debug(error_msg)
        errors.append(error_msg)

    # Detect AMD GPUs
    try:
        amd_gpus = detect_amd_gpus()
        if amd_gpus:
            logger.info(f"Detected {len(amd_gpus)} AMD GPU(s)")
            all_gpus.extend(amd_gpus)
    except Exception as e:
        error_msg = f"AMD detection error: {e}"
        logger.debug(error_msg)
        errors.append(error_msg)

    # Detect Intel GPUs (if no discrete GPUs found)
    if not all_gpus:
        try:
            intel_gpus = detect_intel_gpus()
            if intel_gpus:
                logger.info(f"Detected {len(intel_gpus)} Intel GPU(s)")
                all_gpus.extend(intel_gpus)
        except Exception as e:
            error_msg = f"Intel detection error: {e}"
            logger.debug(error_msg)
            errors.append(error_msg)

    # Calculate total memory
    total_memory = sum(gpu.memory_mb or 0 for gpu in all_gpus)

    # Build result
    if all_gpus:
        return GPUDetectionResult(
            available=True,
            gpus=all_gpus,
            total_memory_mb=total_memory,
        )
    error_message = "; ".join(errors) if errors else "No GPUs detected"
    return GPUDetectionResult(
        available=False,
        gpus=[],
        total_memory_mb=0,
        error_message=error_message,
    )


def detect_nvidia_gpus() -> list[GPUInfo]:
    """Detect NVIDIA GPUs using nvidia-smi.

    Executes nvidia-smi with CSV output format to query GPU information.
    Command: nvidia-smi --query-gpu=index,name,memory.total,
        driver_version --format=csv,noheader,nounits

    Returns:
        List of detected NVIDIA GPUs (empty list if none found or tool unavailable)

    Example:
        >>> gpus = detect_nvidia_gpus()
        >>> for gpu in gpus:
        ...     print(f"{gpu.model}: {gpu.memory_mb}MB")
    """
    try:
        # Query GPU information in CSV format
        result = subprocess.run(  # nosec B603 B607 - Safe execution of system tools
            [
                NVIDIA_SMI_CMD,
                "--query-gpu=index,name,memory.total,driver_version",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=DETECTION_TIMEOUT,
            check=False,
        )

        if result.returncode != 0:
            logger.debug(f"nvidia-smi returned non-zero: {result.returncode}")
            return []

        # Parse CSV output
        gpus: list[GPUInfo] = []
        cuda_version = get_cuda_version()

        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue

            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 4:
                logger.warning(f"Unexpected nvidia-smi output format: {line}")
                continue

            try:
                index = int(parts[0])
                name = parts[1]
                memory_mb = int(float(parts[2]))  # Handle decimal values
                driver_version = parts[3]

                gpu = GPUInfo(
                    vendor=GPUVendor.NVIDIA,
                    model=name,
                    memory_mb=memory_mb,
                    driver_version=driver_version,
                    cuda_version=cuda_version,
                    index=index,
                )
                gpus.append(gpu)
                logger.debug(f"Detected NVIDIA GPU {index}: {name}")

            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse nvidia-smi line '{line}': {e}")
                continue

        return gpus

    except FileNotFoundError:
        logger.debug("nvidia-smi not found")
        return []
    except subprocess.TimeoutExpired:
        logger.warning(f"nvidia-smi timed out after {DETECTION_TIMEOUT}s")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in NVIDIA detection: {e}")
        return []


def detect_amd_gpus() -> list[GPUInfo]:
    """Detect AMD GPUs using rocm-smi.

    Executes rocm-smi to query AMD GPU information. The tool provides
    product name and memory information.

    Returns:
        List of detected AMD GPUs (empty list if none found or tool unavailable)

    Note:
        ROCm tools may require specific privileges or ROCm installation.
    """
    try:
        # Get list of GPU devices
        result = subprocess.run(  # nosec B603 B607 - Safe execution of system tools
            [ROCM_SMI_CMD, "--showproductname"],
            capture_output=True,
            text=True,
            timeout=DETECTION_TIMEOUT,
            check=False,
        )

        if result.returncode != 0:
            logger.debug(f"rocm-smi returned non-zero: {result.returncode}")
            return []

        gpus: list[GPUInfo] = []
        rocm_version = get_rocm_version()

        # Parse rocm-smi output
        # Format: GPU[X]: Product Name: <name>
        gpu_pattern = re.compile(r"GPU\[(\d+)\].*?:\s*(.+?)(?:\n|$)", re.IGNORECASE)

        for match in gpu_pattern.finditer(result.stdout):
            try:
                index = int(match.group(1))
                model = match.group(2).strip()

                # Try to get memory info for this GPU
                memory_mb = _get_amd_gpu_memory(index)

                gpu = GPUInfo(
                    vendor=GPUVendor.AMD,
                    model=model,
                    memory_mb=memory_mb,
                    rocm_version=rocm_version,
                    index=index,
                )
                gpus.append(gpu)
                logger.debug(f"Detected AMD GPU {index}: {model}")

            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse rocm-smi output: {e}")
                continue

        return gpus

    except FileNotFoundError:
        logger.debug("rocm-smi not found")
        return []
    except subprocess.TimeoutExpired:
        logger.warning(f"rocm-smi timed out after {DETECTION_TIMEOUT}s")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in AMD detection: {e}")
        return []


def _get_amd_gpu_memory(gpu_index: int) -> int | None:
    """Get memory info for specific AMD GPU.

    Args:
        gpu_index: GPU index to query

    Returns:
        Memory in MB, or None if unavailable
    """
    try:
        result = subprocess.run(  # nosec B603 B607 - Safe execution of system tools
            [ROCM_SMI_CMD, "--showmeminfo", "vram", "-d", str(gpu_index)],
            capture_output=True,
            text=True,
            timeout=DETECTION_TIMEOUT,
            check=False,
        )

        if result.returncode == 0:
            # Parse memory from output (format varies)
            # Look for patterns like "Total: 8192 MB" or similar
            memory_pattern = re.compile(r"(\d+)\s*MB", re.IGNORECASE)
            match = memory_pattern.search(result.stdout)
            if match:
                return int(match.group(1))

    except Exception as e:
        logger.debug(f"Failed to get AMD GPU memory for index {gpu_index}: {e}")

    return None


def detect_intel_gpus() -> list[GPUInfo]:
    """Detect Intel GPUs using system tools.

    Detection strategy varies by platform:
    - Linux: lspci | grep -i vga
    - Windows: wmic path win32_VideoController get name
    - macOS: system_profiler SPDisplaysDataType

    Returns:
        List of detected Intel GPUs (empty list if none found)

    Note:
        This is a fallback method that provides basic information.
        Driver version and memory may not be available.
    """
    system = platform.system()

    if system == "Linux":
        return _detect_intel_gpus_linux()
    if system == "Darwin":
        return _detect_intel_gpus_macos()
    if system == "Windows":
        return _detect_intel_gpus_windows()
    logger.warning(f"Unsupported platform for Intel GPU detection: {system}")
    return []


def _detect_intel_gpus_linux() -> list[GPUInfo]:
    """Detect Intel GPUs on Linux using lspci."""
    try:
        result = subprocess.run(  # nosec B603 B607 - Safe execution of system tools
            ["lspci"],
            capture_output=True,
            text=True,
            timeout=DETECTION_TIMEOUT,
            check=False,
        )

        if result.returncode != 0:
            return []

        gpus: list[GPUInfo] = []
        index = 0

        # Look for VGA/3D/Display controllers with Intel
        for line in result.stdout.split("\n"):
            line_lower = line.lower()
            has_intel = ("vga" in line_lower or "3d" in line_lower or "display" in line_lower) and "intel" in line_lower
            if has_intel:
                # Extract model name
                # Format: 00:02.0 VGA compatible controller: Intel...
                parts = line.split(":")
                model = ":".join(parts[2:]).strip() if len(parts) >= 3 else "Intel GPU"

                gpu = GPUInfo(
                    vendor=GPUVendor.INTEL,
                    model=model,
                    index=index,
                )
                gpus.append(gpu)
                logger.debug(f"Detected Intel GPU: {model}")
                index += 1

        return gpus

    except FileNotFoundError:
        logger.debug("lspci not found")
        return []
    except Exception as e:
        logger.error(f"Error detecting Intel GPUs on Linux: {e}")
        return []


def _detect_intel_gpus_macos() -> list[GPUInfo]:
    """Detect Intel GPUs on macOS using system_profiler."""
    try:
        result = subprocess.run(  # nosec B603 B607 - Safe execution of system tools
            ["system_profiler", "SPDisplaysDataType"],
            capture_output=True,
            text=True,
            timeout=DETECTION_TIMEOUT,
            check=False,
        )

        if result.returncode != 0:
            return []

        gpus: list[GPUInfo] = []
        index = 0

        # Parse system_profiler output
        # Look for Intel GPUs in the output
        lines = result.stdout.split("\n")
        current_gpu: str | None = None
        current_vram: int | None = None

        for line in lines:
            line_stripped = line.strip()

            # Chipset Model indicates a new GPU entry
            if line_stripped.startswith("Chipset Model:"):
                if current_gpu and "intel" in current_gpu.lower():
                    gpu = GPUInfo(
                        vendor=GPUVendor.INTEL,
                        model=current_gpu,
                        memory_mb=current_vram,
                        index=index,
                    )
                    gpus.append(gpu)
                    logger.debug(f"Detected Intel GPU: {current_gpu}")
                    index += 1

                current_gpu = line_stripped.split(":", 1)[1].strip()
                current_vram = None

            # VRAM indicates memory
            elif line_stripped.startswith("VRAM"):
                vram_str = line_stripped.split(":", 1)[1].strip()
                # Parse "8192 MB" or "8 GB"
                vram_match = re.search(r"(\d+)\s*(MB|GB)", vram_str, re.IGNORECASE)
                if vram_match:
                    vram_value = int(vram_match.group(1))
                    vram_unit = vram_match.group(2).upper()
                    current_vram = vram_value * 1024 if vram_unit == "GB" else vram_value

        # Handle last GPU
        if current_gpu and "intel" in current_gpu.lower():
            gpu = GPUInfo(
                vendor=GPUVendor.INTEL,
                model=current_gpu,
                memory_mb=current_vram,
                index=index,
            )
            gpus.append(gpu)
            logger.debug(f"Detected Intel GPU: {current_gpu}")

        return gpus

    except FileNotFoundError:
        logger.debug("system_profiler not found")
        return []
    except Exception as e:
        logger.error(f"Error detecting Intel GPUs on macOS: {e}")
        return []


def _detect_intel_gpus_windows() -> list[GPUInfo]:
    """Detect Intel GPUs on Windows using wmic."""
    try:
        result = subprocess.run(  # nosec B603 B607 - Safe execution of system tools
            ["wmic", "path", "win32_VideoController", "get", "name"],
            capture_output=True,
            text=True,
            timeout=DETECTION_TIMEOUT,
            check=False,
        )

        if result.returncode != 0:
            return []

        gpus: list[GPUInfo] = []
        index = 0

        # Parse wmic output
        lines = result.stdout.split("\n")
        for line in lines[1:]:  # Skip header
            line_stripped = line.strip()
            if line_stripped and "intel" in line_stripped.lower():
                gpu = GPUInfo(
                    vendor=GPUVendor.INTEL,
                    model=line_stripped,
                    index=index,
                )
                gpus.append(gpu)
                logger.debug(f"Detected Intel GPU: {line_stripped}")
                index += 1

        return gpus

    except FileNotFoundError:
        logger.debug("wmic not found")
        return []
    except Exception as e:
        logger.error(f"Error detecting Intel GPUs on Windows: {e}")
        return []


def get_cuda_version() -> str | None:
    """Get installed CUDA version.

    Attempts to determine CUDA version using:
    1. nvcc --version (CUDA Toolkit)
    2. nvidia-smi (Driver CUDA version)

    Returns:
        CUDA version string (e.g., "11.8"), or None if unavailable
    """
    # Try nvcc first (CUDA Toolkit version)
    try:
        result = subprocess.run(  # nosec B603 B607 - Safe execution of system tools
            [NVCC_CMD, "--version"],
            capture_output=True,
            text=True,
            timeout=DETECTION_TIMEOUT,
            check=False,
        )

        if result.returncode == 0:
            # Parse version from output: "release 11.8, V11.8.89"
            version_match = re.search(r"release (\d+\.\d+)", result.stdout)
            if version_match:
                version = version_match.group(1)
                logger.debug(f"Detected CUDA version (nvcc): {version}")
                return version

    except FileNotFoundError:
        logger.debug("nvcc not found")
    except Exception as e:
        logger.debug(f"Error getting CUDA version from nvcc: {e}")

    # Try nvidia-smi as fallback
    try:
        result = subprocess.run(  # nosec B603 B607 - Safe execution of system tools
            [NVIDIA_SMI_CMD, "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=DETECTION_TIMEOUT,
            check=False,
        )

        if result.returncode == 0:
            # Get CUDA version from nvidia-smi
            result2 = subprocess.run(
                [NVIDIA_SMI_CMD],
                capture_output=True,
                text=True,
                timeout=DETECTION_TIMEOUT,
                check=False,
            )

            if result2.returncode == 0:
                # Parse "CUDA Version: 11.8" from header
                cuda_match = re.search(r"CUDA Version:\s*(\d+\.\d+)", result2.stdout)
                if cuda_match:
                    version = cuda_match.group(1)
                    logger.debug(f"Detected CUDA version (nvidia-smi): {version}")
                    return version

    except FileNotFoundError:
        pass
    except Exception as e:
        logger.debug(f"Error getting CUDA version from nvidia-smi: {e}")

    return None


def get_rocm_version() -> str | None:
    """Get installed ROCm version.

    Attempts to determine ROCm version from:
    1. /opt/rocm/.info/version file
    2. rocm-smi --version output

    Returns:
        ROCm version string (e.g., "5.4.0"), or None if unavailable
    """
    # Try version file first
    version_file = Path("/opt/rocm/.info/version")
    if version_file.exists():
        try:
            version = version_file.read_text().strip()
            logger.debug(f"Detected ROCm version (file): {version}")
            return version
        except Exception as e:
            logger.debug(f"Error reading ROCm version file: {e}")

    # Try rocm-smi --version
    try:
        result = subprocess.run(  # nosec B603 B607 - Safe execution of system tools
            [ROCM_SMI_CMD, "--version"],
            capture_output=True,
            text=True,
            timeout=DETECTION_TIMEOUT,
            check=False,
        )

        if result.returncode == 0:
            # Parse version from output
            version_match = re.search(r"(\d+\.\d+\.\d+)", result.stdout)
            if version_match:
                version = version_match.group(1)
                logger.debug(f"Detected ROCm version (rocm-smi): {version}")
                return version

    except FileNotFoundError:
        logger.debug("rocm-smi not found")
    except Exception as e:
        logger.debug(f"Error getting ROCm version: {e}")

    return None
