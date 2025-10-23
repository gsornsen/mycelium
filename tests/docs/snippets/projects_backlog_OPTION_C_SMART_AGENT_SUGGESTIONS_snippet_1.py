# Source: projects/backlog/OPTION_C_SMART_AGENT_SUGGESTIONS.md
# Line: 112
# Valid syntax: True
# Has imports: True
# Has assignments: True

"""Context extraction from files, git, and user queries.

Analyzes working directory context to extract relevant keywords for
agent recommendation. Supports file type detection, git branch/commit
parsing, and NLP-based query understanding.

Author: @claude-code-developer + @ml-engineer
Date: 2025-10-18
"""

import re
import subprocess
from pathlib import Path


class ContextExtractor:
    """Extracts context keywords from environment.

    Analyzes open files, git state, and user queries to build a semantic
    context vector for agent recommendation.

    Example:
        >>> extractor = ContextExtractor()
        >>> context = extractor.extract_from_files([Path("src/components/Button.tsx")])
        >>> "react" in context
        True
        >>> "typescript" in context
        True
    """

    # File extension → keyword mapping
    FILE_TYPE_KEYWORDS = {
        # Frontend
        ".tsx": ["react", "typescript", "frontend", "component"],
        ".jsx": ["react", "javascript", "frontend", "component"],
        ".ts": ["typescript", "javascript"],
        ".js": ["javascript"],
        ".vue": ["vue", "frontend", "component"],
        ".svelte": ["svelte", "frontend", "component"],
        ".css": ["css", "styling", "frontend"],
        ".scss": ["sass", "css", "styling", "frontend"],
        ".html": ["html", "frontend", "markup"],

        # Backend
        ".py": ["python", "backend"],
        ".go": ["golang", "backend"],
        ".rs": ["rust", "backend"],
        ".java": ["java", "backend"],
        ".rb": ["ruby", "backend"],
        ".php": ["php", "backend"],

        # Infrastructure
        ".yaml": ["yaml", "config", "infrastructure"],
        ".yml": ["yaml", "config", "infrastructure"],
        ".toml": ["toml", "config"],
        ".json": ["json", "config"],
        ".dockerfile": ["docker", "container", "infrastructure"],
        "Dockerfile": ["docker", "container", "infrastructure"],
        "docker-compose.yml": ["docker", "compose", "infrastructure"],

        # Data
        ".sql": ["sql", "database", "data"],
        ".graphql": ["graphql", "api", "data"],
        ".proto": ["protobuf", "grpc", "api"],

        # ML/AI
        ".ipynb": ["jupyter", "python", "data-science", "ml"],
        ".pkl": ["python", "ml", "model"],
        ".h5": ["keras", "tensorflow", "ml"],
        ".pt": ["pytorch", "ml"],

        # Documentation
        ".md": ["documentation", "markdown"],
        ".rst": ["documentation", "restructuredtext"],
        ".tex": ["latex", "documentation"],

        # Testing
        "test_*.py": ["testing", "pytest", "python"],
        "*_test.go": ["testing", "golang"],
        "*.test.ts": ["testing", "typescript", "jest"],
        "*.spec.ts": ["testing", "typescript", "jest"],
    }

    # Directory name → keyword mapping
    DIR_KEYWORDS = {
        "src": ["source", "code"],
        "tests": ["testing", "quality"],
        "docs": ["documentation"],
        "frontend": ["frontend", "ui"],
        "backend": ["backend", "api"],
        "api": ["api", "backend"],
        "components": ["react", "vue", "component", "frontend"],
        "services": ["backend", "service"],
        "models": ["data", "database", "ml"],
        "utils": ["utility", "helper"],
        "config": ["configuration", "settings"],
        "scripts": ["automation", "tooling"],
        "infra": ["infrastructure", "devops"],
        "infrastructure": ["infrastructure", "devops"],
        ".github": ["ci-cd", "github", "automation"],
        ".gitlab": ["ci-cd", "gitlab", "automation"],
    }

    def extract_from_files(self, file_paths: list[Path]) -> str:
        """Extract keywords from open files.

        Analyzes file extensions and directory names to infer context.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            Space-separated keyword string

        Example:
            >>> extractor = ContextExtractor()
            >>> context = extractor.extract_from_files([
            ...     Path("src/components/Button.tsx"),
            ...     Path("tests/unit/test_button.py")
            ... ])
            >>> "react" in context and "testing" in context
            True
        """
        keywords = set()

        for path in file_paths:
            # Extract from file extension
            suffix = path.suffix.lower()
            if suffix in self.FILE_TYPE_KEYWORDS:
                keywords.update(self.FILE_TYPE_KEYWORDS[suffix])

            # Special case: full filename patterns
            filename = path.name
            if filename.startswith("test_") or filename.endswith("_test.py"):
                keywords.update(["testing", "pytest", "python"])
            if filename == "Dockerfile":
                keywords.update(["docker", "container", "infrastructure"])

            # Extract from directory names
            for part in path.parts:
                part_lower = part.lower()
                if part_lower in self.DIR_KEYWORDS:
                    keywords.update(self.DIR_KEYWORDS[part_lower])

        return " ".join(keywords)

    def extract_from_git(self) -> str:
        """Extract context from git branch and recent commits.

        Parses branch name and commit messages for semantic keywords.

        Returns:
            Space-separated keyword string

        Example:
            >>> extractor = ContextExtractor()
            >>> context = extractor.extract_from_git()
            >>> len(context) > 0  # May be empty if not in git repo
            True
        """
        keywords = set()

        try:
            # Get current branch name
            branch = subprocess.check_output(
                ["git", "branch", "--show-current"],
                stderr=subprocess.DEVNULL
            ).decode().strip()

            # Parse branch name (e.g., feat/api-redesign → api, redesign)
            branch_keywords = re.findall(r'[a-z]+', branch.lower())
            keywords.update(branch_keywords)

            # Get recent commit messages (last 5)
            commits = subprocess.check_output(
                ["git", "log", "--oneline", "-5"],
                stderr=subprocess.DEVNULL
            ).decode().strip().split('\n')

            for commit in commits:
                # Extract words from commit message
                commit_words = re.findall(r'[a-z]{3,}', commit.lower())
                keywords.update(commit_words)

        except (subprocess.CalledProcessError, FileNotFoundError):
            # Not a git repo or git not available
            pass

        return " ".join(keywords)

    def extract_from_query(self, query: str) -> str:
        """Extract keywords from user query using NLP.

        Uses simple word extraction for now. Can be enhanced with spaCy
        for entity recognition and keyword extraction.

        Args:
            query: User's natural language query

        Returns:
            Space-separated keyword string

        Example:
            >>> extractor = ContextExtractor()
            >>> context = extractor.extract_from_query("help with react components")
            >>> "react" in context and "components" in context
            True
        """
        # Simple approach: extract alphanumeric words
        keywords = re.findall(r'\b[a-z]{3,}\b', query.lower())

        # TODO: Enhance with spaCy for:
        # - Named entity recognition
        # - Keyword extraction (RAKE, TF-IDF)
        # - Synonym expansion

        return " ".join(keywords)

    def extract_full_context(
        self,
        query: str | None = None,
        file_paths: list[Path] | None = None,
        include_git: bool = True
    ) -> str:
        """Extract comprehensive context from all sources.

        Combines query, file, and git context into single keyword string.

        Args:
            query: Optional user query
            file_paths: Optional file paths
            include_git: Whether to include git context

        Returns:
            Combined keyword string

        Example:
            >>> extractor = ContextExtractor()
            >>> context = extractor.extract_full_context(
            ...     query="optimize database queries",
            ...     file_paths=[Path("src/models/user.py")]
            ... )
            >>> "database" in context and "python" in context
            True
        """
        all_keywords = []

        if query:
            all_keywords.append(self.extract_from_query(query))

        if file_paths:
            all_keywords.append(self.extract_from_files(file_paths))

        if include_git:
            all_keywords.append(self.extract_from_git())

        # Combine and deduplicate
        combined = " ".join(all_keywords)
        unique_keywords = list(dict.fromkeys(combined.split()))  # Preserve order

        return " ".join(unique_keywords)
