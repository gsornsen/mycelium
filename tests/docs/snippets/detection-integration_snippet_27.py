# Source: detection-integration.md
# Line: 1020
# Valid syntax: True
# Has imports: True
# Has assignments: True

import signal
import sys
from mycelium_onboarding.detection import detect_all

class Application:
    def __init__(self):
        self.running = True
        self.services = None

    def startup(self):
        """Application startup."""
        print("Detecting services...")
        summary = detect_all()
        self.services = summary

        # Register signal handlers
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, signum, frame):
        """Graceful shutdown."""
        print("Shutting down...")
        self.running = False
        sys.exit(0)

    def run(self):
        """Application main loop."""
        self.startup()
        while self.running:
            # Application logic
            time.sleep(1)

app = Application()
app.run()