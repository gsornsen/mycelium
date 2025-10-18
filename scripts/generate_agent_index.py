#!/usr/bin/env python3
"""Generate agent metadata index from markdown agent files.

This script parses all agent markdown files in the plugins/mycelium-core/agents/ directory,
extracts metadata, estimates token counts, and generates a JSON index
for efficient agent discovery and selection.

Usage:
    python scripts/generate_agent_index.py
    python scripts/generate_agent_index.py --output custom-path/index.json
    python scripts/generate_agent_index.py --validate-only
"""

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class AgentMetadata:
    """Metadata for a single agent."""

    id: str
    name: str
    display_name: str
    category: str
    description: str
    tools: list[str]
    keywords: list[str]
    file_path: str
    estimated_tokens: int


class AgentIndexGenerator:
    """Generator for agent metadata index."""

    # Category mapping (filename prefix -> category name)
    CATEGORIES = {
        "01-core": "Core Development",
        "02-language": "Language Specialists",
        "03-infrastructure": "Infrastructure",
        "03-project": "Project Management",
        "04-quality": "Quality & Security",
        "05-data": "Data & AI",
        "06-developer": "Developer Experience",
        "07-specialized": "Specialized Domains",
        "08-business": "Business & Product",
        "09-meta": "Meta-Orchestration",
        "10-research": "Research & Analysis",
        "11-claude": "Claude Code",
    }

    # Common words to exclude from keywords
    STOP_WORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
        "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
        "to", "was", "will", "with", "you", "your", "when", "working",
        "invoke", "expert", "specialist", "senior", "agent", "mycelium",
        "focus", "ensuring", "emphasis"
    }

    def __init__(self, agents_dir: Path, output_path: Path):
        """Initialize generator.

        Args:
            agents_dir: Path to agents directory
            output_path: Path to output index.json file
        """
        self.agents_dir = agents_dir
        self.output_path = output_path
        self.agents: list[AgentMetadata] = []

    def parse_agent_file(self, file_path: Path) -> AgentMetadata | None:
        """Parse a single agent markdown file.

        Args:
            file_path: Path to agent markdown file

        Returns:
            AgentMetadata or None if parsing fails
        """
        try:
            content = file_path.read_text(encoding='utf-8')

            # Extract YAML frontmatter
            frontmatter_match = re.search(
                r'^---\s*\n(.*?)\n---\s*\n',
                content,
                re.MULTILINE | re.DOTALL
            )

            if not frontmatter_match:
                print(f"Warning: No frontmatter in {file_path}", file=sys.stderr)
                return None

            frontmatter = frontmatter_match.group(1)
            body = content[frontmatter_match.end():]

            # Parse frontmatter fields
            name = self._extract_field(frontmatter, 'name')
            description = self._extract_field(frontmatter, 'description')
            tools_str = self._extract_field(frontmatter, 'tools')

            if not name or not description:
                print(f"Warning: Missing name or description in {file_path}", file=sys.stderr)
                return None

            # Parse tools
            tools = self._parse_tools(tools_str) if tools_str else []

            # Extract category from filename prefix
            category = self._extract_category_from_filename(file_path.name)

            # Generate unique ID from filename (without .md extension)
            # This ensures uniqueness even if frontmatter names are duplicated
            unique_id = file_path.stem  # e.g., "01-core-wordpress-master"

            # Generate display name (convert kebab-case to Title Case)
            display_name = self._generate_display_name(name)

            # Extract keywords from content
            keywords = self._extract_keywords(description, body)

            # Estimate token count (rough approximation: words / 0.75)
            token_count = self._estimate_tokens(content)

            # Get relative file path from repository root
            # For flat structure: plugins/mycelium-core/agents/filename.md
            try:
                relative_path = str(file_path.relative_to(self.agents_dir.parent.parent.parent))
            except ValueError:
                # Fallback for test files outside repository
                relative_path = str(file_path)

            return AgentMetadata(
                id=unique_id,  # Use filename-based ID for uniqueness
                name=name,
                display_name=display_name,
                category=category,
                description=description.strip(),
                tools=tools,
                keywords=keywords,
                file_path=relative_path,
                estimated_tokens=token_count
            )

        except Exception as e:
            print(f"Error parsing {file_path}: {e}", file=sys.stderr)
            return None

    def _extract_field(self, frontmatter: str, field: str) -> str | None:
        """Extract a field from YAML frontmatter."""
        pattern = rf'^{field}:\s*(.+)$'
        match = re.search(pattern, frontmatter, re.MULTILINE)
        return match.group(1).strip() if match else None

    def _parse_tools(self, tools_str: str) -> list[str]:
        """Parse tools string into list."""
        # Handle both comma-separated and other formats
        tools = [t.strip() for t in re.split(r'[,\s]+', tools_str)]
        # Remove empty strings and normalize
        tools = [t for t in tools if t and t != '-']
        return sorted(set(tools))

    def _extract_category_from_filename(self, filename: str) -> str:
        """Extract category from filename prefix.

        Example: '09-meta-multi-agent-coordinator.md' -> 'Meta-Orchestration'
        """
        # Extract prefix (e.g., '09-meta' from '09-meta-multi-agent-coordinator.md')
        match = re.match(r'^(\d{2}-\w+)-', filename)
        if not match:
            return "Unknown"

        prefix = match.group(1)
        return self.CATEGORIES.get(prefix, "Unknown")

    def _generate_display_name(self, name: str) -> str:
        """Generate display name from agent name."""
        # Convert kebab-case to Title Case
        words = name.replace('-', ' ').split()
        return ' '.join(word.capitalize() for word in words)

    def _extract_keywords(self, description: str, body: str) -> list[str]:
        """Extract keywords from description and body."""
        # Combine description and first 500 chars of body
        text = description + ' ' + body[:500]

        # Convert to lowercase and extract words
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())

        # Filter out stop words and get unique keywords
        keywords = {w for w in words if w not in self.STOP_WORDS}

        # Return top 15 most common keywords (sorted alphabetically)
        return sorted(keywords)[:15]

    def _estimate_tokens(self, content: str) -> int:
        """Estimate token count (rough approximation)."""
        # Count words (split on whitespace)
        word_count = len(content.split())

        # Rough approximation: 1 token ≈ 0.75 words
        # Add overhead for markdown formatting
        estimated_tokens = int(word_count / 0.75) + 50

        return estimated_tokens

    def scan_agents(self) -> None:
        """Scan all agent markdown files."""
        agent_files = sorted(self.agents_dir.glob('*.md'))

        print(f"Scanning {len(agent_files)} agent files in {self.agents_dir}...")

        for agent_file in agent_files:
            metadata = self.parse_agent_file(agent_file)
            if metadata:
                self.agents.append(metadata)

        print(f"Successfully parsed {len(self.agents)} agents")

    def generate_index(self) -> dict[str, Any]:
        """Generate index structure."""
        # Group agents by category
        categories = sorted(set(agent.category for agent in self.agents))

        return {
            "version": "1.0.0",
            "generated": datetime.now(timezone.utc).isoformat(),
            "agent_count": len(self.agents),
            "categories": categories,
            "agents": [asdict(agent) for agent in sorted(self.agents, key=lambda a: a.id)]
        }

    def validate_index(self, index: dict[str, Any]) -> bool:
        """Validate generated index."""
        errors = []

        # Check required fields
        if index.get("version") != "1.0.0":
            errors.append("Invalid version")

        if index.get("agent_count") != len(self.agents):
            errors.append(f"Agent count mismatch: {index.get('agent_count')} != {len(self.agents)}")

        # Validate each agent
        agent_ids: set[str] = set()
        for agent_data in index.get("agents", []):
            # Check for duplicates
            agent_id = agent_data.get("id")
            if agent_id in agent_ids:
                errors.append(f"Duplicate agent ID: {agent_id}")
            agent_ids.add(agent_id)

            # Check required fields
            required_fields = ["id", "name", "display_name", "category", "description", "file_path"]
            for field in required_fields:
                if not agent_data.get(field):
                    errors.append(f"Agent {agent_id} missing field: {field}")

            # Check tools is a list
            if not isinstance(agent_data.get("tools", []), list):
                errors.append(f"Agent {agent_id} tools is not a list")

            # Check estimated_tokens is positive
            if agent_data.get("estimated_tokens", 0) <= 0:
                errors.append(f"Agent {agent_id} has invalid token count")

        if errors:
            print("Validation errors:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            return False

        print("Index validation passed ✓")
        return True

    def write_index(self, index: dict[str, Any]) -> None:
        """Write index to JSON file."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        print(f"Index written to {self.output_path}")
        print(f"  - {index['agent_count']} agents indexed")
        print(f"  - {len(index['categories'])} categories")

    def run(self, validate_only: bool = False) -> bool:
        """Run the index generation process.

        Args:
            validate_only: If True, only validate existing index

        Returns:
            True if successful, False otherwise
        """
        if validate_only:
            if not self.output_path.exists():
                print(f"Error: Index file not found: {self.output_path}", file=sys.stderr)
                return False

            with open(self.output_path, encoding='utf-8') as f:
                index = json.load(f)

            # Still need to scan agents for validation
            self.scan_agents()
            return self.validate_index(index)

        # Generate new index
        self.scan_agents()
        index = self.generate_index()

        if not self.validate_index(index):
            return False

        self.write_index(index)
        return True


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate agent metadata index from markdown files"
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('plugins/mycelium-core/agents/index.json'),
        help='Output path for index.json (default: plugins/mycelium-core/agents/index.json)'
    )
    parser.add_argument(
        '--agents-dir',
        type=Path,
        default=Path('plugins/mycelium-core/agents'),
        help='Path to agents directory (default: plugins/mycelium-core/agents/)'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate existing index, do not regenerate'
    )

    args = parser.parse_args()

    # Resolve paths relative to repository root
    repo_root = Path(__file__).parent.parent
    agents_dir = repo_root / args.agents_dir
    output_path = repo_root / args.output

    if not agents_dir.exists():
        print(f"Error: Agents directory not found: {agents_dir}", file=sys.stderr)
        sys.exit(1)

    generator = AgentIndexGenerator(agents_dir, output_path)
    success = generator.run(validate_only=args.validate_only)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
