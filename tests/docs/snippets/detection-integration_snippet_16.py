# Source: detection-integration.md
# Line: 615
# Valid syntax: True
# Has imports: True
# Has assignments: True

import threading
from mycelium_onboarding.detection import detect_all

class BackgroundDetector:
    """Run detection in background with periodic updates."""

    def __init__(self, interval=60):
        self.interval = interval
        self.summary = None
        self.running = False
        self.thread = None

    def start(self):
        """Start background detection."""
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop background detection."""
        self.running = False
        if self.thread:
            self.thread.join()

    def _run(self):
        """Background detection loop."""
        while self.running:
            self.summary = detect_all()
            time.sleep(self.interval)

    def get_summary(self):
        """Get latest detection summary."""
        if self.summary is None:
            self.summary = detect_all()
        return self.summary

# Usage
detector = BackgroundDetector(interval=30)
detector.start()

# Later...
summary = detector.get_summary()
print(f"Services: {summary.has_docker}, {summary.has_redis}")

# Cleanup
detector.stop()