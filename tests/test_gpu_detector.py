"""Tests for GPU detection module.

This module tests GPU detection across multiple vendors (NVIDIA, AMD, Intel)
and platforms (Linux, macOS, Windows/WSL2). Tests use mocked subprocess calls
to simulate various hardware configurations without requiring actual GPUs.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from mycelium_onboarding.detection.gpu_detector import (
    GPUDetectionResult,
    GPUInfo,
    GPUVendor,
    detect_amd_gpus,
    detect_gpus,
    detect_intel_gpus,
    detect_nvidia_gpus,
    get_cuda_version,
    get_rocm_version,
)


class TestNvidiaGPUDetection:
    """Tests for NVIDIA GPU detection."""

    def test_detect_nvidia_gpus_single_gpu(self) -> None:
        """Test successful detection of single NVIDIA GPU."""
        mock_output = "0, NVIDIA GeForce RTX 3080, 10240, 470.57.02\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            gpus = detect_nvidia_gpus()

            assert len(gpus) == 1
            assert gpus[0].vendor == GPUVendor.NVIDIA
            assert gpus[0].model == "NVIDIA GeForce RTX 3080"
            assert gpus[0].memory_mb == 10240
            assert gpus[0].driver_version == "470.57.02"
            assert gpus[0].index == 0

    def test_detect_nvidia_gpus_multiple_gpus(self) -> None:
        """Test detection of multiple NVIDIA GPUs."""
        mock_output = (
            "0, NVIDIA GeForce RTX 3080, 10240, 470.57.02\n"
            "1, NVIDIA GeForce RTX 3090, 24576, 470.57.02\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            gpus = detect_nvidia_gpus()

            assert len(gpus) == 2
            assert gpus[0].model == "NVIDIA GeForce RTX 3080"
            assert gpus[0].memory_mb == 10240
            assert gpus[0].index == 0
            assert gpus[1].model == "NVIDIA GeForce RTX 3090"
            assert gpus[1].memory_mb == 24576
            assert gpus[1].index == 1

    def test_detect_nvidia_gpus_decimal_memory(self) -> None:
        """Test handling of decimal memory values."""
        mock_output = "0, NVIDIA Tesla V100, 16160.5, 510.47.03\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            gpus = detect_nvidia_gpus()

            assert len(gpus) == 1
            assert gpus[0].memory_mb == 16160
            assert gpus[0].model == "NVIDIA Tesla V100"

    def test_detect_nvidia_gpus_not_installed(self) -> None:
        """Test NVIDIA detection when nvidia-smi not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            gpus = detect_nvidia_gpus()
            assert len(gpus) == 0

    def test_detect_nvidia_gpus_no_gpus(self) -> None:
        """Test NVIDIA detection when no GPUs present."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="",
            )

            gpus = detect_nvidia_gpus()
            assert len(gpus) == 0

    def test_detect_nvidia_gpus_command_fails(self) -> None:
        """Test NVIDIA detection when nvidia-smi command fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Error: Failed to initialize NVML",
            )

            gpus = detect_nvidia_gpus()
            assert len(gpus) == 0

    def test_detect_nvidia_gpus_timeout(self) -> None:
        """Test NVIDIA detection when command times out."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("nvidia-smi", 5)):
            gpus = detect_nvidia_gpus()
            assert len(gpus) == 0

    def test_detect_nvidia_gpus_malformed_output(self) -> None:
        """Test NVIDIA detection with malformed CSV output."""
        mock_output = "0, NVIDIA GeForce RTX 3080\n"  # Missing fields
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            gpus = detect_nvidia_gpus()
            # Should handle gracefully and return empty list
            assert len(gpus) == 0

    def test_detect_nvidia_gpus_with_cuda_version(self) -> None:
        """Test NVIDIA detection includes CUDA version."""
        mock_output = "0, NVIDIA GeForce RTX 3080, 10240, 470.57.02\n"
        with patch("subprocess.run") as mock_run, \
             patch("mycelium_onboarding.detection.gpu_detector.get_cuda_version", return_value="11.8"):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            gpus = detect_nvidia_gpus()

            assert len(gpus) == 1
            assert gpus[0].cuda_version == "11.8"


class TestAMDGPUDetection:
    """Tests for AMD GPU detection."""

    def test_detect_amd_gpus_single_gpu(self) -> None:
        """Test successful detection of single AMD GPU."""
        mock_output = "GPU[0]: AMD Radeon RX 6900 XT\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            gpus = detect_amd_gpus()

            assert len(gpus) == 1
            assert gpus[0].vendor == GPUVendor.AMD
            assert gpus[0].model == "AMD Radeon RX 6900 XT"
            assert gpus[0].index == 0

    def test_detect_amd_gpus_multiple_gpus(self) -> None:
        """Test detection of multiple AMD GPUs."""
        mock_output = (
            "GPU[0]: AMD Radeon RX 6900 XT\n"
            "GPU[1]: AMD Radeon RX 6800\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            gpus = detect_amd_gpus()

            assert len(gpus) == 2
            assert gpus[0].model == "AMD Radeon RX 6900 XT"
            assert gpus[0].index == 0
            assert gpus[1].model == "AMD Radeon RX 6800"
            assert gpus[1].index == 1

    def test_detect_amd_gpus_not_installed(self) -> None:
        """Test AMD detection when rocm-smi not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            gpus = detect_amd_gpus()
            assert len(gpus) == 0

    def test_detect_amd_gpus_command_fails(self) -> None:
        """Test AMD detection when rocm-smi command fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Error: No GPUs found",
            )

            gpus = detect_amd_gpus()
            assert len(gpus) == 0

    def test_detect_amd_gpus_with_rocm_version(self) -> None:
        """Test AMD detection includes ROCm version."""
        mock_output = "GPU[0]: AMD Radeon RX 6900 XT\n"
        with patch("subprocess.run") as mock_run, \
             patch("mycelium_onboarding.detection.gpu_detector.get_rocm_version", return_value="5.4.0"):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            gpus = detect_amd_gpus()

            assert len(gpus) == 1
            assert gpus[0].rocm_version == "5.4.0"

    def test_detect_amd_gpus_timeout(self) -> None:
        """Test AMD detection when command times out."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("rocm-smi", 5)):
            gpus = detect_amd_gpus()
            assert len(gpus) == 0


