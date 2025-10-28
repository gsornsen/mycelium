# Performance Analytics

**Module**: `mycelium_analytics` **Status**: Production Ready **Coverage**: 94.77% **Privacy**: Local-only, no PII

______________________________________________________________________

## Overview

Mycelium's Performance Analytics provides privacy-first telemetry for tracking agent discovery performance, cache
efficiency, and token consumption in production use. All data is stored locally and never transmitted.

**Key Features:**

- Real-time performance metrics
- Cache performance tracking
- Token savings measurement (Phase 1 impact)
- Performance trend analysis
- Privacy-first design (local-only storage)

______________________________________________________________________

## Quick Start

### Generate Performance Report

```bash
# Text format (human-readable)
uv run python -m mycelium_analytics report --days=7

# JSON format (machine-readable)
uv run python -m mycelium_analytics report --days=30 --format=json
```

### Health Check Dashboard

```bash
# Quick health check with ASCII dashboard
uv run python scripts/health_check.py

# Custom time period
uv run python scripts/health_check.py --days=30
```

### Programmatic Usage

```python
from mycelium_analytics import EventStorage, TelemetryCollector, MetricsAnalyzer

# Initialize components
storage = EventStorage()
telemetry = TelemetryCollector(storage)
analyzer = MetricsAnalyzer(storage)

# Record events
telemetry.record_agent_discovery("list_agents", duration_ms=0.08, agent_count=119)
telemetry.record_agent_load("01-core-api-designer", load_time_ms=1.2,
                            content_size_bytes=6424, estimated_tokens=1606)

# Analyze metrics
discovery_stats = analyzer.get_discovery_stats(days=7)
token_savings = analyzer.get_token_savings(days=7)
cache_performance = analyzer.get_cache_performance(days=7)
```

______________________________________________________________________

## Architecture

### Components

#### 1. EventStorage (`storage.py`)

Thread-safe JSONL storage backend with automatic log rotation.

**Storage Location**: `~/.mycelium/analytics/events.jsonl`

**Key Methods:**

- `append_event(event)`: Thread-safe event append
- `read_events(start_date, limit)`: Read events with filtering
- `get_storage_stats()`: File counts, event counts, data freshness

**Features:**

- Automatic rotation at 10MB threshold
- Thread-safe with `threading.Lock()`
- Graceful error handling
- No external dependencies

#### 2. TelemetryCollector (`telemetry.py`)

Lightweight event collection with privacy guarantees.

**Key Methods:**

- `record_agent_discovery(operation, duration_ms, cache_hit, agent_count)`
- `record_agent_load(agent_id, load_time_ms, content_size_bytes, estimated_tokens)`
- `record_session_start(session_type, initial_tokens)`
- `record_session_end(session_type, duration_seconds, operations_count)`

**Privacy Guarantees:**

- Agent IDs hashed (SHA256, 8-char prefix)
- No file paths (beyond project root)
- No command content
- No PII (usernames, emails)
- UTC timestamps only

**Opt-out**: Set `MYCELIUM_TELEMETRY=0` to disable.

#### 3. MetricsAnalyzer (`metrics.py`)

Statistical analysis engine for computing performance metrics.

**Key Methods:**

- `get_discovery_stats(days)`: p50/p95/p99 latencies, cache hit rate
- `get_token_savings(days)`: Phase 1 lazy loading impact
- `get_cache_performance(days)`: Hit rate, latency comparison
- `get_performance_trends(days)`: Daily stats, trend detection
- `get_summary_report(days)`: Complete analytics dashboard

**Statistical Methods:**

- Percentile calculation (linear interpolation)
- Trend detection (improving/stable/degrading)
- Daily grouping with time-series analysis

______________________________________________________________________

## Event Schema

### agent_discovery Event

```json
{
  "timestamp": "2025-10-19T00:05:42.011733+00:00",
  "event_type": "agent_discovery",
  "operation": "list_agents",
  "duration_ms": 0.08,
  "cache_hit": false,
  "agent_count": 119
}
```

**Fields:**

