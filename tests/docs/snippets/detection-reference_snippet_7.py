# Source: detection-reference.md
# Line: 136
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection import detect_all, generate_detection_report

summary = detect_all()

# Human-readable text
text_report = generate_detection_report(summary, format="text")
print(text_report)

# Machine-readable JSON
json_report = generate_detection_report(summary, format="json")
import json
data = json.loads(json_report)

# YAML for config management
yaml_report = generate_detection_report(summary, format="yaml")