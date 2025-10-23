# Source: detection-integration.md
# Line: 321
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.config.manager import ConfigManager
from mycelium_onboarding.detection import detect_all


def update_redis_config_only():
    """Update only Redis configuration from detection."""
    summary = detect_all()
    manager = ConfigManager()
    config = manager.load()

    if summary.has_redis:
        redis_instance = summary.redis[0]
        config.services.redis.enabled = True
        config.services.redis.port = redis_instance.port

        if redis_instance.version:
            config.services.redis.version = redis_instance.version

        manager.save(config)
        print(f"Updated Redis config: port {redis_instance.port}")
    else:
        print("Redis not detected, config unchanged")

update_redis_config_only()
