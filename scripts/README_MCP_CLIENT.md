# Mycelium MCP Test Client

Interactive testing tool for the Mycelium MCP (Model Context Protocol) server. This client provides a user-friendly
interface for manual QA, debugging, and validation during development.

## Features

- **Interactive REPL Mode**: Menu-driven interface with command history
- **Direct Command Mode**: Scriptable CLI commands for automation
- **Pretty Output**: Rich-formatted JSON, tables, and panels
- **Command Shortcuts**: Quick access with single-letter commands
- **Workflow Tracking**: Automatic tracking of last workflow ID
- **Verbose Mode**: View raw JSON-RPC messages for debugging
- **Error Handling**: Graceful error messages and recovery

## Installation

The MCP client uses dependencies already in the project:

```bash
# No additional installation needed
# Uses: rich, subprocess, json (all available)
```

## Usage

### Interactive Mode (Recommended)

Launch the interactive REPL for exploratory testing:

```bash
uv run python scripts/mcp_client.py
```

This opens an interactive session where you can:

- Search for agents
- View agent details
- List categories
- Invoke agents on tasks
- Check workflow status
- Use command shortcuts (d, i, s, c, etc.)

**Interactive Session Example:**

```
🍄 Mycelium MCP Test Client
===========================

Commands:
  discover <query>     - Search for agents
  details <name>       - Get agent details
  categories           - List categories
  invoke <name> <task> - Invoke agent
  status [workflow_id] - Check workflow status
  last                 - Show last workflow_id
  help                 - Show this help
  quit                 - Exit

Shortcuts:
  d = discover, i = invoke, s = status, c = categories

> discover Python
Found 5 agents:
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name              ┃ Category ┃ Description                  ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ python-pro        │ language │ Expert Python developer...   │
│ django-developer  │ language │ Django specialist...         │
└───────────────────┴──────────┴──────────────────────────────┘

> details python-pro
╭─────── Agent: python-pro ───────╮
│ Name: python-pro                │
│ Category: language              │
│                                 │
│ Description:                    │
│ Expert Python developer with... │
│                                 │
│ Tools:                          │
│ Read(*), Write(*), Bash(*)      │
│                                 │
│ Command:                        │
│ claude --agent python-pro       │
╰─────────────────────────────────╯

> invoke python-pro "Write hello world"
⚠️  HIGH RISK AGENT - Consent required

╭─────── Workflow Started ───────╮
│ Workflow ID: wf_abc123def456   │
│ Agent: python-pro              │
│ Status: started                │
│ PID: 12345                     │
│ Risk Level: high               │
│                                │
│ Agent started successfully     │
╰────────────────────────────────╯

> status
Using last workflow: wf_abc123def456

╭────── Workflow Status ─────────╮
│ Workflow ID: wf_abc123def456   │
│ Status: running                │
│ Agent: python-pro              │
│ Task: Write hello world        │
│ Started: 2025-11-30T10:30:00Z  │
╰────────────────────────────────╯

> quit
Goodbye!
```

### Direct Command Mode

For scripting and automation, use direct commands:

```bash
# Search for agents
uv run python scripts/mcp_client.py discover "Python backend"

# Get agent details
uv run python scripts/mcp_client.py details backend-developer

# List all categories
uv run python scripts/mcp_client.py categories

# Invoke an agent
uv run python scripts/mcp_client.py invoke python-pro "Build a CLI tool"

# Check workflow status
uv run python scripts/mcp_client.py status wf_abc123def456
```

Direct mode outputs JSON for easy parsing:

```bash
# Parse with jq
uv run python scripts/mcp_client.py discover "React" | jq '.[] | .name'

# Save to file
uv run python scripts/mcp_client.py categories > categories.json
```

### Verbose Mode

Enable verbose logging to see raw JSON-RPC messages:

