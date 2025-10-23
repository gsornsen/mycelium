# Source: detection-reference.md
# Line: 220
# Valid syntax: True
# Has imports: False
# Has assignments: False

@property
def has_docker(self) -> bool:
    """Check if Docker is available."""
    return self.docker.available

@property
def has_redis(self) -> bool:
    """Check if at least one Redis instance is available."""
    return any(r.available for r in self.redis)

@property
def has_postgres(self) -> bool:
    """Check if at least one PostgreSQL instance is available."""
    return any(p.available for p in self.postgres)

@property
def has_temporal(self) -> bool:
    """Check if Temporal is available."""
    return self.temporal.available

@property
def has_gpu(self) -> bool:
    """Check if at least one GPU is available."""
    return self.gpu.available
