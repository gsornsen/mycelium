# Source: detection-reference.md
# Line: 471
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection.postgres_detector import scan_common_postgres_ports

instances = scan_common_postgres_ports()
for pg in instances:
    print(f"PostgreSQL {pg.version} on port {pg.port}")
    print(f"  Auth method: {pg.authentication_method}")
