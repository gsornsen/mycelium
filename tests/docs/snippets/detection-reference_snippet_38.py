# Source: detection-reference.md
# Line: 786
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection import detect_all

# Simple detection
summary = detect_all()
print(f"Services available: {summary.has_docker}, {summary.has_redis}")