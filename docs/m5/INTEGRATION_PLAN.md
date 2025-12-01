# M5 Integration Plan

## Overview

After Teams 1, 2, and 3 complete their work, integrate the components into a cohesive system.

## Integration Points

### 1. Wire Consent into invoke_agent

**File**: `/home/gerald/git/mycelium/src/mycelium/mcp/tools.py`

In `AgentDiscoveryTools.invoke_agent()`:

```python
from mycelium.mcp.consent import ConsentManager
from mycelium.mcp.permissions import get_agent_risk_level, parse_agent_tools

def invoke_agent(self, agent_name: str, task_description: str, context=None):
    # Load agent config
    agent_config = self.loader.load_agent(agent_name)
    if not agent_config:
        return {"status": "failed", "error": f"Agent '{agent_name}' not found"}

    # Get agent file path
    agent_path = self.loader.plugin_dir / f"{agent_name}.md"

    # Check risk level
    risk_level = get_agent_risk_level(agent_path)

    # If high-risk, require consent
    if risk_level == "high":
        consent_mgr = ConsentManager()

        # Check existing consent
        if not consent_mgr.check_consent(agent_name, agent_path, risk_level):
            # Request consent
            tools = parse_agent_tools(agent_path)
            if not consent_mgr.request_consent(agent_name, agent_path, risk_level, tools):
                return {
                    "status": "failed",
                    "error": "User denied consent for high-risk agent"
                }

    # Consent granted (or not required), proceed with execution
    # ... rest of invoke_agent implementation
```

### 2. Wire Isolation into ProcessManager

**File**: `/home/gerald/git/mycelium/src/mycelium/supervisor/manager.py`

In `ProcessManager.start_agent()`:

```python
from mycelium.mcp.isolation import EnvironmentIsolation

def start_agent(self, name: str, config: Optional[Path] = None) -> int:
    # ... existing code ...

    # Create isolated environment
    isolation = EnvironmentIsolation()
    clean_env = isolation.filter_environment(os.environ.copy())

    # Start process with isolated environment
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=workdir,
        env=clean_env,  # Use filtered environment
        start_new_session=True,
    )

    # ... rest of method ...
```

In `ProcessManager.get_logs()`:

```python
from mycelium.mcp.isolation import OutputSanitizer

def get_logs(self, name: str, lines: int = 50) -> str:
    # Read log entries
    entries = self.log_manager.read(agent_name=name, lines=lines)

    # Sanitize output
    sanitizer = OutputSanitizer()
    output_lines = []
    for entry in entries:
        formatted = entry.format(include_timestamp=True)
        sanitized = sanitizer.sanitize(formatted)
        output_lines.append(sanitized)

    return "\n".join(output_lines) + "\n"
```

### 3. Update MCP Server Documentation

**File**: `/home/gerald/git/mycelium/src/mycelium/mcp/server.py`

Update docstrings for new tools:

```python
@mcp.tool()
def invoke_agent(
    agent_name: str,
    task_description: str,
    context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Invoke an agent to execute a task via MCP.

    This tool delegates work to specialist agents. For high-risk
    agents (those with Bash(*) or Write(*) permissions), the user
    will be prompted for consent via CLI.

    Security features:
    - User consent required for dangerous tools
    - Environment isolation (sensitive vars blocked)
    - Output sanitization (credentials redacted)
    - Checksum-based re-consent on agent changes

    Args:
        agent_name: Name of the agent to invoke (e.g., "python-pro")
        task_description: Description of the task to execute
        context: Optional context dict (files, project info, etc.)

    Returns:
        Dictionary with workflow_id, status, and details

    Examples:
        >>> invoke_agent("python-pro", "Implement user authentication")
        {
            "workflow_id": "wf_abc123",
            "status": "started",
            "agent_name": "python-pro",
            "message": "Agent started successfully"
        }
    """
    return _tools.invoke_agent(agent_name, task_description, context)
```

### 4. Integration Tests

**File**: `/home/gerald/git/mycelium/tests/integration/mcp/test_m5_integration.py`

End-to-end integration tests:

