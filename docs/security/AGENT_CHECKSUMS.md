# Agent Integrity Verification with Checksums

This document describes the agent checksum system for detecting tampering and ensuring integrity of agent definition
files.

## Overview

The checksum system generates SHA-256 checksums for all agent `.md` files and stores them in a JSON file. These
checksums can be used to verify that agent files haven't been modified, corrupted, or tampered with.

## Features

- **SHA-256 checksums**: Cryptographically secure hash function
- **Batch generation**: Generate checksums for all agents at once
- **Integrity verification**: Detect modified, missing, or new agents
- **CLI integration**: Easy-to-use commands for managing checksums
- **MCP integration**: Built-in verification at MCP server startup

## Quick Start

### Generate Checksums

```bash
# Generate checksums for all agents (default plugin directory)
mycelium agent checksum generate

# Generate with custom paths
mycelium agent checksum generate --plugin-dir /path/to/agents --output /custom/checksums.json
```

This creates a checksums file at `~/.mycelium/agent_checksums.json`:

```json
{
  "generated_at": "2025-11-30T14:00:00Z",
  "agents": {
    "backend-developer": "sha256:abc123...",
    "frontend-developer": "sha256:def456..."
  }
}
```

### Verify Checksums

```bash
# Verify all agents against stored checksums
mycelium agent checksum verify

# Verify with custom paths
mycelium agent checksum verify --plugin-dir /path/to/agents --checksums /custom/checksums.json
```

**Success output:**

```
✓ All agent checksums verified successfully
  ✓ No integrity issues detected
```

**Failure output:**

```
⚠ Agent integrity check failed for 2 agent(s)

Failed agents:
  ✗ backend-developer
  ✗ frontend-developer

Possible causes:
  • Agent file modified
  • Agent file missing
  • New agent not in checksums
```

### Show Checksums

```bash
# Show checksums in human-readable format
mycelium agent checksum show

# Show checksums as JSON
mycelium agent checksum show --json
```

## API Usage

### Generate Checksums Programmatically

```python
from pathlib import Path
from mycelium.mcp.checksums import generate_all_checksums, save_checksums

# Generate checksums
plugin_dir = Path("/path/to/agents")
checksums = generate_all_checksums(plugin_dir)

# Save to file
output_path = Path.home() / ".mycelium" / "agent_checksums.json"
save_checksums(checksums, output_path)

print(f"Generated {len(checksums)} checksums")
```

### Verify Integrity

```python
from pathlib import Path
from mycelium.mcp.checksums import verify_all_checksums

plugin_dir = Path("/path/to/agents")
checksums_path = Path.home() / ".mycelium" / "agent_checksums.json"

# Verify all agents
failed = verify_all_checksums(plugin_dir, checksums_path)

if not failed:
    print("All agents verified successfully")
else:
    print(f"Failed agents: {failed}")
```

### Single Agent Verification

```python
from pathlib import Path
from mycelium.mcp.checksums import generate_agent_checksum, verify_agent_checksum

agent_file = Path("/path/to/agents/backend-developer.md")

# Generate checksum
checksum = generate_agent_checksum(agent_file)
print(f"Checksum: {checksum}")

# Verify against expected checksum
expected = "sha256:abc123..."
is_valid = verify_agent_checksum("backend-developer", agent_file, expected)
print(f"Valid: {is_valid}")
```

## MCP Server Integration

The MCP server can use checksums to verify agent integrity at startup:

```python
from pathlib import Path
from mycelium.mcp.checksums import verify_all_checksums

def mcp_server_startup():
    plugin_dir = Path("/path/to/agents")
    checksums_path = Path.home() / ".mycelium" / "agent_checksums.json"

    # Verify agents at startup
    failed = verify_all_checksums(plugin_dir, checksums_path)

    if failed:
        logger.warning(f"Agent integrity check failed: {failed}")
        # Log warning but continue serving
    else:
        logger.info("All agents verified successfully")
```

See `examples/checksum_integration.py` for a complete example.

## Security Considerations

### What Checksums Detect

✓ **Modified agent files**: Any change to file content is detected ✓ **Corrupted files**: File corruption changes the
checksum ✓ **Missing files**: Agent files that were deleted ✓ **New files**: Agents added after checksum generation

### What Checksums Don't Prevent

✗ **Concurrent modifications**: If an attacker can modify both the agent file and checksums file ✗ **Time-of-check to
time-of-use**: File could be modified between verification and use ✗ **Authorized changes**: Legitimate updates require
regenerating checksums

