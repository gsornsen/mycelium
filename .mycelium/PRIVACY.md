# Privacy Policy - Mycelium Performance Analytics

**Last Updated**: 2025-10-19 **Effective Date**: 2025-10-19

______________________________________________________________________

## Overview

Mycelium's Performance Analytics system collects local telemetry data to help you understand and optimize the
performance of your agent discovery system. **All data is stored locally on your machine and never transmitted to
external servers.**

______________________________________________________________________

## Data Collection

### What We Collect

**Performance Metrics Only:**

- Agent discovery operation latencies (milliseconds)
- Cache hit/miss statistics
- Agent load times and content sizes
- Session start/end timestamps

**Privacy-Safe Identifiers:**

- Agent IDs (SHA256 hashed, 8-character prefix)
- Operation types (list_agents, get_agent, search)
- UTC timestamps

### What We DO NOT Collect

❌ **No Personal Information:**

- No usernames or email addresses
- No IP addresses or network information
- No system information (OS version, hardware)

❌ **No Content:**

- No file paths (beyond project root)
- No command content or arguments
- No agent markdown content

❌ **No Tracking:**

- No cookies or tracking pixels
- No external API calls
- No third-party analytics services

______________________________________________________________________

## Data Storage

**Location**: `~/.mycelium/analytics/`

**Format**: JSONL (newline-delimited JSON)

**Retention**: User-managed (no automatic deletion)

**Security**:

- Local filesystem permissions
- No encryption (data is non-sensitive)
- No network transmission

______________________________________________________________________

## Data Usage

### How We Use Data

**Performance Optimization:**

- Identify slow operations
- Optimize cache strategies
- Measure Phase 1 impact

**Diagnostics:**

- Troubleshoot performance issues
- Validate performance targets
- Track system health

### How We DO NOT Use Data

❌ **No External Sharing:**

- Data never leaves your machine
- No telemetry servers
- No analytics platforms

❌ **No Profiling:**

- No user behavior tracking
- No usage pattern analysis
- No predictive modeling

______________________________________________________________________

## Your Rights

### Opt-out

Disable telemetry completely:

```bash
export MYCELIUM_TELEMETRY=0
```

**Effect**: No events recorded, no storage writes, no performance impact.

### Data Deletion

Delete all telemetry data:

```bash
rm -rf ~/.mycelium/analytics/
```

**Effect**: All historical data permanently deleted.

### Data Access

View your data:

```bash
# View raw events
cat ~/.mycelium/analytics/events.jsonl

# View analytics report
uv run python -m mycelium_analytics report --format=json
```

______________________________________________________________________

## Technical Implementation

### Privacy-Preserving Design

**Agent ID Hashing:**

```python
agent_id_hash = hashlib.sha256(agent_id.encode()).hexdigest()[:8]
# "01-core-api-designer" → "f2f2cbc2"
```

**Graceful Degradation:**

- Telemetry failures never break agent discovery
- Silent error handling
- No exceptions propagated

**Thread Safety:**

- Concurrent event recording
- Lock-based synchronization
- No race conditions

______________________________________________________________________

## Changes to This Policy

We will notify users of any changes to this privacy policy by:

1. Updating the "Last Updated" date
1. Adding a changelog section
1. Requiring explicit opt-in for new data collection

**Current Version**: 1.0.0 **Changelog**: None (initial version)

______________________________________________________________________

## Contact

For privacy questions or concerns:

- Open an issue: [GitHub Issues](https://github.com/gsornsen/mycelium/issues)
- Email: privacy@mycelium.dev

______________________________________________________________________

**This policy applies only to Mycelium Performance Analytics. It does not cover third-party tools or services you may
use with Mycelium.**