```python
"""Integration tests for M5: MCP Server Execution."""

import pytest
from pathlib import Path
from mycelium.mcp.tools import AgentDiscoveryTools
from mycelium.mcp.consent import ConsentManager
from mycelium.mcp.isolation import EnvironmentIsolation

def test_invoke_low_risk_agent_no_consent():
    """Low-risk agents should not require consent."""
    tools = AgentDiscoveryTools()

    # Invoke low-risk agent
    result = tools.invoke_agent("documentation-writer", "Write README")

    # Should succeed without consent prompt
    assert result["status"] == "started"
    assert "workflow_id" in result

def test_invoke_high_risk_agent_with_consent(monkeypatch):
    """High-risk agents should require consent."""
    tools = AgentDiscoveryTools()

    # Mock user input: grant consent
    monkeypatch.setattr('builtins.input', lambda _: 'yes')

    # Invoke high-risk agent
    result = tools.invoke_agent("backend-developer", "Implement auth")

    # Should succeed after consent
    assert result["status"] == "started"

    # Consent should be persisted
    consent_mgr = ConsentManager()
    consents = consent_mgr.list_consents()
    assert any(c.agent_name == "backend-developer" for c in consents)

def test_invoke_high_risk_agent_denied_consent(monkeypatch):
    """High-risk agents should fail if consent denied."""
    tools = AgentDiscoveryTools()

    # Mock user input: deny consent
    monkeypatch.setattr('builtins.input', lambda _: 'no')

    # Invoke high-risk agent
    result = tools.invoke_agent("backend-developer", "Implement auth")

    # Should fail without consent
    assert result["status"] == "failed"
    assert "consent" in result["error"].lower()

def test_environment_isolation_applied():
    """Sensitive environment variables should be blocked."""
    import os
    from mycelium.supervisor.manager import ProcessManager

    # Set sensitive env var
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test_secret_key"

    # Start agent (would use ProcessManager internally)
    manager = ProcessManager()

    # Verify isolation is applied
    isolation = EnvironmentIsolation()
    filtered = isolation.filter_environment(os.environ)

    assert "AWS_SECRET_ACCESS_KEY" not in filtered
    assert "PATH" in filtered  # Safe vars still passed

def test_output_sanitization():
    """Agent output should be sanitized."""
    from mycelium.mcp.isolation import OutputSanitizer

    sanitizer = OutputSanitizer()

    # Test various credential types
    test_cases = [
        (
            "My AWS key: AKIAIOSFODNN7EXAMPLE",
            "My AWS key: [AWS_ACCESS_KEY_REDACTED]"
        ),
        (
            "api_key = 'sk_test_1234567890abcdefghij'",
            "api_key = [REDACTED]"
        ),
    ]

    for input_text, expected in test_cases:
        result = sanitizer.sanitize(input_text)
        assert expected in result or "[REDACTED]" in result

def test_re_consent_on_checksum_change(tmp_path, monkeypatch):
    """Consent should be invalidated if agent changes."""
    # Create test agent file
    agent_file = tmp_path / "test-agent.md"
    agent_file.write_text("---\ntools: Bash(*)\n---\nTest agent")

    consent_mgr = ConsentManager(consent_file=tmp_path / "consents.json")

    # Grant initial consent
    consent_mgr.grant_consent("test-agent", agent_file, "high")

    # Verify consent
    assert consent_mgr.check_consent("test-agent", agent_file, "high")

    # Modify agent file
    agent_file.write_text("---\ntools: Bash(*), Write(*)\n---\nModified")

    # Consent should now be invalid
    assert not consent_mgr.check_consent("test-agent", agent_file, "high")

    # Should request re-consent
    monkeypatch.setattr('builtins.input', lambda _: 'yes')
    consent_mgr.request_consent("test-agent", agent_file, "high", ["Bash(*)", "Write(*)"])

    # Should be valid again
    assert consent_mgr.check_consent("test-agent", agent_file, "high")
```

## Integration Checklist

- [ ] Consent checks integrated into `invoke_agent`
- [ ] Environment isolation integrated into `ProcessManager.start_agent`
- [ ] Output sanitization integrated into `ProcessManager.get_logs`
- [ ] All integration tests passing
- [ ] Documentation updated
- [ ] Security review completed

## Testing Command

Run all M5 tests:

```bash
uv run pytest tests/unit/mcp/ -v
uv run pytest tests/integration/mcp/test_m5_integration.py -v
```

## Rollout Plan

1. Merge Team 1, 2, 3 branches into `feat/m5-mcp-server-execution`
1. Run integration tests
1. Fix any integration issues
1. Run full test suite
1. Security review
1. Merge to main branch (or designated integration branch)

## Success Criteria

- [ ] All team deliverables completed
- [ ] Integration complete
- [ ] All tests passing (unit + integration)
- [ ] No regressions in existing functionality
- [ ] Documentation complete
- [ ] Security requirements met
