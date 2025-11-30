"""Agent configuration loader.

Parses agent .md files to extract execution configuration.
"""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentConfig:
    """Agent configuration from .md file.

    Attributes:
        name: Agent name identifier
        category: Agent category (core, language, specialized, etc.)
        description: Agent description
        command: Command to execute agent
        env: Environment variables for agent
        workdir: Working directory for agent
        tools: List of tools available to agent
    """

    name: str
    category: str
    description: str
    command: list[str]
    env: dict[str, str] | None = None
    workdir: Path | None = None
    tools: list[str] | None = None

    @classmethod
    def from_file(cls, path: Path) -> "AgentConfig":
        """Load agent config from .md file.

        Args:
            path: Path to agent .md file

        Returns:
            Parsed agent configuration

        Raises:
            ValueError: If file format is invalid
        """
        if not path.exists():
            msg = f"Agent file not found: {path}"
            raise ValueError(msg)

        content = path.read_text(encoding="utf-8")

        # Extract frontmatter (YAML between --- markers)
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)

        if not frontmatter_match:
            msg = f"No frontmatter found in {path}"
            raise ValueError(msg)

        frontmatter = frontmatter_match.group(1)

        # Parse frontmatter fields
        name = cls._extract_field(frontmatter, "name")
        if not name:
            # Fall back to filename without prefix and extension
            name = cls._clean_filename(path.stem)

        description = cls._extract_field(frontmatter, "description", "")
        tools_str = cls._extract_field(frontmatter, "tools", "")
        tools = [t.strip() for t in tools_str.split(",")] if tools_str else None

        # Determine category from filename prefix
        category = cls._extract_category(path.stem)

        # Default command pattern
        command = ["claude", "--agent", name]

        # Check for Execution section in content
        execution_section = cls._extract_execution_section(content)
        if execution_section:
            # Parse custom command if specified
            command_match = re.search(r"command:\s*(.+)", execution_section)
            if command_match:
                command = [c.strip() for c in command_match.group(1).split()]

        return cls(
            name=name,
            category=category,
            description=description,
            command=command,
            env=None,  # Could be extracted from Execution section if needed
            workdir=None,  # Could be extracted from Execution section if needed
            tools=tools,
        )

    @staticmethod
    def _extract_field(frontmatter: str, field: str, default: str = "") -> str:
        """Extract field from frontmatter.

        Args:
            frontmatter: YAML frontmatter content
            field: Field name to extract
            default: Default value if field not found

        Returns:
            Field value or default
        """
        match = re.search(rf"^{field}:\s*(.+)$", frontmatter, re.MULTILINE)
        return match.group(1).strip() if match else default

    @staticmethod
    def _clean_filename(filename: str) -> str:
        """Clean filename to extract agent name.

        Removes numeric prefixes and category prefixes.

        Args:
            filename: Filename without extension

        Returns:
            Cleaned agent name
        """
        # Remove patterns like "01-core-", "02-language-", etc.
        return re.sub(r"^\d+-(?:core|language|specialized|framework)-", "", filename)

    @staticmethod
    def _extract_category(filename: str) -> str:
        """Extract category from filename prefix.

        Args:
            filename: Filename without extension

        Returns:
            Category name (core, language, specialized, framework, etc.)
        """
        match = re.match(r"^\d+-([a-z]+)-", filename)
        return match.group(1) if match else "unknown"

    @staticmethod
    def _extract_execution_section(content: str) -> str | None:
        """Extract Execution section from content.

        Args:
            content: Full markdown content

        Returns:
            Execution section content or None
        """
        match = re.search(r"## Execution\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
        return match.group(1).strip() if match else None


class AgentLoader:
    """Load agent configurations from plugin directory."""

    def __init__(self, plugin_dir: Path) -> None:
        """Initialize loader.

        Args:
            plugin_dir: Directory containing agent .md files
        """
        self.plugin_dir = plugin_dir

    def load_agent(self, name: str) -> AgentConfig | None:
        """Load specific agent configuration.

        Args:
            name: Agent name (can be full filename like '05-data-python-pro'
                  or short name like 'python-pro')

        Returns:
            Agent config or None if not found
        """
        if not self.plugin_dir.exists():
            return None

        # Try exact filename match first (e.g., "05-data-python-pro.md")
        exact_path = self.plugin_dir / f"{name}.md"
        if exact_path.exists():
            try:
                return AgentConfig.from_file(exact_path)
            except ValueError:
                pass

        # Search for matching .md file by cleaned name
        for md_file in self.plugin_dir.glob("*.md"):
            try:
                config = AgentConfig.from_file(md_file)
                # Match against cleaned name OR full filename stem
                if config.name == name or md_file.stem == name:
                    return config
            except ValueError:
                # Skip invalid files
                continue

        return None

    def list_agents(self) -> list[AgentConfig]:
        """List all available agent configurations.

        Returns:
            List of agent configs
        """
        agents: list[AgentConfig] = []

        if not self.plugin_dir.exists():
            return agents

        # Scan all .md files
        for md_file in sorted(self.plugin_dir.glob("*.md")):
            try:
                config = AgentConfig.from_file(md_file)
                agents.append(config)
            except ValueError:
                # Skip invalid files
                continue

        return agents

    def list_by_category(self, category: str) -> list[AgentConfig]:
        """List agents filtered by category.

        Args:
            category: Category to filter by

        Returns:
            List of agent configs in category
        """
        all_agents = self.list_agents()
        return [agent for agent in all_agents if agent.category == category]

    def get_categories(self) -> list[str]:
        """Get list of all categories.

        Returns:
            List of unique category names
        """
        all_agents = self.list_agents()
        categories = {agent.category for agent in all_agents}
        return sorted(categories)
