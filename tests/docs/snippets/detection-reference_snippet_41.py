# Source: detection-reference.md
# Line: 825
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection import detect_all, generate_detection_report
import json

# Generate JSON report
summary = detect_all()
json_report = generate_detection_report(summary, format="json")
data = json.loads(json_report)

# Access specific values
docker_version = data["docker"]["version"]
redis_instances = len(data["redis"]["instances"])