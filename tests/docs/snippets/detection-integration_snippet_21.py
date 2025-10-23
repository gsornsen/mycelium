# Source: detection-integration.md
# Line: 825
# Valid syntax: True
# Has imports: True
# Has assignments: True

# myapp/apps.py
from django.apps import AppConfig
from mycelium_onboarding.detection import detect_all

class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        """Check services on Django startup."""
        summary = detect_all()

        if not summary.has_redis:
            import warnings
            warnings.warn("Redis not available, some features will be disabled")

        # Store in Django cache
        from django.core.cache import cache
        cache.set("service_detection", {
            "docker": summary.has_docker,
            "redis": summary.has_redis,
            "postgres": summary.has_postgres,
        }, 60)