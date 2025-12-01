"""Agent file integrity verification using SHA-256 checksums.

This module provides functions to generate and verify checksums for agent .md files
to detect tampering or corruption.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def generate_agent_checksum(agent_path: Path) -> str:
    """Generate SHA-256 checksum for an agent .md file.

    Args:
        agent_path: Path to the agent .md file

    Returns:
        SHA-256 checksum in the format "sha256:hexdigest"

    Raises:
        FileNotFoundError: If the agent file doesn't exist
        IOError: If the file cannot be read
    """
    if not agent_path.exists():
        raise FileNotFoundError(f"Agent file not found: {agent_path}")

    if not agent_path.is_file():
        raise ValueError(f"Path is not a file: {agent_path}")

    # Read file in binary mode and generate checksum
    sha256_hash = hashlib.sha256()
    try:
        with open(agent_path, "rb") as f:
            # Read in chunks for memory efficiency
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
    except IOError as e:
        raise IOError(f"Failed to read agent file {agent_path}: {e}") from e

    return f"sha256:{sha256_hash.hexdigest()}"


def generate_all_checksums(plugin_dir: Path) -> dict[str, str]:
    """Generate checksums for all agents in the plugin directory.

    Args:
        plugin_dir: Path to the plugin directory containing agent .md files

    Returns:
        Dictionary mapping agent names to checksums
        Format: {"agent-name": "sha256:hexdigest", ...}

    Raises:
        FileNotFoundError: If the plugin directory doesn't exist
    """
    if not plugin_dir.exists():
        raise FileNotFoundError(f"Plugin directory not found: {plugin_dir}")

    if not plugin_dir.is_dir():
        raise ValueError(f"Path is not a directory: {plugin_dir}")

    checksums: dict[str, str] = {}

    # Find all .md files in the plugin directory
    for agent_file in sorted(plugin_dir.glob("*.md")):
        try:
            # Extract agent name from filename (strip number prefix and category)
            agent_name = _extract_agent_name(agent_file.name)
            checksum = generate_agent_checksum(agent_file)
            checksums[agent_name] = checksum
        except (FileNotFoundError, IOError, ValueError) as e:
            # Log error but continue processing other agents
            print(f"Warning: Failed to generate checksum for {agent_file.name}: {e}")
            continue

    return checksums


def save_checksums(checksums: dict[str, str], path: Path) -> None:
    """Save checksums to a JSON file.

    Args:
        checksums: Dictionary of agent names to checksums
        path: Path to save the checksums file

    Raises:
        IOError: If the file cannot be written
    """
    # Create parent directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create checksums data structure
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "agents": checksums,
    }

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
    except IOError as e:
        raise IOError(f"Failed to write checksums to {path}: {e}") from e


def load_checksums(path: Path) -> dict[str, str]:
    """Load checksums from a JSON file.

    Args:
        path: Path to the checksums file

    Returns:
        Dictionary mapping agent names to checksums

    Raises:
        FileNotFoundError: If the checksums file doesn't exist
        ValueError: If the file format is invalid
        IOError: If the file cannot be read
    """
    if not path.exists():
        raise FileNotFoundError(f"Checksums file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except IOError as e:
        raise IOError(f"Failed to read checksums from {path}: {e}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in checksums file {path}: {e}") from e

    # Validate structure
    if not isinstance(data, dict):
        raise ValueError(f"Invalid checksums file format: expected dict, got {type(data)}")

    if "agents" not in data:
        raise ValueError("Invalid checksums file: missing 'agents' key")

    if not isinstance(data["agents"], dict):
        raise ValueError(f"Invalid checksums file: 'agents' must be dict, got {type(data['agents'])}")

    return data["agents"]


def verify_agent_checksum(agent_name: str, agent_path: Path, expected: str) -> bool:
    """Verify that an agent file matches the expected checksum.

    Args:
        agent_name: Name of the agent (for error messages)
        agent_path: Path to the agent .md file
        expected: Expected checksum in format "sha256:hexdigest"

    Returns:
        True if checksum matches, False otherwise

    Raises:
        FileNotFoundError: If the agent file doesn't exist
        IOError: If the file cannot be read
    """
    try:
        actual = generate_agent_checksum(agent_path)
        return actual == expected
    except (FileNotFoundError, IOError):
        # Re-raise file access errors
        raise


def verify_all_checksums(plugin_dir: Path, checksums_path: Path) -> list[str]:
    """Verify all agents against stored checksums.

    Args:
        plugin_dir: Path to the plugin directory containing agent .md files
        checksums_path: Path to the checksums JSON file

    Returns:
        List of agent names that failed verification (empty list if all pass)
        Reasons for failure:
        - Checksum mismatch (file modified)
        - Agent file missing
        - Agent not in checksums file (new agent)

    Raises:
        FileNotFoundError: If plugin directory or checksums file doesn't exist
        ValueError: If checksums file format is invalid
    """
    # Load stored checksums
    stored_checksums = load_checksums(checksums_path)

    # Generate current checksums
    try:
        current_checksums = generate_all_checksums(plugin_dir)
    except FileNotFoundError:
        raise

    failed: list[str] = []

    # Check for agents in stored checksums
    for agent_name, expected_checksum in stored_checksums.items():
        if agent_name not in current_checksums:
            # Agent file is missing
            failed.append(agent_name)
            print(f"Warning: Agent file missing: {agent_name}")
        elif current_checksums[agent_name] != expected_checksum:
            # Checksum mismatch
            failed.append(agent_name)
            print(f"Warning: Checksum mismatch for agent: {agent_name}")
            print(f"  Expected: {expected_checksum}")
            print(f"  Actual:   {current_checksums[agent_name]}")

    # Check for new agents not in stored checksums
    for agent_name in current_checksums:
        if agent_name not in stored_checksums:
            # New agent detected
            failed.append(agent_name)
            print(f"Warning: New agent detected (not in checksums): {agent_name}")

    return failed


def _extract_agent_name(filename: str) -> str:
    """Extract agent name from filename.

    Removes .md extension and number/category prefix.

    Examples:
        "01-core-backend-developer.md" -> "backend-developer"
        "02-language-python-pro.md" -> "python-pro"

    Args:
        filename: Agent filename

    Returns:
        Cleaned agent name
    """
    # Remove .md extension
    name = filename.removesuffix(".md")

    # Remove number prefix (e.g., "01-")
    parts = name.split("-", maxsplit=1)
    if len(parts) == 2 and parts[0].isdigit():
        name = parts[1]

    # Remove category prefix (e.g., "core-")
    # Common categories: core, language, specialized, data, developer, etc.
    categories = [
        "core",
        "language",
        "specialized",
        "data",
        "developer",
        "business",
        "devops",
        "infrastructure",
        "security",
    ]

    for category in categories:
        prefix = f"{category}-"
        if name.startswith(prefix):
            name = name.removeprefix(prefix)
            break

    return name