```bash
# Interactive mode with verbose logging
uv run python scripts/mcp_client.py --verbose

# Direct command with verbose logging
uv run python scripts/mcp_client.py --verbose discover "Python"
```

Verbose mode shows:

- JSON-RPC request messages
- JSON-RPC response messages
- Full error tracebacks

## Available Commands

### discover

Search for agents using natural language queries.

**Interactive:**

```
> discover Python backend
> d web development
```

**Direct:**

```bash
uv run python scripts/mcp_client.py discover "Python backend"
```

**Search Tips:**

- Use keywords from agent names, descriptions, or tools
- Search by category: "language", "core", "data"
- Search by capability: "Python", "React", "database", "API"

### details

Get full metadata for a specific agent including tools, command, and description.

**Interactive:**

```
> details backend-developer
```

**Direct:**

```bash
uv run python scripts/mcp_client.py details backend-developer
```

### categories

List all available agent categories with agent counts.

**Interactive:**

```
> categories
> c
```

**Direct:**

```bash
uv run python scripts/mcp_client.py categories
```

### invoke

Invoke an agent to execute a task. For high-risk agents (with Bash/Write permissions), user consent will be requested.

**Interactive:**

```
> invoke python-pro "Write a hello world script"
> i frontend-developer "Build a React component"
```

**Direct:**

```bash
uv run python scripts/mcp_client.py invoke python-pro "Implement user auth"
```

**Returns:**

- `workflow_id`: Unique identifier for tracking
- `status`: "started" or "failed"
- `agent_name`: Name of invoked agent
- `pid`: Process ID (if started)
- `risk_level`: "low", "medium", or "high"
- `message`: Status message

### status

Check the status of a running workflow.

**Interactive:**

```
> status wf_abc123def456
> s                      # Uses last workflow_id
```

**Direct:**

```bash
uv run python scripts/mcp_client.py status wf_abc123def456
```

**Returns:**

- `workflow_id`: Workflow identifier
- `status`: "running", "completed", "failed", or "not_found"
- `agent_name`: Agent name
- `task`: Task description
- `started_at`: ISO timestamp
- `completed_at`: ISO timestamp (if finished)
- `error`: Error message (if failed)
- `exit_code`: Process exit code (if finished)

### last

Show the last workflow ID (interactive mode only).

**Interactive:**

```
> last
Last workflow ID: wf_abc123def456
```

This is useful for quickly checking status after invoking an agent:

```
> invoke python-pro "Build feature"
> last
> status
```

## Command Shortcuts

Interactive mode supports single-letter shortcuts:

| Shortcut | Command | | -------- | ---------- | | `d` | discover | | `i` | invoke | | `s` | status | | `c` | categories
| | `h` | help | | `q` | quit |

## Architecture

### Communication Flow

```
┌──────────────┐         JSON-RPC          ┌──────────────┐
│              │◄────────────────────────►│              │
│  MCP Client  │     (stdio transport)    │  MCP Server  │
│              │                          │              │
└──────────────┘                          └──────────────┘
       │                                         │
       │                                         │
       ▼                                         ▼
┌──────────────┐                          ┌──────────────┐
│ Rich Console │                          │ Agent Tools  │
│   (Output)   │                          │  (Discovery) │
└──────────────┘                          └──────────────┘
```

### JSON-RPC Protocol

The client uses JSON-RPC 2.0 over stdio:

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "discover_agents",
    "arguments": {
      "query": "Python backend"
    }
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[{\"name\": \"python-pro\", ...}]"
      }
    ]
  }
}
```

## Testing Workflows

### Basic Agent Discovery

```bash
# 1. Start interactive client
uv run python scripts/mcp_client.py

# 2. Search for agents
> discover Python

# 3. Get details
> details python-pro

# 4. List categories
> categories
```

### Agent Invocation & Status Tracking

```bash
# 1. Invoke an agent
> invoke python-pro "Write a CLI tool"

# 2. Note the workflow_id in the response

