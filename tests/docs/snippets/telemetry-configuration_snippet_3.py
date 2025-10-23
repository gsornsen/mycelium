# Source: telemetry-configuration.md
# Line: 270
# Valid syntax: True
# Has imports: True
# Has assignments: True

from plugins.mycelium_core.telemetry import TelemetryClient, TelemetryConfig

# Custom configuration
config = TelemetryConfig(
    enabled=True,
    endpoint="https://my-endpoint.com",
    timeout=10,
    batch_size=50
)

client = TelemetryClient(config=config)