# Source: detection-reference.md
# Line: 410
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection.redis_detector import detect_redis

result = detect_redis(host="localhost", port=6379)
if result.available:
    if result.password_required:
        print("Redis requires authentication")
    else:
        print(f"Redis {result.version} accessible")
