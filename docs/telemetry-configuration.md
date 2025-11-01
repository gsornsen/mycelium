# Telemetry Configuration Guide

## Overview

Mycelium includes an **opt-in telemetry system** designed with privacy-first principles. Telemetry helps improve the
platform by collecting anonymized usage and performance data.

**Important**: Telemetry is **DISABLED BY DEFAULT**. You must explicitly opt-in to enable it.

## Privacy Guarantees

### What We NEVER Collect

The telemetry system is designed to respect your privacy. We **NEVER** collect:

- ❌ User prompts or responses
- ❌ Code content or file contents
- ❌ Personally Identifiable Information (PII)
- ❌ File paths containing usernames
- ❌ API keys, tokens, or credentials
- ❌ Email addresses
- ❌ IP addresses
- ❌ Session contents

### What We DO Collect (Anonymized)

When enabled, we only collect anonymized, non-sensitive data:

- ✅ Agent usage counts (hashed agent IDs)
- ✅ Performance metrics (latency, success/failure rates)
- ✅ Error types (sanitized stack traces, no user data)
- ✅ System metadata (OS, Python version, Mycelium version)

All identifiers are hashed using SHA-256 with a unique salt before transmission, making them irreversible and
non-identifying.

## Configuration

### Quick Start

To enable telemetry, add the following to your `.env` file:

```bash
TELEMETRY_ENABLED=true
```

That's it! Telemetry will use default settings.

### Environment Variables

All telemetry configuration is done through environment variables:

| Variable                   | Default                                 | Description                                       |
| -------------------------- | --------------------------------------- | ------------------------------------------------- |
| `TELEMETRY_ENABLED`        | `false`                                 | Enable telemetry collection (true/false)          |
| `TELEMETRY_ENDPOINT`       | `https://mycelium-telemetry.sornsen.io` | Telemetry collection endpoint                     |
| `TELEMETRY_TIMEOUT`        | `5`                                     | Request timeout in seconds (1-30)                 |
| `TELEMETRY_BATCH_SIZE`     | `100`                                   | Number of events to batch before sending (1-1000) |
| `TELEMETRY_RETRY_ATTEMPTS` | `3`                                     | Number of retry attempts on failure (0-10)        |
| `TELEMETRY_RETRY_BACKOFF`  | `2.0`                                   | Exponential backoff multiplier (1.0-10.0)         |
| `TELEMETRY_SALT`           | Auto-generated                          | Salt for hashing identifiers (optional)           |

### Example Configurations

#### Minimal Configuration (Recommended)

```bash
# Enable with defaults
TELEMETRY_ENABLED=true
```

#### Custom Endpoint (Self-Hosting)

```bash
# Use your own telemetry endpoint
TELEMETRY_ENABLED=true
TELEMETRY_ENDPOINT=https://telemetry.mycompany.com
```

#### Performance Tuning

```bash
# Enable with custom settings
TELEMETRY_ENABLED=true
TELEMETRY_TIMEOUT=10
TELEMETRY_BATCH_SIZE=50
TELEMETRY_RETRY_ATTEMPTS=5
```

#### Disable Telemetry (Default)

```bash
# Explicitly disable (same as omitting the variable)
TELEMETRY_ENABLED=false
```

Or simply don't set `TELEMETRY_ENABLED` - it defaults to disabled.

## Self-Hosting

You can run your own telemetry collection endpoint instead of using the default.

### Requirements

Your endpoint must:

- Accept POST requests at the configured URL
- Handle JSON payloads with this structure:

```json
{
  "events": [
    {
      "event_type": "agent_usage",
      "agent_id_hash": "sha256_hash_here",
      "operation": "discover",
      "timestamp": 1234567890.123
    }
  ],
  "version": "1.0",
  "timestamp": 1234567890.123
}
```

### Example Configuration

```bash
TELEMETRY_ENABLED=true
TELEMETRY_ENDPOINT=https://your-telemetry-server.com/api/events
TELEMETRY_TIMEOUT=10
```

## Performance Impact

### When Disabled (Default)

**Zero overhead**. All telemetry functions become no-ops that return immediately.

- No background threads created
- No network connections initiated
- No memory allocated for telemetry
- Impact: \<1 microsecond per call

### When Enabled

Minimal overhead with non-blocking operation:

- Background thread handles all network I/O
- Events are queued and batched for efficiency
- Failed sends don't impact application performance
- Typical overhead: \<1ms per tracked event
- Memory usage: ~5MB for event queue

## Event Types

### Agent Usage Events

Tracks when agents are used and which operations they perform.

**Example event** (as sent to endpoint):

```json
{
  "event_type": "agent_usage",
  "agent_id_hash": "a3f2b1c9...",
  "operation": "discover",
  "timestamp": 1234567890.123,
  "metadata": {
    "duration_ms": 150,
    "success": true
  }
}
```

### Performance Metrics

Tracks system performance characteristics.

**Example event**:

```json
{
  "event_type": "performance",
  "metric_name": "discovery_latency",
  "value": 123.45,
  "unit": "ms",
  "timestamp": 1234567890.123,
  "tags": {
    "operation": "search"
  }
}
```

### Error Events

Tracks errors with anonymized details.

**Example event**:

