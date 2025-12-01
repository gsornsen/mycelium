# Team 2: Consent System

## Mission

Implement user consent system for high-risk agent execution.

## Context

- Permissions analysis at `/home/gerald/git/mycelium/src/mycelium/mcp/permissions.py`
- Checksum validation at `/home/gerald/git/mycelium/src/mycelium/mcp/checksums.py`
- High-risk pattern: `Bash(*)` from permissions.py
- Consent must be CLI-based (no GUI for v1.0)

## Tasks

### 1. Create Consent Module

**File**: `/home/gerald/git/mycelium/src/mycelium/mcp/consent.py`

Implement complete consent system:

```python
"""User consent management for high-risk agent execution.

Handles consent prompts, persistence, and re-consent logic.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import json

@dataclass
class ConsentRecord:
    """Record of user consent for an agent."""
    agent_name: str
    checksum: str
    risk_level: str
    granted_at: str
    expires_at: Optional[str] = None

class ConsentManager:
    """Manage user consent for agent execution."""

    def __init__(self, consent_file: Optional[Path] = None):
        """Initialize consent manager.

        Args:
            consent_file: Path to consent storage file
                         Defaults to ~/.mycelium/agent_consents.json
        """
        if consent_file is None:
            consent_file = Path.home() / ".mycelium" / "agent_consents.json"
        self.consent_file = consent_file
        self.consent_file.parent.mkdir(parents=True, exist_ok=True)

    def check_consent(
        self,
        agent_name: str,
        agent_path: Path,
        risk_level: str
    ) -> bool:
        """Check if user has granted consent for agent execution.

        Args:
            agent_name: Name of the agent
            agent_path: Path to agent .md file
            risk_level: Risk level from permissions analysis

        Returns:
            True if consent granted and valid, False otherwise
        """
        # Implementation requirements:
        # 1. Load consent records from JSON file
        # 2. Find record for agent_name
        # 3. Generate current checksum for agent_path
        # 4. Compare checksums - if different, consent invalid
        # 5. Check expiration if set
        # 6. Return True if consent valid
        pass

    def request_consent(
        self,
        agent_name: str,
        agent_path: Path,
        risk_level: str,
        tools: list[str]
    ) -> bool:
        """Request user consent via CLI prompt.

        Args:
            agent_name: Name of the agent
            agent_path: Path to agent .md file
            risk_level: Risk level (high/medium/low)
            tools: List of agent tools

        Returns:
            True if user grants consent, False otherwise
        """
        # Implementation requirements:
        # 1. Display warning banner
        # 2. Show agent details (name, tools, risk level)
        # 3. For high-risk agents, show specific warnings:
        #    "This agent can execute ANY shell command"
        #    "This agent can modify ANY file"
        # 4. Prompt user: "Grant permission? (yes/no): "
        # 5. If yes, save consent record
        # 6. Return user decision
        pass

    def grant_consent(
        self,
        agent_name: str,
        agent_path: Path,
        risk_level: str
    ) -> None:
        """Grant and persist consent for an agent.

        Args:
            agent_name: Name of the agent
            agent_path: Path to agent .md file
            risk_level: Risk level
        """
        # Implementation requirements:
        # 1. Generate checksum for agent file
        # 2. Create ConsentRecord
        # 3. Load existing consents
        # 4. Add/update record
        # 5. Save to JSON file
        pass

    def revoke_consent(self, agent_name: str) -> None:
        """Revoke consent for an agent.

        Args:
            agent_name: Name of the agent
        """
        # Implementation requirements:
        # 1. Load consent records
        # 2. Remove record for agent_name
        # 3. Save updated records
        pass

    def list_consents(self) -> list[ConsentRecord]:
        """List all granted consents.

        Returns:
            List of consent records
        """
        # Implementation requirements:
        # 1. Load and return all consent records
        pass

    def _load_consents(self) -> dict[str, ConsentRecord]:
        """Load consent records from file."""
        # Implementation: Read JSON, parse to ConsentRecord objects
        pass

    def _save_consents(self, consents: dict[str, ConsentRecord]) -> None:
        """Save consent records to file."""
        # Implementation: Serialize to JSON, write file
        pass
```

### 2. CLI Consent Prompt Design

**High-Risk Agent Warning**:

```
╔════════════════════════════════════════════════════════════╗
║                    SECURITY WARNING                        ║
║                                                            ║
║  Agent: backend-developer                                  ║
║  Risk Level: HIGH                                          ║
║                                                            ║
║  This agent has UNRESTRICTED PERMISSIONS:                  ║
║  • Can execute ANY shell command (Bash(*))                 ║
║  • Can read/write ANY file                                 ║
║  • Has access to your entire system                        ║
║                                                            ║
║  Only grant permission if you trust this agent.            ║
╚════════════════════════════════════════════════════════════╝

Grant permission? (yes/no):
```

### 3. Re-Consent Logic

When agent checksum changes:

```
╔════════════════════════════════════════════════════════════╗
║                 AGENT MODIFIED DETECTED                    ║
║                                                            ║
║  Agent: backend-developer                                  ║
║  Previous consent is no longer valid.                      ║
║                                                            ║
║  The agent definition has changed since you last           ║
║  granted permission. Please review and re-consent.         ║
╚════════════════════════════════════════════════════════════╝

Grant permission? (yes/no):
```

### 4. Testing

**File**: `/home/gerald/git/mycelium/tests/unit/mcp/test_consent.py`

Test coverage:

- Test consent grant and persistence
- Test consent check with valid checksum
- Test consent invalidation on checksum change
- Test consent revocation
- Test consent listing
- Test CLI prompt (mock user input)
- Test consent file creation
- Test concurrent consent updates

## Success Criteria

- [ ] ConsentManager class implemented
- [ ] Consent persistence in `~/.mycelium/agent_consents.json`
- [ ] CLI consent prompts working
- [ ] Re-consent on checksum change working
- [ ] All tests pass
- [ ] Clean, user-friendly consent messages

## Files to Create

- Create: `/home/gerald/git/mycelium/src/mycelium/mcp/consent.py`
- Create: `/home/gerald/git/mycelium/tests/unit/mcp/test_consent.py`

## Coordination

- Update Redis: `mycelium:m5:team2:status` = "in_progress" when starting
- Update Redis: `mycelium:m5:team2:status` = "completed" when done
- Publish event: `mycelium:m5:events` when completed
