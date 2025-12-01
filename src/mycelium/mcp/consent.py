"""User consent management for high-risk agent execution.

Handles consent prompts, persistence, and re-consent logic based on checksums.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from mycelium.mcp.checksums import generate_agent_checksum


@dataclass
class ConsentRecord:
    """Record of user consent for an agent."""

    agent_name: str
    checksum: str
    risk_level: str
    granted_at: str
    expires_at: str | None = None


class ConsentManager:
    """Manage user consent for agent execution."""

    def __init__(self, consent_file: Path | None = None):
        """Initialize consent manager.

        Args:
            consent_file: Path to consent storage file
                         Defaults to ~/.mycelium/agent_consents.json
        """
        if consent_file is None:
            consent_file = Path.home() / ".mycelium" / "agent_consents.json"
        self.consent_file = consent_file
        self.consent_file.parent.mkdir(parents=True, exist_ok=True)

    def check_consent(self, agent_name: str, agent_path: Path, risk_level: str) -> bool:
        """Check if user has granted consent for agent execution.

        Args:
            agent_name: Name of the agent
            agent_path: Path to agent .md file
            risk_level: Risk level from permissions analysis (used for validation)

        Returns:
            True if consent granted and valid, False otherwise
        """
        # Load consent records
        consents = self._load_consents()

        # Check if we have a consent record
        if agent_name not in consents:
            return False

        record = consents[agent_name]

        # Validate risk level matches (security check)
        if record.risk_level != risk_level:
            return False

        # Generate current checksum
        try:
            current_checksum = generate_agent_checksum(agent_path)
        except Exception:
            # If we can't generate checksum, deny consent
            return False

        # Compare checksums - if different, consent invalid
        if record.checksum != current_checksum:
            return False

        # Check expiration if set
        if record.expires_at:
            expires = datetime.fromisoformat(record.expires_at)
            if datetime.now(timezone.utc) > expires:
                return False

        # Consent is valid
        return True

    def request_consent(self, agent_name: str, agent_path: Path, risk_level: str, tools: list[str]) -> bool:
        """Request user consent via CLI prompt.

        Args:
            agent_name: Name of the agent
            agent_path: Path to agent .md file
            risk_level: Risk level (high/medium/low)
            tools: List of agent tools

        Returns:
            True if user grants consent, False otherwise
        """
        # Display warning banner
        if risk_level == "high":
            self._display_high_risk_warning(agent_name, tools)
        elif risk_level == "medium":
            self._display_medium_risk_warning(agent_name, tools)
        else:
            self._display_low_risk_warning(agent_name, tools)

        # Prompt user
        try:
            response = input("\nGrant permission? (yes/no): ").strip().lower()

            if response in ("yes", "y"):
                # Save consent
                self.grant_consent(agent_name, agent_path, risk_level)
                print(f"\nPermission granted for agent '{agent_name}'")
                return True
            print(f"\nPermission denied for agent '{agent_name}'")
            return False

        except (EOFError, KeyboardInterrupt):
            print("\n\nPermission denied (interrupted)")
            return False

    def grant_consent(self, agent_name: str, agent_path: Path, risk_level: str) -> None:
        """Grant and persist consent for an agent.

        Args:
            agent_name: Name of the agent
            agent_path: Path to agent .md file
            risk_level: Risk level
        """
        # Generate checksum
        checksum = generate_agent_checksum(agent_path)

        # Create consent record
        record = ConsentRecord(
            agent_name=agent_name,
            checksum=checksum,
            risk_level=risk_level,
            granted_at=datetime.now(timezone.utc).isoformat(),
        )

        # Load existing consents
        consents = self._load_consents()

        # Add/update record
        consents[agent_name] = record

        # Save to file
        self._save_consents(consents)

    def revoke_consent(self, agent_name: str) -> None:
        """Revoke consent for an agent.

        Args:
            agent_name: Name of the agent
        """
        # Load consents
        consents = self._load_consents()

        # Remove record
        if agent_name in consents:
            del consents[agent_name]

            # Save updated records
            self._save_consents(consents)

    def list_consents(self) -> list[ConsentRecord]:
        """List all granted consents.

        Returns:
            List of consent records
        """
        consents = self._load_consents()
        return list(consents.values())

    def _load_consents(self) -> dict[str, ConsentRecord]:
        """Load consent records from file.

        Returns:
            Dictionary mapping agent names to consent records
        """
        if not self.consent_file.exists():
            return {}

        try:
            with self.consent_file.open(encoding="utf-8") as f:
                data = json.load(f)

            # Validate data structure
            if not isinstance(data, dict):
                return {}

            # Convert to ConsentRecord objects
            consents = {}
            for agent_name, record_data in data.items():
                consents[agent_name] = ConsentRecord(**record_data)

            return consents

        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            # If file is corrupted or invalid, return empty
            return {}

    def _save_consents(self, consents: dict[str, ConsentRecord]) -> None:
        """Save consent records to file.

        Args:
            consents: Dictionary of consent records
        """
        # Convert to JSON-serializable format
        data = {agent_name: asdict(record) for agent_name, record in consents.items()}

        # Write to file
        try:
            with self.consent_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, sort_keys=True)
        except OSError:
            # Fail silently - we can't write consents
            pass

    def _display_high_risk_warning(self, agent_name: str, tools: list[str]) -> None:
        """Display high-risk consent prompt.

        Args:
            agent_name: Name of the agent
            tools: List of agent tools
        """
        # Build tools warning
        tool_warnings = []
        for tool in tools:
            if "Bash(*)" in tool or tool == "Bash":
                tool_warnings.append("  \u2022 Can execute ANY shell command (Bash(*))")
            elif "Write(*)" in tool or tool == "Write":
                tool_warnings.append("  \u2022 Can read/write ANY file (Write(*))")
            elif "Edit(*)" in tool or tool == "Edit":
                tool_warnings.append("  \u2022 Can edit ANY file (Edit(*))")

        if not tool_warnings:
            tool_warnings.append("  \u2022 Has unrestricted permissions")

        print("\n" + "=" * 60)
        print("                    SECURITY WARNING                        ")
        print("=" * 60)
        print()
        print(f"  Agent: {agent_name}")
        print("  Risk Level: HIGH")
        print()
        print("  This agent has UNRESTRICTED PERMISSIONS:")
        for warning in tool_warnings:
            print(warning)
        print("  \u2022 Has access to your entire system")
        print()
        print("  Only grant permission if you trust this agent.")
        print("=" * 60)

    def _display_medium_risk_warning(self, agent_name: str, tools: list[str]) -> None:
        """Display medium-risk consent prompt.

        Args:
            agent_name: Name of the agent
            tools: List of agent tools
        """
        print("\n" + "-" * 60)
        print("                   Permission Required                      ")
        print("-" * 60)
        print()
        print(f"  Agent: {agent_name}")
        print("  Risk Level: MEDIUM")
        print()
        print("  This agent has elevated permissions:")
        for tool in tools:
            print(f"  \u2022 {tool}")
        print()
        print("  Review permissions before granting access.")
        print("-" * 60)

    def _display_low_risk_warning(self, agent_name: str, tools: list[str]) -> None:
        """Display low-risk consent prompt.

        Args:
            agent_name: Name of the agent
            tools: List of agent tools
        """
        print("\n" + "-" * 60)
        print(f"  Agent: {agent_name}")
        print("  Risk Level: LOW")
        print()
        print("  Tools:")
        for tool in tools:
            print(f"  \u2022 {tool}")
        print("-" * 60)
