# Source: telemetry-configuration.md
# Line: 260
# Valid syntax: True
# Has imports: True
# Has assignments: False

from plugins.mycelium_core.telemetry import TelemetryClient

with TelemetryClient() as client:
    client.track_agent_usage("agent-id", "operation")
    # Client automatically shuts down when exiting context