"""Agent selector using fzf for fuzzy-searchable agent discovery.

Provides interactive agent selection with preview pane showing agent details.
Handles security by sanitizing agent names to prevent shell injection.
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, Sequence

from mycelium.discovery.scanner import DiscoveredAgent
from mycelium.errors import MyceliumError
from mycelium.registry.client import AgentInfo, RegistryClient


def check_fzf_installed() -> bool:
    """Check if fzf is installed on the system.

    Returns:
        True if fzf is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["fzf", "--version"],
            capture_output=True,
            timeout=2,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_fzf_install_instructions() -> str:
    """Get platform-specific fzf installation instructions.

    Returns:
        Formatted installation instructions string
    """
    instructions = """fzf is not installed. Please install it:

macOS (Homebrew):
  brew install fzf

Linux (apt):
  sudo apt install fzf

Linux (pacman):
  sudo pacman -S fzf

Windows (Scoop):
  scoop install fzf

Or install via GitHub:
  https://github.com/junegunn/fzf#installation
"""
    return instructions


def sanitize_agent_name(name: str) -> str:
    """Sanitize agent name to prevent shell injection.

    Args:
        name: Agent name to sanitize

    Returns:
        Sanitized agent name safe for shell usage

    Raises:
        MyceliumError: If agent name contains dangerous characters
    """
    # Allow only alphanumeric, hyphens, underscores, and dots
    # This prevents shell injection via agent names
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")

    if not all(c in allowed_chars for c in name):
        raise MyceliumError(
            f"Invalid agent name: {name!r}",
            suggestion="Agent names must contain only alphanumeric characters, hyphens, underscores, and dots",
            docs_url="https://docs.mycelium.dev/security/agent-names",
            debug_info={"agent_name": name}
        )

    return name


def create_preview_script(agents_data: dict[str, AgentInfo | DiscoveredAgent]) -> Path:
    """Create a temporary preview script for fzf.

    Args:
        agents_data: Dictionary mapping agent names to agent info

    Returns:
        Path to temporary preview script

    Note:
        The preview script is written to /tmp for security isolation
    """
    # Create a temporary directory for the preview script
    preview_script = Path("/tmp/mycelium_fzf_preview.sh")

    # Create JSON data file with agent details
    json_file = Path("/tmp/mycelium_agents.json")
    serializable_data = {}
    for name, agent in agents_data.items():
        if isinstance(agent, AgentInfo):
            serializable_data[name] = agent.to_dict()
        else:
            # DiscoveredAgent
            serializable_data[name] = {
                "name": agent.name,
                "category": agent.category,
                "description": agent.description,
                "file_path": str(agent.file_path),
            }

    json_file.write_text(json.dumps(serializable_data, indent=2), encoding="utf-8")

    # Create preview script that reads from JSON
    script_content = f"""#!/bin/bash
AGENT_NAME="$1"
jq -r ".[\\"$AGENT_NAME\\"] | if . then
    \\"Name: \\" + .name + \\"\\n\\" +
    \\"Category: \\" + .category + \\"\\n\\" +
    \\"Description: \\" + (.description // \\"No description\\") + \\"\\n\\"
else
    \\"Agent not found\\"
end" {json_file}
"""

    preview_script.write_text(script_content, encoding="utf-8")
    preview_script.chmod(0o755)

    return preview_script


