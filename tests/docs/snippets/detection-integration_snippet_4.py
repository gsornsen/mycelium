# Source: detection-integration.md
# Line: 123
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection import detect_all

def select_redis_instance(prefer_authenticated=True):
    """Select appropriate Redis instance based on preferences."""
    summary = detect_all()

    if not summary.has_redis:
        return None

    # Filter instances based on preferences
    if prefer_authenticated:
        auth_instances = [r for r in summary.redis if r.password_required]
        if auth_instances:
            return auth_instances[0]

    # Default to first available
    return summary.redis[0]

redis_instance = select_redis_instance()
if redis_instance:
    print(f"Using Redis on port {redis_instance.port}")