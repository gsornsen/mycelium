# Source: detection-integration.md
# Line: 278
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection import detect_all, update_config_from_detection
from mycelium_onboarding.config.manager import ConfigManager

def auto_configure():
    """Automatically configure services based on detection."""
    # Detect services
    print("Detecting services...")
    summary = detect_all()

    # Load existing config or create new
    manager = ConfigManager()
    try:
        base_config = manager.load()
        print("Loaded existing configuration")
    except FileNotFoundError:
        base_config = None
        print("Creating new configuration")

    # Update config with detected values
    config = update_config_from_detection(summary, base_config)

    # Save updated config
    manager.save(config)
    print("Configuration updated successfully")

    # Report changes
    if summary.has_redis:
        print(f"  Redis: enabled on port {config.services.redis.port}")
    if summary.has_postgres:
        print(f"  PostgreSQL: enabled on port {config.services.postgres.port}")
    if summary.has_temporal:
        print(f"  Temporal: enabled on ports {config.services.temporal.ui_port}/{config.services.temporal.frontend_port}")

    return config

config = auto_configure()