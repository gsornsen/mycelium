# Source: detection-integration.md
# Line: 351
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection import detect_all
from mycelium_onboarding.config.manager import ConfigManager

def validate_config_against_detection():
    """Validate that configured services are actually available."""
    manager = ConfigManager()
    config = manager.load()
    summary = detect_all()

    issues = []

    # Check Redis
    if config.services.redis.enabled and not summary.has_redis:
        issues.append("Redis is enabled in config but not detected")

    # Check PostgreSQL
    if config.services.postgres.enabled and not summary.has_postgres:
        issues.append("PostgreSQL is enabled in config but not detected")

    # Check Temporal
    if config.services.temporal.enabled and not summary.has_temporal:
        issues.append("Temporal is enabled in config but not detected")

    # Check port mismatches
    if summary.has_redis:
        configured_port = config.services.redis.port
        detected_ports = [r.port for r in summary.redis]
        if configured_port not in detected_ports:
            issues.append(
                f"Redis configured on port {configured_port} but detected on {detected_ports}"
            )

    if issues:
        print("Configuration validation issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("Configuration validated successfully")
        return True

validate_config_against_detection()