```json
{
  "event_type": "error",
  "error_type": "ValueError",
  "error_message": "Invalid input in module.py",
  "timestamp": 1234567890.123,
  "stack_trace": "File \"myapp/module.py\", line 42..."
}
```

Note: File paths and any sensitive information are anonymized before sending.

### System Info Events

Tracks system metadata (sent once on startup).

**Example event**:

```json
{
  "event_type": "system_info",
  "platform": "Linux",
  "platform_version": "5.15.0",
  "python_version": "3.11.4",
  "python_implementation": "CPython",
  "timestamp": 1234567890.123
}
```

## Programmatic Usage

### Using the Telemetry Client

```python
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
```

### Context Manager Pattern

```python
from plugins.mycelium_core.telemetry import TelemetryClient

with TelemetryClient() as client:
    client.track_agent_usage("agent-id", "operation")
    # Client automatically shuts down when exiting context
```

### Custom Configuration

```python
from plugins.mycelium_core.telemetry import TelemetryClient, TelemetryConfig

# Custom configuration
config = TelemetryConfig(
    enabled=True,
    endpoint="https://my-endpoint.com",
    timeout=10,
    batch_size=50
)

client = TelemetryClient(config=config)
```

## Graceful Degradation

The telemetry system is designed to **never impact your application**, even when errors occur:

### Network Failures

If the telemetry endpoint is unreachable:

- Events are queued and retried with exponential backoff
- After max retries, events are discarded (logged but not saved)
- Application continues normally

### Configuration Errors

If configuration is invalid:

- Telemetry defaults to disabled
- Warning logged but application continues
- No exceptions raised

### Queue Overflow

If event queue fills up:

- New events are dropped (oldest first)
- Warning logged
- Application continues normally

## Security Considerations

### Data Transmission

- All communication uses HTTPS
- Connections timeout after configured duration (default: 5s)
- No credentials or authentication required (public endpoint)

### Endpoint Validation

- Only HTTPS endpoints are accepted by default
- HTTP allowed only for localhost development
- Invalid URLs cause telemetry to disable

### Salt Management

The anonymization salt is auto-generated and unique per installation. You can optionally provide your own:

```bash
# Generate a secure salt
TELEMETRY_SALT=$(openssl rand -hex 32)

# Add to .env
echo "TELEMETRY_SALT=$TELEMETRY_SALT" >> .env
```

**Important**: Keep your salt secret. If compromised, identifiers could potentially be correlated across sessions.

## Troubleshooting

### Telemetry Not Sending Events

1. **Verify telemetry is enabled**:

   ```bash
   echo $TELEMETRY_ENABLED  # Should print "true"
   ```

1. **Check logs** for telemetry errors:

   ```bash
   # Look for "telemetry" in logs
   grep -i telemetry logs/mycelium.log
   ```

1. **Test endpoint connectivity**:

   ```bash
   curl -X POST https://mycelium-telemetry.sornsen.io \
     -H "Content-Type: application/json" \
     -d '{"test": true}'
   ```

1. **Verify configuration**:

   ```python
   from plugins.mycelium_core.telemetry import TelemetryConfig

   config = TelemetryConfig.from_env()
   print(f"Enabled: {config.enabled}")
   print(f"Endpoint: {config.endpoint}")
   ```

### High Memory Usage

If telemetry is using excessive memory:

1. **Reduce batch size**:

   ```bash
   TELEMETRY_BATCH_SIZE=50  # Default is 100
   ```

1. **Check for endpoint issues**:

   - Events accumulate if endpoint is down
   - Verify endpoint is responding

1. **Monitor queue size** (programmatically):

   ```python
   client = TelemetryClient()
   print(f"Queue size: {client._event_queue.qsize()}")
   ```

### Events Not Batching

Events are sent when:

- Batch size is reached (default: 100 events), OR
- 30 seconds have passed since last send

For immediate sending, reduce batch size:

```bash
TELEMETRY_BATCH_SIZE=1  # Send immediately
```

## FAQ

### Why is telemetry disabled by default?

We respect user privacy and choice. Telemetry should always be opt-in, never opt-out.

### Can I review data before it's sent?

Yes! Enable debug logging to see all telemetry events:

```python
import logging
logging.getLogger("plugins.mycelium_core.telemetry").setLevel(logging.DEBUG)
```

### What happens to failed events?

Events that fail to send after retries are discarded and logged. They are never persisted to disk.

### Can I disable telemetry for specific agents?

Currently, telemetry is system-wide. You can only enable/disable for the entire Mycelium installation.

### How long are events retained?

Event retention is determined by your telemetry endpoint. The default Mycelium endpoint retains anonymized data for 90
days.

### Can I export my telemetry data?

Contact the endpoint administrator (for default endpoint: team@mycelium.dev) to request your anonymized data export.

## Support

For questions or issues:

- **Documentation**: [https://mycelium.dev/docs/telemetry](https://mycelium.dev/docs/telemetry)
- **GitHub Issues**: [https://github.com/mycelium/mycelium/issues](https://github.com/mycelium/mycelium/issues)
- **Email**: support@mycelium.dev

## Version History

- **1.0.0** (2025-10-21): Initial telemetry system release
  - Opt-in telemetry with privacy-first design
  - Agent usage, performance, and error tracking
  - Self-hosting support
