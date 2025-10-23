# Source: detection-reference.md
# Line: 861
# Valid syntax: True
# Has imports: True
# Has assignments: True

import time
from functools import lru_cache

@lru_cache(maxsize=1)
def cached_detect_all():
    return detect_all()

# Clear cache every 60 seconds
last_detection = time.time()
if time.time() - last_detection > 60:
    cached_detect_all.cache_clear()
    last_detection = time.time()