- `timestamp`: ISO 8601 UTC timestamp
- `event_type`: Always "agent_discovery"
- `operation`: "list_agents" | "get_agent" | "search"
- `duration_ms`: Operation latency in milliseconds
- `cache_hit`: Boolean (only for get_agent)
- `agent_count`: Number of agents in result

### agent_load Event

```json
{
  "timestamp": "2025-10-19T00:05:42.012169+00:00",
  "event_type": "agent_load",
  "agent_id_hash": "f2f2cbc2",
  "load_time_ms": 1.16,
  "content_size_bytes": 6424,
  "estimated_tokens": 1606
}
```

**Fields:**

- `timestamp`: ISO 8601 UTC timestamp
- `event_type`: Always "agent_load"
- `agent_id_hash`: SHA256 hash (8-char prefix) for privacy
- `load_time_ms`: Time to load markdown file
- `content_size_bytes`: File size in bytes
- `estimated_tokens`: Rough token estimate (~4 chars/token)

______________________________________________________________________

## Metrics Reference

### Discovery Performance

**Metrics:**

- **Total Operations**: Count of all discovery operations
- **By Operation**: Stats grouped by operation type (list_agents, get_agent, search)
- **Percentiles**: p50, p95, p99 latencies in milliseconds
- **Cache Hit Rate**: Percentage of get_agent operations served from cache

**Performance Targets:**

- `list_agents`: p95 \< 20ms
- `get_agent`: p95 \< 5ms
- `search`: p95 \< 10ms

**Example Output:**

```json
{
  "total_operations": 5370,
  "by_operation": {
    "list_agents": {
      "count": 1245,
      "p50_ms": 0.08,
      "p95_ms": 0.12,
      "p99_ms": 0.18,
      "avg_ms": 0.09
    },
    "get_agent": {
      "count": 3891,
      "p50_ms": 0.03,
      "p95_ms": 1.16,
      "p99_ms": 2.45,
      "avg_ms": 0.45,
      "cache_hit_rate": 87.2
    }
  }
}
```

### Token Savings

**Metrics:**

- **Total Agents Loaded**: Actual number loaded (vs 119 total)
- **Total Tokens Loaded**: Actual token consumption
- **Baseline Tokens**: Pre-Phase 1 estimate (119 × 450 = 53,550)
- **Estimated Savings**: Baseline - Actual
- **Savings Percentage**: (Savings / Baseline) × 100

**Phase 1 Impact:**

- Lazy loading only loads agents on-demand
- Typical usage: 10-30 agents loaded per session
- Expected savings: 60-90% token reduction

**Example Output:**

```json
{
  "total_agents_loaded": 47,
  "total_tokens_loaded": 21150,
  "avg_tokens_per_agent": 450.0,
  "estimated_baseline_tokens": 53550,
  "estimated_savings_tokens": 32400,
  "savings_percentage": 60.5
}
```

### Cache Performance

**Metrics:**

- **Hit Rate**: Percentage of cache hits (target: >80%)
- **Hit Latency**: Average latency for cache hits
- **Miss Latency**: Average latency for cache misses
- **Speedup**: Miss latency / Hit latency ratio

**LRU Cache Configuration:**

- Max size: 50 agents
- Eviction policy: Least Recently Used (LRU)
- Thread-safe: OrderedDict with move_to_end()

**Example Output:**

```json
{
  "total_lookups": 3891,
  "cache_hits": 3392,
  "cache_misses": 499,
  "hit_rate_percentage": 87.2,
  "avg_hit_latency_ms": 0.03,
  "avg_miss_latency_ms": 1.24,
  "speedup": 41.3
}
```

### Performance Trends

**Metrics:**

- **Daily Stats**: Operations, avg latency, cache hit rate per day
- **Trend**: "improving" | "stable" | "degrading"

**Trend Detection Logic:**

- Compare first half vs second half of time period
- Improving: Second half avg \< First half avg × 0.9 (>10% improvement)
- Degrading: Second half avg > First half avg × 1.1 (>10% degradation)
- Stable: Otherwise

**Example Output:**