### Best Practices

1. **Store checksums securely**: Keep `agent_checksums.json` in a protected location
1. **Verify regularly**: Run `mycelium agent checksum verify` periodically
1. **Update after changes**: Regenerate checksums after intentional agent updates
1. **Integrate with CI/CD**: Verify checksums in deployment pipelines
1. **Monitor failures**: Alert on checksum verification failures
1. **Use version control**: Track both agents and checksums in git

### Advanced Security

For production environments, consider:

- **Digital signatures**: Sign the checksums file with a private key
- **Immutable storage**: Store checksums in write-once storage
- **Audit logging**: Log all checksum verifications and failures
- **Automated alerts**: Notify security team on integrity failures

## File Format

The checksums file uses JSON format:

```json
{
  "generated_at": "2025-11-30T14:00:00+00:00",
  "agents": {
    "agent-name": "sha256:hexdigest",
    ...
  }
}
```

### Fields

- `generated_at`: ISO 8601 timestamp of checksum generation (UTC)
- `agents`: Dictionary mapping agent names to SHA-256 checksums
  - **Key**: Agent name (extracted from filename)
  - **Value**: Checksum in format `sha256:hexdigest`

### Agent Name Extraction

Agent names are extracted from filenames:

| Filename                          | Extracted Name      |
| --------------------------------- | ------------------- |
| `01-core-backend-developer.md`    | `backend-developer` |
| `02-language-python-pro.md`       | `python-pro`        |
| `03-specialized-data-engineer.md` | `data-engineer`     |

The extraction removes:

1. Number prefix (e.g., `01-`)
1. Category prefix (e.g., `core-`, `language-`, `specialized-`)
1. `.md` extension

## Troubleshooting

### Error: Checksums file not found

**Cause**: No checksums file exists

**Solution**: Generate checksums first

```bash
mycelium agent checksum generate
```

### Error: Plugin directory not found

**Cause**: Plugin directory doesn't exist or wrong path

**Solution**: Specify correct path or check default location

```bash
mycelium agent checksum generate --plugin-dir /correct/path
```

### Warning: Checksum mismatch

**Cause**: Agent file was modified after checksum generation

**Solution**: If modification was intentional, regenerate checksums

```bash
mycelium agent checksum generate
```

### Warning: Agent file missing

**Cause**: Agent file was deleted

**Solution**:

- Restore the file from backup, or
- Regenerate checksums if deletion was intentional

### Warning: New agent detected

**Cause**: Agent file added after checksum generation

**Solution**: Regenerate checksums to include new agent

```bash
mycelium agent checksum generate
```

## Testing

Run the checksum tests:

```bash
# Run all checksum tests
uv run pytest tests/unit/mcp/test_checksums.py -v

# Run specific test class
uv run pytest tests/unit/mcp/test_checksums.py::TestGenerateAgentChecksum -v

# Run with coverage
uv run pytest tests/unit/mcp/test_checksums.py --cov=mycelium.mcp.checksums
```

## Implementation Details

### Algorithm

1. **File Reading**: Files are read in 4096-byte chunks for memory efficiency
1. **Hashing**: SHA-256 hash is computed incrementally
1. **Format**: Checksums are prefixed with `sha256:` for clarity
1. **Timestamp**: Generation time is recorded in UTC ISO 8601 format

### Performance

- **Generation**: ~0.1ms per agent file
- **Verification**: ~0.2ms per agent file
- **Typical operation**: 100 agents verified in \< 50ms

### Error Handling

All functions handle errors gracefully:

- `FileNotFoundError`: File or directory doesn't exist
- `ValueError`: Invalid file format or structure
- `IOError`: File read/write failures

## Related Documentation

- [Security Overview](./SECURITY_REVIEW_EXECUTIVE_SUMMARY.md)
- [MCP Server Discovery](../research/MYCELIUM_MCP_SERVER_SPEC.md)
- [CLI Commands Reference](../COMMANDS_AND_HOOKS_REFERENCE.md)

## Future Enhancements

Potential improvements:

1. **Digital signatures**: GPG signing of checksums file
1. **Merkle trees**: Efficient verification of large agent sets
1. **Incremental updates**: Update checksums for changed files only
1. **Remote verification**: Verify against published checksums
1. **Automated monitoring**: Continuous integrity checking
1. **Integration with CI/CD**: Pre-commit hooks for verification