def run_fzf_selector(
    agents: Sequence[AgentInfo | DiscoveredAgent],
    category: Optional[str] = None,
) -> Optional[str]:
    """Run fzf interactive selector for agents.

    Args:
        agents: List of agents to select from
        category: Optional category filter

    Returns:
        Selected agent name or None if cancelled

    Raises:
        MyceliumError: If fzf fails or agent names are invalid
    """
    if not agents:
        raise MyceliumError(
            "No agents available to select",
            suggestion="Discover agents first: mycelium agent discover",
            docs_url="https://docs.mycelium.dev/cli/discover"
        )

    # Check fzf is installed
    if not check_fzf_installed():
        raise MyceliumError(
            "fzf is not installed",
            suggestion=get_fzf_install_instructions(),
            docs_url="https://github.com/junegunn/fzf#installation"
        )

    # Sanitize all agent names for security
    agents_data: dict[str, AgentInfo | DiscoveredAgent] = {}
    agent_names: list[str] = []

    for agent in agents:
        try:
            sanitized_name = sanitize_agent_name(agent.name)
            agents_data[sanitized_name] = agent
            agent_names.append(sanitized_name)
        except MyceliumError:
            # Skip agents with invalid names
            continue

    if not agent_names:
        raise MyceliumError(
            "No valid agents found after sanitization",
            suggestion="Check agent naming conventions",
            docs_url="https://docs.mycelium.dev/security/agent-names"
        )

    # Create preview script
    preview_script = create_preview_script(agents_data)

    try:
        # Build fzf command with preview
        prompt = f"Select agent ({len(agent_names)} available)"
        if category:
            prompt += f" [Category: {category}]"

        fzf_cmd = [
            "fzf",
            "--prompt", f"{prompt} > ",
            "--height", "60%",
            "--reverse",
            "--border",
            "--info", "inline",
            "--preview", f"{preview_script} {{}}",
            "--preview-window", "right:50%:wrap",
            "--bind", "ctrl-c:abort",
        ]

        # Run fzf with agent names as input
        # fzf automatically opens /dev/tty for keyboard input and UI display
        # when stdin is a pipe. We pipe agent names and capture stdout for result.
        process = subprocess.Popen(
            fzf_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,  # Inherit - fzf uses /dev/tty for display anyway
            text=True,
        )
        stdout, _ = process.communicate(
            input="\n".join(agent_names),
            timeout=300,
        )
        returncode = process.returncode

        # Handle cancellation (Ctrl+C or Ctrl+D)
        if returncode == 130:  # SIGINT (Ctrl+C)
            return None
        if returncode == 1:  # No match or ESC
            return None

        # Check for other errors
        if returncode != 0:
            raise MyceliumError(
                f"fzf exited with error code {returncode}",
                suggestion="Check fzf is properly installed",
                docs_url="https://github.com/junegunn/fzf",
                debug_info={"returncode": returncode}
            )

        # Get selected agent name
        selected = stdout.strip()
        if not selected:
            return None

        return selected

    except subprocess.TimeoutExpired:
        raise MyceliumError(
            "fzf selection timed out",
            suggestion="Selection took too long (>5 minutes)",
            docs_url="https://docs.mycelium.dev/cli/select"
        )
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        return None
    finally:
        # Cleanup temporary files
        if preview_script.exists():
            preview_script.unlink()
        json_file = Path("/tmp/mycelium_agents.json")
        if json_file.exists():
            json_file.unlink()


def select_agent_interactive(
    registry: RegistryClient,
    category: Optional[str] = None,
) -> Optional[AgentInfo]:
    """Interactive agent selection using fzf.

    Args:
        registry: Registry client to fetch agents
        category: Optional category filter

    Returns:
        Selected agent info or None if cancelled

    Raises:
        MyceliumError: If selection fails
    """
    # Get agents from registry
    try:
        agents = registry.list_agents(category=category)
    except Exception as e:
        raise MyceliumError(
            f"Failed to list agents: {e}",
            suggestion="Ensure Redis is running: redis-cli ping",
            docs_url="https://docs.mycelium.dev/setup/redis",
            debug_info={"category": category}
        )

    if not agents:
        raise MyceliumError(
            "No agents registered" + (f" in category '{category}'" if category else ""),
            suggestion="Discover agents first: mycelium agent discover",
            docs_url="https://docs.mycelium.dev/cli/discover"
        )

    # Run fzf selector
    selected_name = run_fzf_selector(agents, category=category)

    if not selected_name:
        return None

    # Get full agent info
    agent_info = registry.get_agent(selected_name)
    if not agent_info:
        raise MyceliumError(
            f"Selected agent '{selected_name}' not found in registry",
            suggestion="Try refreshing: mycelium agent discover",
            docs_url="https://docs.mycelium.dev/cli/select"
        )

    return agent_info
