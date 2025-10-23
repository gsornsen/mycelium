# Source: telemetry-configuration.md
# Line: 226
# Valid syntax: True
# Has imports: True
# Has assignments: True

from plugins.mycelium_core.telemetry import TelemetryClient

# Client automatically loads configuration from environment
client = TelemetryClient()

# Track agent usage
client.track_agent_usage(
    agent_id="backend-developer",
    operation="discover",
    metadata={"duration_ms": 150, "success": True}
)

# Track performance metrics
client.track_performance(
    metric_name="query_latency",
    value=95.5,
    unit="ms",
    tags={"operation": "search"}
)

# Track errors
client.track_error(
    error_type="ConnectionError",
    error_message="Failed to connect",
    stack_trace=traceback.format_exc()
)

# Graceful shutdown
client.shutdown()