# 3. Check status immediately
> status

# 4. Check again after some time
> s

# 5. View last workflow
> last
```

### Scripted Testing

```bash
#!/bin/bash
# Test all MCP tools

# Search
uv run python scripts/mcp_client.py discover "React" > search_results.json

# Categories
uv run python scripts/mcp_client.py categories > categories.json

# Details
uv run python scripts/mcp_client.py details frontend-developer > details.json

# Invoke (requires manual consent for high-risk agents)
# uv run python scripts/mcp_client.py invoke python-pro "Test task"

echo "Test complete"
```

## Troubleshooting

### Connection Issues

**Error:** `MCP server not connected`

**Solution:** The client automatically starts the MCP server. If this fails:

1. Verify `mycelium.mcp.server` module exists
1. Check `uv run python -m mycelium.mcp.server` works manually
1. Enable verbose mode: `--verbose` to see detailed errors

### Tool Call Failures

**Error:** `MCP Error -32601: Method not found`

**Solution:**

1. Ensure MCP server is running the latest code
1. Check tool name spelling
1. Verify server exports the tool (check `server.py`)

### Workflow Not Found

**Error:** `Workflow 'wf_xyz' not found`

**Possible Causes:**

1. Workflow ID was mistyped
1. Redis is not running (workflows are stored in Redis)
1. Workflow has expired or been cleaned up

**Solution:**

1. Use `last` command to view the correct workflow ID
1. Check Redis is running: `redis-cli ping`
1. Invoke the agent again to create a new workflow

### High-Risk Agent Consent

**Behavior:** Agent invocation prompts for consent

**Explanation:** Agents with dangerous tools (Bash, Write) require user consent for security.

**Options:**

1. Grant consent when prompted
1. Use a lower-risk agent
1. Check consent status in `~/.config/mycelium/consent.json`

## Development

### Adding New Commands

To add a new command to the interactive CLI:

1. Add a method to `InteractiveCLI` class:

   ```python
   def cmd_mycommand(self, args: str) -> None:
       """Execute mycommand."""
       # Implementation
   ```

1. Add command handler in `run()` loop:

   ```python
   elif command == "mycommand":
       self.cmd_mycommand(args)
   ```

1. Add to help text in `show_welcome()`:

   ```python
   [cyan]mycommand <args>[/cyan] - Description
   ```

### Adding New MCP Tools

To test a new MCP tool:

1. Add method to `MCPClient` class:

   ```python
   def my_tool(self, arg: str) -> dict[str, Any]:
       return self.call_tool("my_tool", {"arg": arg})
   ```

1. Add interactive command wrapper:

   ```python
   def cmd_mytool(self, args: str) -> None:
       result = self.client.my_tool(args)
       # Display result
   ```

## Performance

The MCP client is designed for manual testing, not high-throughput automation:

- **Startup time**: ~1-2 seconds (MCP server initialization)
- **Request latency**: ~50-200ms per tool call
- **Concurrent requests**: Not supported (stdio is sequential)

For high-performance testing, consider using the Discovery API directly.

## Security

The MCP client respects the same security controls as the MCP server:

- **User consent** required for high-risk agents
- **Environment isolation** (sensitive vars blocked)
- **Output sanitization** (credentials redacted)
- **Checksum validation** (re-consent on agent changes)

The client itself does not execute agent code—it only sends requests to the MCP server, which handles execution.

## Related Documentation

- [MCP Server Implementation](/src/mycelium/mcp/server.py)
- [Agent Discovery Tools](/src/mycelium/mcp/tools.py)
- [Security & Consent](/src/mycelium/mcp/consent.py)
- [Discovery API](/src/mycelium/api/)

## Support

For issues or questions:

1. Check verbose mode output: `--verbose`
1. Review server logs
1. Check Redis connection
1. Verify agent files exist in `plugins/mycelium-core/agents/`

## License

MIT License - See project LICENSE file
