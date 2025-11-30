# Mycelium MCP Server

This directory contains the MCP (Model Context Protocol) server for Mycelium agent discovery.

## Features

The MCP server exposes three tools via the Model Context Protocol:

1. **discover_agents** - Natural language search for agents
1. **get_agent_details** - Get full metadata for a specific agent
1. **list_categories** - List all available agent categories with counts

## Running the Server

Start the MCP server using stdio transport:

```bash
uv run mycelium-mcp
```

Or directly with Python:

```bash
uv run python -m mycelium.mcp.server
```

## Module Structure

- `server.py` - FastMCP server setup and tool definitions
- `tools.py` - Agent discovery tool implementations
- `checksums.py` - Agent integrity verification (SHA-256 checksums)
- `permissions.py` - Tool permission analysis and risk assessment

## Usage Example

The MCP server is designed to be used by MCP-compatible clients like Claude Desktop.

Configure it in your MCP client with:

```json
{
  "mcpServers": {
    "mycelium": {
      "command": "uv",
      "args": ["run", "mycelium-mcp"],
      "cwd": "/path/to/mycelium"
    }
  }
}
```

## Tools

### discover_agents

Search for agents using natural language queries.

**Input:**

- `query` (string): Natural language search query (e.g., "Python backend development")

**Output:**

- List of matching agents with name, category, and description

**Example:**

```
discover_agents("database optimization")
→ [{name: "database-optimizer", category: "data", description: "..."}]
```

### get_agent_details

Get complete metadata for a specific agent.

**Input:**

- `name` (string): Agent name (e.g., "backend-developer")

**Output:**

- Full agent information including tools, command, and description

**Example:**

```
get_agent_details("backend-developer")
→ {name: "backend-developer", tools: ["Read", "Write", "Bash"], ...}
```

### list_categories

List all available agent categories with counts.

**Output:**

- List of categories with agent counts

**Example:**

```
list_categories()
→ [{category: "core", count: 10}, {category: "language", count: 15}, ...]
```

## Development

### Running Tests

```bash
# Run unit tests
uv run pytest tests/unit/mcp/test_tools.py -v

# Run manual integration test
uv run python manual_mcp_server_test.py
```

### Type Checking

```bash
uv run mypy src/mycelium/mcp/tools.py src/mycelium/mcp/server.py
```

## Architecture

The MCP server uses:

- **FastMCP 2.0** - High-level MCP server framework
- **stdio transport** - Standard for MCP communication
- **AgentLoader** - Existing Mycelium agent configuration loader
- **RegistryClient** - Agent registry integration (future use)

The server loads agent configurations from `plugins/mycelium-core/agents/` and provides search, metadata, and
categorization capabilities via MCP tools.
