# Source: detection-integration.md
# Line: 61
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection import detect_all

def initialize_caching():
    """Initialize caching with Redis if available, else use memory cache."""
    summary = detect_all()

    if summary.has_redis:
        # Use Redis for distributed caching
        import redis
        redis_instance = summary.redis[0]
        cache = redis.Redis(
            host=redis_instance.host,
            port=redis_instance.port
        )
        print(f"Using Redis cache on port {redis_instance.port}")
    else:
        # Fallback to in-memory cache
        from cachetools import TTLCache
        cache = TTLCache(maxsize=1000, ttl=300)
        print("Using in-memory cache (Redis not available)")

    return cache

cache = initialize_caching()