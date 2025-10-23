# Source: detection-integration.md
# Line: 557
# Valid syntax: True
# Has imports: True
# Has assignments: True

import time

from mycelium_onboarding.detection import detect_all

# Simple cache with TTL
_detection_cache = None
_cache_timestamp = 0
_cache_ttl = 60  # seconds

def cached_detect_all(ttl=60):
    """Detect all services with caching."""
    global _detection_cache, _cache_timestamp, _cache_ttl

    _cache_ttl = ttl
    current_time = time.time()

    # Return cached result if still valid
    if _detection_cache and (current_time - _cache_timestamp) < _cache_ttl:
        return _detection_cache

    # Run detection and cache result
    _detection_cache = detect_all()
    _cache_timestamp = current_time

    return _detection_cache

# Usage
summary1 = cached_detect_all(ttl=60)  # Runs detection
summary2 = cached_detect_all(ttl=60)  # Returns cached (fast)
