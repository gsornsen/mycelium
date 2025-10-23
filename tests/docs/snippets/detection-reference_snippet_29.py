# Source: detection-reference.md
# Line: 568
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection.temporal_detector import detect_temporal

result = detect_temporal()

if result.available:
    print(f"Temporal {result.version} available")
    print(f"  Frontend: localhost:{result.frontend_port}")
    print(f"  UI: http://localhost:{result.ui_port}")
else:
    print(f"Temporal unavailable: {result.error_message}")
