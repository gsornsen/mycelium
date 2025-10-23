# Source: detection-integration.md
# Line: 948
# Valid syntax: True
# Has imports: True
# Has assignments: True

from fastapi import FastAPI, status
from mycelium_onboarding.detection import detect_all

app = FastAPI()

@app.get("/health/liveness")
async def liveness():
    """Liveness probe - is the application running?"""
    return {"status": "alive"}

@app.get("/health/readiness")
async def readiness():
    """Readiness probe - can the application serve traffic?"""
    summary = detect_all()

    # Check critical services
    if not summary.has_redis or not summary.has_postgres:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "reason": "required services unavailable"}
        )

    return {"status": "ready"}

@app.get("/health/startup")
async def startup():
    """Startup probe - has initialization completed?"""
    # Perform full detection
    summary = detect_all()

    if summary.detection_time > 10.0:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "starting", "reason": "detection too slow"}
        )

    return {"status": "started"}