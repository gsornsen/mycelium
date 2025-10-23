# Source: detection-reference.md
# Line: 698
# Valid syntax: True
# Has imports: False
# Has assignments: True

class GPUVendor(str, Enum):
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    UNKNOWN = "unknown"
