# /health-check - Mycelium Performance Health Check

Display real-time performance analytics for mycelium agent discovery, cache, and token usage.

## Implementation

Read telemetry data from `~/.mycelium/analytics/events.jsonl` and display:

1. **Agent Discovery Performance** (last 7 days)
   - Total operations
   - p95 latency for list_agents, get_agent, search
   - Performance vs targets

2. **Cache Performance**
   - Cache hit rate
   - Hit vs miss latency comparison
   - Cache efficiency score

3. **Token Savings** (Phase 1 impact)
   - Total tokens loaded
   - Estimated savings vs baseline
   - Savings percentage

4. **System Health**
   - Storage usage
   - Event count
   - Latest event timestamp

## Usage

```bash
# Run the health check
uv run python scripts/health_check.py

# Or import and use programmatically
uv run python -c "from scripts.health_check import generate_health_report; print(generate_health_report())"
```

## Output Format

```
╔═══════════════════════════════════════════════════════════╗
║        🔍 Mycelium Performance Health Check               ║
║        Last 7 Days                                        ║
╚═══════════════════════════════════════════════════════════╝

📊 AGENT DISCOVERY PERFORMANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Operation       Count    p50      p95      p99      Target   Status
list_agents     1,245    0.08ms   0.12ms   0.18ms   <20ms    ✅
get_agent       3,891    0.03ms   1.16ms   2.45ms   <5ms     ✅
search          234      0.09ms   0.15ms   0.22ms   <10ms    ✅

Overall: 5,370 operations, p95 = 0.85ms ✅

⚡ CACHE PERFORMANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hit Rate:       87.2% ✅ (target: >80%)
Cache Hits:     3,392 operations (avg: 0.03ms)
Cache Misses:   499 operations (avg: 1.24ms)
Speedup:        41.3x faster on cache hits

💾 TOKEN SAVINGS (Phase 1 Impact)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Agents Loaded:       47 / 119 (39.5%)
Tokens Loaded:       21,150 tokens
Baseline (pre-P1):   53,550 tokens (all 119 agents @ 450 tokens)
Savings:             32,400 tokens (60.5% reduction) ✅

📈 PERFORMANCE TREND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Trend: IMPROVING ✅ (latency decreasing over time)

🗄️  STORAGE HEALTH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Event Files:    1 file
Total Events:   5,370 events
Storage Size:   805 KB
Latest Event:   2025-10-18 23:45:12 UTC (2 minutes ago)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All Systems Operational - Performance Excellent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Tips:
  • Cache hit rate is excellent (87%)
  • Phase 1 lazy loading saving 60% of tokens
  • All operations meeting performance targets

Run `uv run python -m mycelium_analytics report` for detailed analysis.
```

## Technical Details

The health check script:
- Reads events from `~/.mycelium/analytics/events.jsonl`
- Calculates percentiles (p50, p95, p99) for discovery operations
- Analyzes cache hit rates and latency differences
- Estimates token savings from lazy loading (Phase 1)
- Provides actionable performance insights

## Performance Targets

| Metric | Target | Status Indicator |
|--------|--------|------------------|
| list_agents p95 | < 20ms | ✅ Pass, ⚠️ Warn (>20ms), ❌ Fail (>30ms) |
| get_agent p95 | < 5ms | ✅ Pass, ⚠️ Warn (>5ms), ❌ Fail (>7.5ms) |
| search p95 | < 10ms | ✅ Pass, ⚠️ Warn (>10ms), ❌ Fail (>15ms) |
| Cache hit rate | > 80% | ✅ Pass, ⚠️ Warn (<80%), ❌ Fail (<60%) |
| Token savings | > 40% | ✅ Pass, ⚠️ Warn (<40%), ❌ Fail (<30%) |

## Dependencies

- `mycelium_analytics.EventStorage` - Read telemetry events
- `mycelium_analytics.MetricsAnalyzer` - Compute performance metrics
