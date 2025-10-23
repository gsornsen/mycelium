# Source: detection-integration.md
# Line: 509
# Valid syntax: True
# Has imports: True
# Has assignments: True

import time

from mycelium_onboarding.detection import detect_all


def wait_for_services(required_services, max_wait=60, check_interval=5):
    """Wait for required services to become available."""
    start_time = time.time()

    while time.time() - start_time < max_wait:
        summary = detect_all()

        # Check all required services
        all_available = True
        for service in required_services:
            if service == "docker" and not summary.has_docker or service == "redis" and not summary.has_redis or service == "postgres" and not summary.has_postgres or service == "temporal" and not summary.has_temporal:
                all_available = False

        if all_available:
            print(f"All required services available after {time.time() - start_time:.1f}s")
            return True

        print(f"Waiting for services... ({time.time() - start_time:.1f}s)")
        time.sleep(check_interval)

    print(f"Timeout: Services not available after {max_wait}s")
    return False

# Wait for services
required = ["docker", "redis", "postgres"]
if wait_for_services(required):
    print("Starting application...")
else:
    print("Cannot start: Required services unavailable")
    exit(1)