```json
{
  "daily_stats": [
    {
      "date": "2025-10-18",
      "operations": 1234,
      "avg_latency_ms": 0.45,
      "cache_hit_rate": 85.2
    }
  ],
  "trend": "improving"
}
```

______________________________________________________________________

## Integration Points

### Agent Discovery Integration

Telemetry hooks are integrated into `scripts/agent_discovery.py`:

**Instrumented Operations:**

1. `list_agents()`: Records operation time and agent count
1. `get_agent()`: Records cache hits/misses and load time
1. `search()`: Records search latency and result count

**Agent Load Tracking:**

- Content size (bytes)
- Load time (ms)
- Estimated tokens (~4 chars/token)
- Agent ID (hashed for privacy)

**Code Example:**

```python
# In scripts/agent_discovery.py
def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
    start_time = time.perf_counter()

    # ... existing implementation ...

    # Record telemetry
    duration_ms = (time.perf_counter() - start_time) * 1000
    if self.telemetry:
        self.telemetry.record_agent_discovery(
            operation='get_agent',
            duration_ms=duration_ms,
            cache_hit=cache_hit,
            agent_count=1 if agent_full else 0
        )
```

______________________________________________________________________

## CLI Tools

### Analytics Report

**Command**: `uv run python -m mycelium_analytics report`

**Options:**

- `--days N`: Number of days to analyze (default: 7)
- `--format {text,json}`: Output format (default: text)

**Text Format Output:**

```
=== Mycelium Performance Analytics (7 days) ===

📊 Agent Discovery Performance:
  Total operations: 5370
  Overall p95: 0.85ms
  Overall avg: 0.42ms

💾 Token Consumption:
  Agents loaded: 47
  Tokens loaded: 21,150
  Estimated savings: 32,400 tokens (60.5%)

⚡ Cache Performance:
  Hit rate: 87.2%
  Avg hit latency: 0.03ms
  Avg miss latency: 1.24ms

📈 Performance Trend: improving
```

**JSON Format Output:**

```json
{
  "report_period_days": 7,
  "generated_at": "2025-10-19T12:00:00+00:00",
  "discovery_stats": { ... },
  "token_savings": { ... },
  "cache_performance": { ... },
  "trends": { ... }
}
```

### Health Check

**Command**: `uv run python scripts/health_check.py`

**Options:**

- `--days N`: Number of days to analyze (default: 7)

**Features:**

- Beautiful ASCII dashboard with box-drawing characters
- Status icons (✅/⚠️/❌)
- Performance vs targets comparison
- Actionable tips based on metrics
- Storage health monitoring

______________________________________________________________________

## Privacy & Security

### Privacy Guarantees

✅ **Local-only storage** (`~/.mycelium/analytics/`) ✅ **No PII collection** (no usernames, emails, paths) ✅ **Agent ID
hashing** (SHA256, 8-char prefix) ✅ **UTC timestamps only** (no timezone PII) ✅ **Performance metrics only** (durations,
counts, booleans) ✅ **Opt-out support** (`MYCELIUM_TELEMETRY=0`) ✅ **Graceful degradation** (failures don't break
operations)

### Data Retention

- **Storage Location**: `~/.mycelium/analytics/`
- **Rotation Policy**: 10MB per file → automatic rotation
- **Retention Policy**: No automatic deletion (user-managed)
- **Manual Cleanup**: Delete `~/.mycelium/analytics/` directory

### Opt-out

Disable telemetry completely:

```bash
export MYCELIUM_TELEMETRY=0
```

Telemetry will gracefully degrade:

- No events recorded
- No storage writes
- No performance impact
- Agent discovery continues normally

______________________________________________________________________

## Testing

### Unit Tests

**Coverage**: 94.77% (63 tests)

**Test Suites:**

1. `test_storage.py`: JSONL append, rotation, thread safety (26 tests)
1. `test_telemetry.py`: Event collection, privacy, degradation (10 tests)
1. `test_metrics.py`: Statistical analysis, percentiles, trends (27 tests)

**Run Tests:**

