# Source: detection-integration.md
# Line: 992
# Valid syntax: True
# Has imports: True
# Has assignments: True

from prometheus_client import Gauge, Counter
from mycelium_onboarding.detection import detect_all

# Define metrics
docker_available = Gauge("mycelium_docker_available", "Docker availability")
redis_available = Gauge("mycelium_redis_available", "Redis availability")
detection_time = Gauge("mycelium_detection_time_seconds", "Detection time")
detection_count = Counter("mycelium_detection_total", "Total detections")

def update_metrics():
    """Update Prometheus metrics from detection."""
    summary = detect_all()

    docker_available.set(1 if summary.has_docker else 0)
    redis_available.set(1 if summary.has_redis else 0)
    detection_time.set(summary.detection_time)
    detection_count.inc()

# Run periodically
import schedule
schedule.every(60).seconds.do(update_metrics)