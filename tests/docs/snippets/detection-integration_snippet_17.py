# Source: detection-integration.md
# Line: 670
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection import detect_all


def preflight_checks():
    """Run pre-flight service checks."""
    print("Running pre-flight checks...")

    summary = detect_all()

    # Define requirements
    requirements = {
        "docker": ("required", summary.has_docker),
        "redis": ("required", summary.has_redis),
        "postgres": ("required", summary.has_postgres),
        "temporal": ("optional", summary.has_temporal),
        "gpu": ("optional", summary.has_gpu),
    }

    # Check requirements
    failed_required = []
    missing_optional = []

    for service, (level, available) in requirements.items():
        if level == "required" and not available:
            failed_required.append(service)
        elif level == "optional" and not available:
            missing_optional.append(service)

    # Report
    if failed_required:
        print(f"❌ Missing required services: {', '.join(failed_required)}")
        return False

    if missing_optional:
        print(f"⚠️  Missing optional services: {', '.join(missing_optional)}")

    print(f"✓ Pre-flight checks passed in {summary.detection_time:.2f}s")
    return True

if __name__ == "__main__":
    if preflight_checks():
        # Start application
        print("Starting application...")
    else:
        print("Cannot start application")
        exit(1)
