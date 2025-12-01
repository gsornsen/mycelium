# Team 1: MCP Execution Tools

## Mission

Add agent execution capabilities to the Mycelium MCP server.

## Context

- MCP server at `/home/gerald/git/mycelium/src/mycelium/mcp/server.py`
- Tools implementation at `/home/gerald/git/mycelium/src/mycelium/mcp/tools.py`
- ProcessManager available at `/home/gerald/git/mycelium/src/mycelium/supervisor/manager.py`
- RegistryClient available at `/home/gerald/git/mycelium/src/mycelium/registry/client.py`

## Tasks

### 1. Add `invoke_agent` Tool

**File**: `/home/gerald/git/mycelium/src/mycelium/mcp/tools.py`

Add method to `AgentDiscoveryTools` class:

```python
def invoke_agent(
    self,
    agent_name: str,
    task_description: str,
    context: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Invoke an agent to execute a task.

    Args:
        agent_name: Name of agent to invoke
        task_description: Task for the agent to execute
        context: Optional context dictionary (files, data, etc.)

    Returns:
        Dictionary with:
        - workflow_id: Unique workflow identifier
        - status: "started" | "failed"
        - agent_name: Name of invoked agent
        - message: Status message
    """
    # Implementation requirements:
    # 1. Validate agent exists using self.loader.load_agent(agent_name)
    # 2. Check agent risk level using permissions.get_agent_risk_level()
    # 3. If high-risk, check consent (will be wired later by integration team)
    # 4. Generate workflow_id using uuid4
    # 5. Use ProcessManager to start agent with task
    # 6. Store workflow state in Redis via RegistryClient
    # 7. Return workflow info
```

**Integration Points**:

- Import `ProcessManager` from `mycelium.supervisor.manager`
- Import `RegistryClient` from `mycelium.registry.client`
- Import risk checking from `mycelium.mcp.permissions`
- Use existing `AgentLoader` instance (self.loader)

### 2. Add `get_workflow_status` Tool

**File**: `/home/gerald/git/mycelium/src/mycelium/mcp/tools.py`

Add method to `AgentDiscoveryTools` class:

```python
def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
    """Get status of a running workflow.

    Args:
        workflow_id: Workflow identifier from invoke_agent

    Returns:
        Dictionary with:
        - workflow_id: Workflow identifier
        - status: "running" | "completed" | "failed" | "not_found"
        - agent_name: Name of agent
        - started_at: ISO timestamp
        - completed_at: ISO timestamp (if completed)
        - result: Execution result (if completed)
        - error: Error message (if failed)
    """
    # Implementation requirements:
    # 1. Query workflow state from Redis via RegistryClient
    # 2. Check process status via ProcessManager
    # 3. Return comprehensive status info
```

### 3. Register Tools in MCP Server

**File**: `/home/gerald/git/mycelium/src/mycelium/mcp/server.py`

Add two new @mcp.tool() decorated functions:

```python
@mcp.tool()
def invoke_agent(
    agent_name: str,
    task_description: str,
    context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Invoke an agent to execute a task via MCP.

    Use this to delegate work to specialist agents.
    """
    return _tools.invoke_agent(agent_name, task_description, context)

@mcp.tool()
def get_workflow_status(workflow_id: str) -> dict[str, Any]:
    """Get the status of a running agent workflow.

    Use this to check on agent execution progress.
    """
    return _tools.get_workflow_status(workflow_id)
```

### 4. Testing

**File**: `/home/gerald/git/mycelium/tests/unit/mcp/test_execution_tools.py`

Create comprehensive tests:

- Test `invoke_agent` with valid agent
- Test `invoke_agent` with invalid agent
- Test `get_workflow_status` with valid workflow
- Test `get_workflow_status` with invalid workflow
- Test workflow state persistence
- Mock ProcessManager and RegistryClient

## Success Criteria

- [ ] `invoke_agent` tool registered in MCP server
- [ ] `get_workflow_status` tool registered in MCP server
- [ ] Tools integrate with ProcessManager
- [ ] Workflow state persisted in Redis
- [ ] All tests pass
- [ ] No consent/isolation logic yet (integration team will wire)

## Files to Create/Modify

- Modify: `/home/gerald/git/mycelium/src/mycelium/mcp/tools.py`
- Modify: `/home/gerald/git/mycelium/src/mycelium/mcp/server.py`
- Create: `/home/gerald/git/mycelium/tests/unit/mcp/test_execution_tools.py`

## Coordination

- Update Redis: `mycelium:m5:team1:status` = "in_progress" when starting
- Update Redis: `mycelium:m5:team1:status` = "completed" when done
- Publish event: `mycelium:m5:events` when completed
