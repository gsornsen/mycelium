# Source: detection-reference.md
# Line: 60
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection import detect_all

summary = detect_all()

if summary.has_docker:
    print(f"Docker {summary.docker.version} available")

if summary.has_redis:
    for redis in summary.redis:
        print(f"Redis instance on port {redis.port}")

print(f"Detection completed in {summary.detection_time:.2f}s")