# Source: detection-reference.md
# Line: 287
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection.docker_detector import detect_docker

result = detect_docker()

if result.available:
    print(f"Docker {result.version} available at {result.socket_path}")
else:
    print(f"Docker unavailable: {result.error_message}")