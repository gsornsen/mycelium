# Source: detection-integration.md
# Line: 793
# Valid syntax: True
# Has imports: True
# Has assignments: True

from flask import Flask, jsonify
from mycelium_onboarding.detection import detect_all

app = Flask(__name__)

@app.route("/health")
def health():
    """Health check endpoint."""
    summary = detect_all()
    return jsonify({
        "status": "healthy",
        "services": {
            "docker": summary.has_docker,
            "redis": summary.has_redis,
            "postgres": summary.has_postgres,
        }
    })

@app.before_first_request
def check_services():
    """Check services before handling first request."""
    summary = detect_all()
    if not summary.has_redis:
        app.logger.warning("Redis not available")

if __name__ == "__main__":
    app.run()