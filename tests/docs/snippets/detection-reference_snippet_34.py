# Source: detection-reference.md
# Line: 672
# Valid syntax: True
# Has imports: False
# Has assignments: True

@dataclass
class GPU:
    vendor: GPUVendor
    model: str
    memory_mb: int | None
    driver_version: str | None
    cuda_version: str | None
    rocm_version: str | None
    index: int
