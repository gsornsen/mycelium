"""Tool permission analysis for Mycelium agents.

This module provides functionality to detect and analyze tool permissions
in agent definitions, identifying potentially dangerous patterns and
providing risk assessments.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re
import yaml


@dataclass
class ToolPermission:
    """Represents a tool permission with risk assessment."""

    tool_name: str
    pattern: str
    risk_level: str  # "high", "medium", "low"
    description: str


# Dangerous tool patterns and their risk levels
DANGEROUS_PATTERNS = {
    # High risk - unrestricted access
    r"^Bash$": {
        "risk": "high",
        "desc": "Unrestricted shell access - can execute any command",
    },
    r"^Bash\(\*\)$": {
        "risk": "high",
        "desc": "Unrestricted shell access - can execute any command",
    },
    r"^Bash\(\*:\*\)$": {
        "risk": "high",
        "desc": "Unrestricted shell access - can execute any command",
    },
    r"^Write$": {
        "risk": "high",
        "desc": "Unrestricted file write - can modify any file",
    },
    r"^Write\(\*\)$": {
        "risk": "high",
        "desc": "Unrestricted file write - can modify any file",
    },
    r"^Edit$": {
        "risk": "high",
        "desc": "Unrestricted file edit - can modify any file",
    },
    r"^Edit\(\*\)$": {
        "risk": "high",
        "desc": "Unrestricted file edit - can modify any file",
    },
    r"^MultiEdit$": {
        "risk": "high",
        "desc": "Unrestricted multi-file edit - can modify multiple files",
    },
    r"^MultiEdit\(\*\)$": {
        "risk": "high",
        "desc": "Unrestricted multi-file edit - can modify multiple files",
    },
    # Medium risk - unrestricted read
    r"^Read$": {
        "risk": "medium",
        "desc": "Unrestricted file read - can read any file",
    },
    r"^Read\(\*\)$": {
        "risk": "medium",
        "desc": "Unrestricted file read - can read any file",
    },
    # Medium risk - container access
    r"^Docker$": {
        "risk": "medium",
        "desc": "Docker access - can manage containers and images",
    },
    r"^kubernetes$": {
        "risk": "medium",
        "desc": "Kubernetes access - can manage cluster resources",
    },
    # Low risk - restricted patterns
    r"^Bash\([^*]+\)$": {
        "risk": "low",
        "desc": "Restricted shell access - limited to specific commands",
    },
    r"^Bash\([^*]+:\*\)$": {
        "risk": "low",
        "desc": "Restricted shell access - limited command namespace",
    },
}


def parse_agent_tools(agent_path: Path) -> list[str]:
    """Extract tool permissions from agent .md file frontmatter.

    Args:
        agent_path: Path to the agent markdown file

    Returns:
        List of tool names/patterns from the frontmatter

    Raises:
        ValueError: If the file doesn't exist or frontmatter is invalid
    """
    if not agent_path.exists():
        raise ValueError(f"Agent file not found: {agent_path}")

    content = agent_path.read_text(encoding="utf-8")

    # Extract YAML frontmatter
    frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not frontmatter_match:
        raise ValueError(f"No frontmatter found in {agent_path}")

    frontmatter_text = frontmatter_match.group(1)

    try:
        frontmatter = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter in {agent_path}: {e}")

    # Extract tools field
    tools_field = frontmatter.get("tools", "")

    if not tools_field:
        return []

    # Parse tools - can be comma-separated string
    if isinstance(tools_field, str):
        tools = [tool.strip() for tool in tools_field.split(",")]
    elif isinstance(tools_field, list):
        tools = [str(tool).strip() for tool in tools_field]
    else:
        tools = [str(tools_field).strip()]

    return [tool for tool in tools if tool]


def analyze_tool_permissions(tools: list[str]) -> list[ToolPermission]:
    """Analyze tools and return permission assessments.

    Args:
        tools: List of tool names/patterns to analyze

    Returns:
        List of ToolPermission objects with risk assessments
    """
    permissions = []

    for tool in tools:
        # Check against dangerous patterns
        matched = False
        for pattern, info in DANGEROUS_PATTERNS.items():
            if re.match(pattern, tool):
                permissions.append(
                    ToolPermission(
                        tool_name=tool,
                        pattern=pattern,
                        risk_level=info["risk"],
                        description=info["desc"],
                    )
                )
                matched = True
                break

        # If not matched, it's a safe tool (low risk)
        if not matched:
            permissions.append(
                ToolPermission(
                    tool_name=tool,
                    pattern=f"^{re.escape(tool)}$",
                    risk_level="low",
                    description=f"Standard tool: {tool}",
                )
            )

    return permissions


def get_agent_risk_level(agent_path: Path) -> str:
    """Get overall risk level for an agent (high/medium/low).

    The overall risk is the highest risk level among all tools.

    Args:
        agent_path: Path to the agent markdown file

    Returns:
        Overall risk level: "high", "medium", or "low"
    """
    try:
        tools = parse_agent_tools(agent_path)
        if not tools:
            return "low"

        permissions = analyze_tool_permissions(tools)

        # Find highest risk level
        risk_priority = {"high": 3, "medium": 2, "low": 1}
        max_risk = max((risk_priority.get(p.risk_level, 1) for p in permissions), default=1)

        for level, priority in risk_priority.items():
            if priority == max_risk:
                return level

        return "low"
    except (ValueError, Exception):
        return "unknown"


def generate_permissions_report(plugin_dir: Path) -> dict[str, Any]:
    """Generate full permissions report for all agents.

    Args:
        plugin_dir: Path to the plugin directory containing agents

    Returns:
        Dictionary containing comprehensive permissions report
    """
    agents_dir = plugin_dir / "agents"

    if not agents_dir.exists():
        return {
            "error": f"Agents directory not found: {agents_dir}",
            "agents": [],
            "summary": {},
        }

    agent_files = sorted(agents_dir.glob("*.md"))
    report = {
        "plugin_dir": str(plugin_dir),
        "total_agents": len(agent_files),
        "agents": [],
        "summary": {"high": 0, "medium": 0, "low": 0, "unknown": 0},
    }

    for agent_file in agent_files:
        try:
            tools = parse_agent_tools(agent_file)
            permissions = analyze_tool_permissions(tools)
            risk_level = get_agent_risk_level(agent_file)

            # Extract agent name from frontmatter
            content = agent_file.read_text(encoding="utf-8")
            frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            agent_name = agent_file.stem

            if frontmatter_match:
                try:
                    frontmatter = yaml.safe_load(frontmatter_match.group(1))
                    agent_name = frontmatter.get("name", agent_file.stem)
                except yaml.YAMLError:
                    pass

            agent_data = {
                "name": agent_name,
                "file": agent_file.name,
                "risk_level": risk_level,
                "tools": tools,
                "permissions": [
                    {
                        "tool": p.tool_name,
                        "risk": p.risk_level,
                        "description": p.description,
                    }
                    for p in permissions
                ],
            }

            report["agents"].append(agent_data)
            report["summary"][risk_level] = report["summary"].get(risk_level, 0) + 1

        except Exception as e:
            report["agents"].append(
                {
                    "name": agent_file.stem,
                    "file": agent_file.name,
                    "risk_level": "unknown",
                    "error": str(e),
                }
            )
            report["summary"]["unknown"] = report["summary"].get("unknown", 0) + 1

    return report


def get_high_risk_agents(plugin_dir: Path) -> list[dict[str, Any]]:
    """Get list of agents with high-risk tool permissions.

    Args:
        plugin_dir: Path to the plugin directory containing agents

    Returns:
        List of high-risk agent information
    """
    report = generate_permissions_report(plugin_dir)
    return [agent for agent in report["agents"] if agent.get("risk_level") == "high"]


def get_agent_permissions(agent_path: Path) -> dict[str, Any]:
    """Get detailed permission information for a specific agent.

    Args:
        agent_path: Path to the agent markdown file

    Returns:
        Dictionary containing agent permission details
    """
    try:
        tools = parse_agent_tools(agent_path)
        permissions = analyze_tool_permissions(tools)
        risk_level = get_agent_risk_level(agent_path)

        # Extract metadata from frontmatter
        content = agent_path.read_text(encoding="utf-8")
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)

        metadata = {"name": agent_path.stem, "description": ""}

        if frontmatter_match:
            try:
                frontmatter = yaml.safe_load(frontmatter_match.group(1))
                metadata["name"] = frontmatter.get("name", agent_path.stem)
                metadata["description"] = frontmatter.get("description", "")
            except yaml.YAMLError:
                pass

        return {
            "name": metadata["name"],
            "description": metadata["description"],
            "file": str(agent_path),
            "risk_level": risk_level,
            "tools": tools,
            "permissions": [
                {
                    "tool": p.tool_name,
                    "pattern": p.pattern,
                    "risk": p.risk_level,
                    "description": p.description,
                }
                for p in permissions
            ],
            "high_risk_tools": [
                p.tool_name for p in permissions if p.risk_level == "high"
            ],
            "medium_risk_tools": [
                p.tool_name for p in permissions if p.risk_level == "medium"
            ],
        }
    except Exception as e:
        return {
            "name": agent_path.stem,
            "file": str(agent_path),
            "risk_level": "unknown",
            "error": str(e),
        }
