"""Agent discovery scanner.

Scans plugin directories for agent definitions and registers
them in the agent registry.
"""

import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from mycelium.errors import MyceliumError
from mycelium.registry.client import RegistryClient, AgentInfo


@dataclass
class DiscoveredAgent:
    """Discovered agent metadata."""

    name: str
    category: str
    description: str
    file_path: Path
    version: Optional[str] = None
    capabilities: Optional[list[str]] = None


class AgentScanner:
    """Scan directories for agent definitions.

    Discovers agents from Markdown files in plugin directories.
    Expected format:
    - File name: {agent-name}.md
    - Contains category, description in frontmatter or content
    """

    def __init__(self, registry: Optional[RegistryClient] = None):
        """Initialize agent scanner.

        Args:
            registry: Optional registry client for auto-registration
        """
        self.registry = registry or RegistryClient()
        self.discovered: dict[str, DiscoveredAgent] = {}

    def scan_directory(self, directory: Path, recursive: bool = True) -> list[DiscoveredAgent]:
        """Scan directory for agent definitions.

        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories

        Returns:
            List of discovered agents
        """
        if not directory.exists():
            raise MyceliumError(
                f"Agent directory not found: {directory}",
                suggestion="Check your plugin directory configuration",
                docs_url="https://docs.mycelium.dev/plugins/structure",
                debug_info={"directory": str(directory)}
            )

        discovered = []
        pattern = "**/*.md" if recursive else "*.md"

        for agent_file in directory.glob(pattern):
            try:
                agent = self._parse_agent_file(agent_file)
                if agent:
                    discovered.append(agent)
                    self.discovered[agent.name] = agent
            except Exception as e:
                # Log warning but continue scanning
                print(f"Warning: Failed to parse {agent_file}: {e}")
                continue

        return discovered

    def _parse_agent_file(self, file_path: Path) -> Optional[DiscoveredAgent]:
        """Parse agent definition from Markdown file.

        Args:
            file_path: Path to agent definition file

        Returns:
            Discovered agent or None if invalid
        """
        content = file_path.read_text(encoding="utf-8")

        # Extract agent name from filename
        # e.g., backend-developer.md -> backend-developer
        name = file_path.stem

        # Skip if not an agent definition
        if not self._is_agent_file(content, name):
            return None

        # Parse metadata from content
        category = self._extract_category(content, file_path.stem)
        description = self._extract_description(content)

        if not category or not description:
            # Not a valid agent definition
            return None

        return DiscoveredAgent(
            name=name,
            category=category,
            description=description,
            file_path=file_path,
        )

    def _is_agent_file(self, content: str, name: str) -> bool:
        """Check if file is an agent definition.

        Args:
            content: File content
            name: File name (stem)

        Returns:
            True if this is an agent definition
        """
        # Check for YAML frontmatter with name/description (standard agent format)
        has_frontmatter = content.strip().startswith("---")
        if has_frontmatter:
            # Look for standard agent frontmatter fields
            lower_content = content.lower()
            if "name:" in lower_content and "description:" in lower_content:
                return True

        # Fallback: check for agent-related keywords in content
        lower_content = content.lower()
        return any(
            keyword in lower_content
            for keyword in ["category:", "agent:", "role:", "specialist", "tools:"]
        )

    def _extract_category(self, content: str, filename: str = "") -> str:
        """Extract category from agent definition.

        Args:
            content: File content
            filename: Filename stem (without extension)

        Returns:
            Category string or "unknown"
        """
        # First priority: Extract from filename prefix pattern (NN-category-name)
        # e.g., "01-core-backend-developer" -> "core"
        # e.g., "05-data-ml-engineer" -> "data"
        if filename:
            filename_match = re.match(r"^\d+-([a-z]+)-", filename)
            if filename_match:
                return filename_match.group(1)

        # Try YAML frontmatter
        frontmatter_match = re.search(r"^---\s*\n(.+?)\n---", content, re.DOTALL | re.MULTILINE)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            category_match = re.search(r"category:\s*['\"]?(.+?)['\"]?\s*$", frontmatter, re.MULTILINE)
            if category_match:
                return category_match.group(1).strip()

        # Try inline category marker
        category_match = re.search(r"(?:Category|category):\s*\*\*(.+?)\*\*", content)
        if category_match:
            return category_match.group(1).strip()

        # Try category in header
        category_match = re.search(r"##\s*Category:\s*(.+)", content)
        if category_match:
            return category_match.group(1).strip()

        # Default categories based on content patterns
        content_lower = content.lower()
        if "backend" in content_lower:
            return "backend"
        elif "frontend" in content_lower:
            return "frontend"
        elif "devops" in content_lower or "infrastructure" in content_lower:
            return "infrastructure"
        elif "test" in content_lower or "qa" in content_lower:
            return "testing"
        elif "security" in content_lower:
            return "security"
        elif "documentation" in content_lower or "docs" in content_lower:
            return "documentation"

        return "general"

    def _extract_description(self, content: str) -> str:
        """Extract description from agent definition.

        Args:
            content: File content

        Returns:
            Description string
        """
        # Try YAML frontmatter first
        frontmatter_match = re.search(r"^---\s*\n(.+?)\n---", content, re.DOTALL | re.MULTILINE)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            desc_match = re.search(r"description:\s*['\"]?(.+?)['\"]?\s*$", frontmatter, re.MULTILINE)
            if desc_match:
                return desc_match.group(1).strip()

        # Try first paragraph after title/frontmatter
        lines = content.split("\n")
        in_frontmatter = False
        past_frontmatter = False

        for line in lines:
            stripped = line.strip()

            # Handle frontmatter boundaries
            if stripped == "---":
                if not in_frontmatter:
                    in_frontmatter = True
                else:
                    in_frontmatter = False
                    past_frontmatter = True
                continue

            # Skip if inside frontmatter
            if in_frontmatter:
                continue

            # Skip headers
            if stripped.startswith("#"):
                continue

            # Return first non-empty line of actual content
            if stripped:
                # Clean up markdown formatting
                description = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
                description = re.sub(r"\*(.+?)\*", r"\1", description)
                return description[:200]  # Limit length

        return "Agent specialist"

    def register_discovered_agents(self) -> int:
        """Register all discovered agents in the registry.

        Returns:
            Number of agents registered
        """
        count = 0
        for agent in self.discovered.values():
            try:
                self.registry.register_agent(
                    name=agent.name,
                    category=agent.category,
                    description=agent.description,
                )
                count += 1
            except Exception as e:
                print(f"Warning: Failed to register {agent.name}: {e}")
                continue

        return count

    def get_discovered_agent(self, name: str) -> Optional[DiscoveredAgent]:
        """Get discovered agent by name.

        Args:
            name: Agent name

        Returns:
            Discovered agent or None
        """
        return self.discovered.get(name)
