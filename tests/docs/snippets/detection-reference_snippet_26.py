# Source: detection-reference.md
# Line: 504
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection.postgres_detector import detect_postgres

result = detect_postgres(host="localhost", port=5432)
if result.available:
    print(f"PostgreSQL {result.version}")
    print(f"Authentication: {result.authentication_method}")
