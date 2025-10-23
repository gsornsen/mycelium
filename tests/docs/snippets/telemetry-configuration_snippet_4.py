# Source: telemetry-configuration.md
# Line: 360
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: unexpected indent (<unknown>, line 1)

   from plugins.mycelium_core.telemetry import TelemetryConfig

   config = TelemetryConfig.from_env()
   print(f"Enabled: {config.enabled}")
   print(f"Endpoint: {config.endpoint}")