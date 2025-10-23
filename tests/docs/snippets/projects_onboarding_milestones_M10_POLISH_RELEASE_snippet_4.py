# Source: projects/onboarding/milestones/M10_POLISH_RELEASE.md
# Line: 1166
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium/telemetry.py
"""Optional telemetry for usage analytics (opt-in only)."""

import os
import platform
from pathlib import Path

import requests


class TelemetryClient:
    """Client for sending anonymous usage telemetry."""

    TELEMETRY_ENDPOINT = "https://telemetry.mycelium.dev/v1/events"

    def __init__(self):
        self.enabled = self._check_telemetry_enabled()
        self.session_id = self._generate_session_id()

    def _check_telemetry_enabled(self) -> bool:
        """Check if user has opted into telemetry."""
        # Check environment variable
        if os.getenv("MYCELIUM_TELEMETRY", "0") == "1":
            return True

        # Check config file
        config_file = Path.home() / ".config" / "mycelium" / "telemetry"
        return config_file.exists()

    def _generate_session_id(self) -> str:
        """Generate anonymous session ID."""
        import uuid
        return str(uuid.uuid4())

    def track_event(
        self,
        event_name: str,
        properties: dict | None = None
    ):
        """Track usage event (async, non-blocking)."""
        if not self.enabled:
            return

        event_data = {
            "event": event_name,
            "properties": properties or {},
            "session_id": self.session_id,
            "platform": platform.system(),
            "python_version": platform.python_version(),
        }

        # Send asynchronously, don't block on failure
        try:
            requests.post(
                self.TELEMETRY_ENDPOINT,
                json=event_data,
                timeout=1.0
            )
        except Exception:
            # Silently fail, never disrupt user experience
            pass


# Global telemetry client
telemetry = TelemetryClient()


# Example usage in code
def track_wizard_completion(deployment_method: str):
    """Track wizard completion event."""
    telemetry.track_event("wizard_completed", {
        "deployment_method": deployment_method
    })