class TestIntelGPUDetection:
    """Tests for Intel GPU detection."""

    def test_detect_intel_gpus_linux(self) -> None:
        """Test Intel GPU detection on Linux."""
        mock_output = (
            "00:02.0 VGA compatible controller: Intel Corporation "
            "UHD Graphics 630 (rev 04)\n"
        )
        with patch("platform.system", return_value="Linux"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            gpus = detect_intel_gpus()

            assert len(gpus) == 1
            assert gpus[0].vendor == GPUVendor.INTEL
            assert "Intel Corporation" in gpus[0].model
            assert gpus[0].index == 0

    def test_detect_intel_gpus_linux_multiple(self) -> None:
        """Test detection of multiple Intel GPUs on Linux."""
        mock_output = (
            "00:02.0 VGA compatible controller: Intel Corporation "
            "UHD Graphics 630 (rev 04)\n"
            "01:00.0 3D controller: Intel Corporation DG1 [Iris Xe MAX]\n"
        )
        with patch("platform.system", return_value="Linux"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            gpus = detect_intel_gpus()

            assert len(gpus) == 2
            assert gpus[0].index == 0
            assert gpus[1].index == 1

    def test_detect_intel_gpus_linux_no_intel(self) -> None:
        """Test Intel GPU detection on Linux with no Intel GPUs."""
        mock_output = (
            "01:00.0 VGA compatible controller: NVIDIA Corporation "
            "GA102 [GeForce RTX 3080]\n"
        )
        with patch("platform.system", return_value="Linux"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            gpus = detect_intel_gpus()
            assert len(gpus) == 0

    def test_detect_intel_gpus_linux_lspci_not_found(self) -> None:
        """Test Intel GPU detection when lspci not available."""
        with patch("platform.system", return_value="Linux"), \
             patch("subprocess.run", side_effect=FileNotFoundError):
            gpus = detect_intel_gpus()
            assert len(gpus) == 0

    def test_detect_intel_gpus_macos(self) -> None:
        """Test Intel GPU detection on macOS."""
        mock_output = """Graphics/Displays:

    Intel UHD Graphics 630:

      Chipset Model: Intel UHD Graphics 630
      Type: GPU
      Bus: Built-In
      VRAM (Dynamic, Max): 1536 MB
      Vendor: Intel
      Device ID: 0x3e9b
"""
        with patch("platform.system", return_value="Darwin"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            gpus = detect_intel_gpus()

            assert len(gpus) == 1
            assert gpus[0].vendor == GPUVendor.INTEL
            assert gpus[0].model == "Intel UHD Graphics 630"
            assert gpus[0].memory_mb == 1536

    def test_detect_intel_gpus_macos_gb_memory(self) -> None:
        """Test Intel GPU detection on macOS with GB memory."""
        mock_output = """Graphics/Displays:

    Intel Iris Plus Graphics:

      Chipset Model: Intel Iris Plus Graphics
      VRAM (Dynamic, Max): 2 GB
"""
        with patch("platform.system", return_value="Darwin"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            gpus = detect_intel_gpus()

            assert len(gpus) == 1
            assert gpus[0].memory_mb == 2048  # Converted from GB

    def test_detect_intel_gpus_macos_no_intel(self) -> None:
        """Test Intel GPU detection on macOS with no Intel GPUs."""
        mock_output = """Graphics/Displays:

    AMD Radeon Pro 5500M:

      Chipset Model: AMD Radeon Pro 5500M
      Type: GPU
      VRAM (Dynamic, Max): 8192 MB
"""
        with patch("platform.system", return_value="Darwin"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            gpus = detect_intel_gpus()
            assert len(gpus) == 0

    def test_detect_intel_gpus_windows(self) -> None:
        """Test Intel GPU detection on Windows."""
        mock_output = """Name
Intel(R) UHD Graphics 630
"""
        with patch("platform.system", return_value="Windows"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            gpus = detect_intel_gpus()

            assert len(gpus) == 1
            assert gpus[0].vendor == GPUVendor.INTEL
            assert gpus[0].model == "Intel(R) UHD Graphics 630"

    def test_detect_intel_gpus_unsupported_platform(self) -> None:
        """Test Intel GPU detection on unsupported platform."""
        with patch("platform.system", return_value="FreeBSD"):
            gpus = detect_intel_gpus()
            assert len(gpus) == 0


class TestCUDAVersion:
    """Tests for CUDA version detection."""

    def test_get_cuda_version_from_nvcc(self) -> None:
        """Test CUDA version detection from nvcc."""
        mock_output = "Cuda compilation tools, release 11.8, V11.8.89\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            version = get_cuda_version()
            assert version == "11.8"

    def test_get_cuda_version_from_nvidia_smi(self) -> None:
        """Test CUDA version detection from nvidia-smi."""
        # First call to nvcc fails
        # Second call to nvidia-smi succeeds
        mock_outputs = [
            MagicMock(returncode=1, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="470.57.02\n", stderr=""),
            MagicMock(
                returncode=0,
                stdout="CUDA Version: 11.8  Driver Version: 470.57.02\n",
                stderr="",
            ),
        ]
        with patch("subprocess.run", side_effect=mock_outputs):
            version = get_cuda_version()
            assert version == "11.8"

    def test_get_cuda_version_not_found(self) -> None:
        """Test CUDA version when CUDA not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            version = get_cuda_version()
            assert version is None

    def test_get_cuda_version_parse_error(self) -> None:
        """Test CUDA version with unparseable output."""
        mock_output = "Some unexpected output\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            version = get_cuda_version()
            assert version is None


class TestROCmVersion:
    """Tests for ROCm version detection."""

    def test_get_rocm_version_from_file(self, tmp_path: Path) -> None:
        """Test ROCm version detection from version file."""
        version_file = tmp_path / ".info" / "version"
        version_file.parent.mkdir(parents=True)
        version_file.write_text("5.4.0\n")

        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value="5.4.0\n"):
            version = get_rocm_version()
            assert version == "5.4.0"

    def test_get_rocm_version_from_rocm_smi(self) -> None:
        """Test ROCm version detection from rocm-smi."""
        mock_output = "ROCm System Management Interface version: 5.4.0\n"
        with patch("pathlib.Path.exists", return_value=False), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            version = get_rocm_version()
            assert version == "5.4.0"

    def test_get_rocm_version_not_found(self) -> None:
        """Test ROCm version when ROCm not installed."""
        with patch("pathlib.Path.exists", return_value=False), \
             patch("subprocess.run", side_effect=FileNotFoundError):
            version = get_rocm_version()
            assert version is None


class TestGPUDetectionIntegration:
    """Integration tests for overall GPU detection."""

    def test_detect_gpus_nvidia_only(self) -> None:
        """Test GPU detection with only NVIDIA GPUs."""
        mock_output = "0, NVIDIA GeForce RTX 3080, 10240, 470.57.02\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            result = detect_gpus()

            assert result.available is True
            assert len(result.gpus) == 1
            assert result.gpus[0].vendor == GPUVendor.NVIDIA
            assert result.total_memory_mb == 10240
            assert result.error_message is None

    def test_detect_gpus_amd_only(self) -> None:
        """Test GPU detection with only AMD GPUs."""
        # NVIDIA detection fails
        # AMD detection succeeds
        call_count = 0

        def mock_run(*args: Any, **kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # nvidia-smi
                return MagicMock(returncode=1, stdout="", stderr="")
            # rocm-smi
            return MagicMock(
                returncode=0,
                stdout="GPU[0]: AMD Radeon RX 6900 XT\n",
                stderr="",
            )

        with patch("subprocess.run", side_effect=mock_run):
            result = detect_gpus()

            assert result.available is True
            assert len(result.gpus) == 1
            assert result.gpus[0].vendor == GPUVendor.AMD

    def test_detect_gpus_multiple_vendors(self) -> None:
        """Test detection when multiple GPU vendors present."""
        call_count = 0

        def mock_run(*args: Any, **kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # nvidia-smi
                return MagicMock(
                    returncode=0,
                    stdout="0, NVIDIA GeForce RTX 3080, 10240, 470.57.02\n",
                    stderr="",
                )
            # rocm-smi
            return MagicMock(
                returncode=0,
                stdout="GPU[0]: AMD Radeon RX 6900 XT\n",
                stderr="",
            )

        with patch("subprocess.run", side_effect=mock_run):
            result = detect_gpus()

            assert result.available is True
            assert len(result.gpus) == 2
            assert result.gpus[0].vendor == GPUVendor.NVIDIA
            assert result.gpus[1].vendor == GPUVendor.AMD
            assert result.total_memory_mb == 10240  # Only NVIDIA has memory info

    def test_detect_gpus_no_gpus(self) -> None:
        """Test detection when no GPUs available."""
        with patch("subprocess.run") as mock_run, \
             patch("platform.system", return_value="Linux"):
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="",
            )

            result = detect_gpus()

            assert result.available is False
            assert len(result.gpus) == 0
            assert result.total_memory_mb == 0
            assert result.error_message is not None

    def test_detect_gpus_intel_fallback(self) -> None:
        """Test Intel GPU detection as fallback."""
        call_count = 0

        def mock_run(*args: Any, **kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # nvidia-smi and rocm-smi fail
                return MagicMock(returncode=1, stdout="", stderr="")
            # lspci succeeds
            return MagicMock(
                returncode=0,
                stdout="00:02.0 VGA compatible controller: Intel Corporation UHD Graphics 630\n",
                stderr="",
            )

        with patch("subprocess.run", side_effect=mock_run), \
             patch("platform.system", return_value="Linux"):
            result = detect_gpus()

            assert result.available is True
            assert len(result.gpus) == 1
            assert result.gpus[0].vendor == GPUVendor.INTEL

    def test_detect_gpus_total_memory_calculation(self) -> None:
        """Test total memory calculation across multiple GPUs."""
        mock_output = (
            "0, NVIDIA GeForce RTX 3080, 10240, 470.57.02\n"
            "1, NVIDIA GeForce RTX 3090, 24576, 470.57.02\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr="",
            )

            result = detect_gpus()

            assert result.available is True
            assert len(result.gpus) == 2
            assert result.total_memory_mb == 34816  # 10240 + 24576

    def test_detect_gpus_permission_error(self) -> None:
        """Test GPU detection with permission errors."""
        with patch("subprocess.run", side_effect=PermissionError("Permission denied")), \
             patch("platform.system", return_value="Linux"):
            result = detect_gpus()

            assert result.available is False
            assert len(result.gpus) == 0
            assert result.error_message is not None


class TestGPUInfo:
    """Tests for GPUInfo dataclass."""

    def test_gpu_info_minimal(self) -> None:
        """Test GPUInfo with minimal required fields."""
        gpu = GPUInfo(vendor=GPUVendor.NVIDIA, model="Test GPU")

        assert gpu.vendor == GPUVendor.NVIDIA
        assert gpu.model == "Test GPU"
        assert gpu.memory_mb is None
        assert gpu.driver_version is None
        assert gpu.cuda_version is None
        assert gpu.rocm_version is None
        assert gpu.index == 0

    def test_gpu_info_complete(self) -> None:
        """Test GPUInfo with all fields populated."""
        gpu = GPUInfo(
            vendor=GPUVendor.NVIDIA,
            model="NVIDIA GeForce RTX 3080",
            memory_mb=10240,
            driver_version="470.57.02",
            cuda_version="11.8",
            index=1,
        )

        assert gpu.vendor == GPUVendor.NVIDIA
        assert gpu.model == "NVIDIA GeForce RTX 3080"
        assert gpu.memory_mb == 10240
        assert gpu.driver_version == "470.57.02"
        assert gpu.cuda_version == "11.8"
        assert gpu.index == 1


class TestGPUDetectionResult:
    """Tests for GPUDetectionResult dataclass."""

    def test_detection_result_success(self) -> None:
        """Test successful detection result."""
        gpu = GPUInfo(
            vendor=GPUVendor.NVIDIA,
            model="NVIDIA GeForce RTX 3080",
            memory_mb=10240,
        )
        result = GPUDetectionResult(
            available=True,
            gpus=[gpu],
            total_memory_mb=10240,
        )

        assert result.available is True
        assert len(result.gpus) == 1
        assert result.total_memory_mb == 10240
        assert result.error_message is None

    def test_detection_result_failure(self) -> None:
        """Test failed detection result."""
        result = GPUDetectionResult(
            available=False,
            gpus=[],
            total_memory_mb=0,
            error_message="No GPUs detected",
        )

        assert result.available is False
        assert len(result.gpus) == 0
        assert result.total_memory_mb == 0
        assert result.error_message == "No GPUs detected"

    def test_detection_result_defaults(self) -> None:
        """Test detection result with default values."""
        result = GPUDetectionResult(available=False)

        assert result.available is False
        assert result.gpus == []
        assert result.total_memory_mb == 0
        assert result.error_message is None


class TestGPUVendorEnum:
    """Tests for GPUVendor enum."""

    def test_gpu_vendor_values(self) -> None:
        """Test GPUVendor enum values."""
        assert GPUVendor.NVIDIA == "nvidia"
        assert GPUVendor.AMD == "amd"
        assert GPUVendor.INTEL == "intel"
        assert GPUVendor.UNKNOWN == "unknown"

    def test_gpu_vendor_from_string(self) -> None:
        """Test creating GPUVendor from string."""
        assert GPUVendor("nvidia") == GPUVendor.NVIDIA
        assert GPUVendor("amd") == GPUVendor.AMD
        assert GPUVendor("intel") == GPUVendor.INTEL
