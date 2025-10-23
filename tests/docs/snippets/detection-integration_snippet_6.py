# Source: detection-integration.md
# Line: 180
# Valid syntax: True
# Has imports: True
# Has assignments: True

from fastapi import FastAPI

from mycelium_onboarding.detection import detect_all_async

app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint with service detection."""
    summary = await detect_all_async()

    return {
        "status": "healthy",
        "services": {
            "docker": summary.has_docker,
            "redis": summary.has_redis,
            "postgres": summary.has_postgres,
            "temporal": summary.has_temporal,
            "gpu": summary.has_gpu,
        },
        "detection_time": summary.detection_time,
    }

@app.get("/health/detailed")
async def detailed_health():
    """Detailed health check with version info."""
    summary = await detect_all_async()

    details = {
        "docker": {
            "available": summary.has_docker,
            "version": summary.docker.version if summary.has_docker else None,
        },
        "redis": {
            "available": summary.has_redis,
            "instances": len(summary.redis),
        },
        "postgres": {
            "available": summary.has_postgres,
            "instances": len(summary.postgres),
        },
    }

    return details

@app.on_event("startup")
async def startup_event():
    """Check required services on startup."""
    summary = await detect_all_async()

    if not summary.has_redis:
        raise RuntimeError("Redis is required but not available")

    print(f"Startup checks passed in {summary.detection_time:.2f}s")