```bash
# All analytics tests
uv run pytest tests/unit/analytics/ -v

# With coverage
uv run pytest tests/unit/analytics/ --cov=mycelium_analytics --cov-report=term-missing
```

### Integration Testing

**Verify telemetry collection:**

```bash
# Run benchmark (generates telemetry events)
uv run python scripts/agent_discovery.py --benchmark

# Check events were recorded
ls -lh ~/.mycelium/analytics/events.jsonl

# View events
cat ~/.mycelium/analytics/events.jsonl | head -5 | jq
```

______________________________________________________________________

## Performance Impact

### Overhead Measurement

**Telemetry Overhead**: \<0.1ms per operation

**Benchmark Results** (with telemetry enabled):

- `list_agents`: 0.08ms (vs 0.08ms without telemetry) - 0% overhead
- `get_agent` (cached): 0.03ms (vs 0.03ms) - 0% overhead
- `get_agent` (miss): 1.16ms (vs 1.15ms) - \<1% overhead

**Memory Impact**: Minimal (immediate disk flush)

**Storage Growth**: ~150 bytes per event

______________________________________________________________________

## Troubleshooting

### No telemetry data

**Symptom**: `uv run python -m mycelium_analytics report` shows "No discovery data available"

**Solutions:**

1. Check `MYCELIUM_TELEMETRY` environment variable (should not be `0`)
1. Verify storage directory exists: `ls -la ~/.mycelium/analytics/`
1. Run benchmark to generate events: `uv run python scripts/agent_discovery.py --benchmark`
1. Check file permissions on `~/.mycelium/analytics/`

### Permission denied errors

**Symptom**: `PermissionError: [Errno 13] Permission denied: '/home/user/.mycelium/analytics/events.jsonl'`

**Solutions:**

1. Check directory permissions: `ls -ld ~/.mycelium/analytics/`
1. Fix permissions: `chmod 755 ~/.mycelium/analytics/`
1. Check file ownership: `ls -l ~/.mycelium/analytics/events.jsonl`

### Storage files too large

**Symptom**: Multiple `events-*.jsonl` files consuming significant disk space

**Solutions:**

1. Check storage stats:
   `uv run python -c "from mycelium_analytics import EventStorage; print(EventStorage().get_storage_stats())"`
1. Delete old events: `rm ~/.mycelium/analytics/events-*.jsonl` (keep `events.jsonl`)
1. Clear all events: `rm -rf ~/.mycelium/analytics/`

______________________________________________________________________

## Future Enhancements

### Phase 2 Roadmap (Post-Initial Release)

1. **Web Dashboard** (optional)

   - Real-time metrics visualization
   - Interactive charts (Chart.js)
   - Historical trend graphs

1. **Alerting** (optional)

   - Performance degradation alerts
   - Cache hit rate thresholds
   - Email/Slack notifications

1. **Export Formats** (optional)

   - CSV export for Excel analysis
   - Prometheus metrics endpoint
   - Grafana dashboard templates

1. **Advanced Analytics** (optional)

   - Agent usage heatmaps
   - Session clustering
   - Predictive performance modeling

______________________________________________________________________

## References

### Source Code

- `mycelium_analytics/storage.py` - JSONL storage backend
- `mycelium_analytics/telemetry.py` - Event collection
- `mycelium_analytics/metrics.py` - Statistical analysis
- `mycelium_analytics/__main__.py` - CLI report tool
- `scripts/health_check.py` - Health dashboard
- `scripts/agent_discovery.py` - Integration hooks

### Documentation

- `.mycelium/modules/analytics.md` - This document
- `.claude/commands/health-check.md` - Slash command reference
- `tests/unit/analytics/` - Test suite documentation

### Related Modules

- [Agent Discovery](./agents.md) - Agent metadata and lazy loading
- [Coordination](./coordination.md) - Multi-agent orchestration
- [Deployment](./deployment.md) - Production deployment guide

______________________________________________________________________

**Last Updated**: 2025-10-19 **Authors**: @python-pro, @cli-developer, @documentation-engineer **Phase**: Phase 2 -
Performance Analytics
