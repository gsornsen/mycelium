# Source: detection-reference.md
# Line: 370
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection.redis_detector import scan_common_redis_ports

# Scan default ports
instances = scan_common_redis_ports()
for redis in instances:
    print(f"Redis {redis.version} on port {redis.port}")

# Scan custom ports
custom_instances = scan_common_redis_ports(
    host="localhost",
    ports=[6379, 6400, 6500],
    timeout=2.0
)