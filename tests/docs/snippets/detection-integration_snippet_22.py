# Source: detection-integration.md
# Line: 852
# Valid syntax: True
# Has imports: True
# Has assignments: True

# celery.py
from celery import Celery

from mycelium_onboarding.detection import detect_all

app = Celery("myapp")

@app.on_after_configure.connect
def check_broker(sender, **kwargs):
    """Check if broker (Redis) is available."""
    summary = detect_all()

    if not summary.has_redis:
        raise RuntimeError("Redis broker not available")

    print(f"Using Redis broker on port {summary.redis[0].port}")
