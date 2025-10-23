# Source: detection-reference.md
# Line: 248
# Valid syntax: True
# Has imports: False
# Has assignments: True

summary = detect_all()

# Check availability
if summary.has_docker:
    print(f"Docker version: {summary.docker.version}")

# Access multiple instances
if summary.has_redis:
    print(f"Found {len(summary.redis)} Redis instance(s)")
    for i, redis in enumerate(summary.redis, 1):
        print(f"  {i}. {redis.host}:{redis.port}")

# Check detection performance
if summary.detection_time > 5.0:
    print("Warning: Detection took longer than expected")