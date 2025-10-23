# Source: detection-reference.md
# Line: 625
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection.gpu_detector import detect_gpus

result = detect_gpus()

if result.available:
    print(f"Found {len(result.gpus)} GPU(s)")
    print(f"Total memory: {result.total_memory_mb} MB")

    for gpu in result.gpus:
        print(f"\n{gpu.vendor.value.upper()}: {gpu.model}")
        print(f"  Memory: {gpu.memory_mb} MB")
        print(f"  Driver: {gpu.driver_version}")

        if gpu.cuda_version:
            print(f"  CUDA: {gpu.cuda_version}")
        if gpu.rocm_version:
            print(f"  ROCm: {gpu.rocm_version}")
else:
    print(f"No GPUs detected: {result.error_message}")
