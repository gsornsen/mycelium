# Source: projects/backlog/OPTION_B_AGENT_PROMPT_OPTIMIZATION.md
# Line: 880
# Valid syntax: True
# Has imports: True
# Has assignments: True

"""Prompt optimization engine with template application and A/B testing.

Applies optimization templates to improve prompt quality based on rubric
analysis. Supports batch optimization and A/B testing of improvements.

Author: @claude-code-developer + @documentation-engineer
Date: 2025-10-18
"""

from pathlib import Path
from typing import Any
import re


class PromptOptimizer:
    """Optimizes agent prompts using templates and best practices.

    Provides methods to apply standard templates, optimize for tokens,
    suggest improvements, and A/B test changes.

    Attributes:
        analyzer: PromptAnalyzer for quality assessment
        template_dir: Directory containing optimization templates

    Example:
        >>> optimizer = PromptOptimizer()
        >>> suggestions = optimizer.suggest_improvements("agents/01-api-designer.md")
        >>> len(suggestions) > 0
        True
    """

    def __init__(
        self,
        analyzer: 'PromptAnalyzer',
        template_dir: Path | None = None
    ):
        """Initialize optimizer.

        Args:
            analyzer: PromptAnalyzer instance
            template_dir: Directory with templates (default: templates/prompts/)
        """
        self.analyzer = analyzer
        self.template_dir = template_dir or Path("templates/prompts")

    def suggest_improvements(
        self,
        prompt_path: Path,
        agent_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Analyze prompt and suggest specific improvements.

        Args:
            prompt_path: Path to agent markdown file
            agent_id: Optional agent ID for analytics

        Returns:
            List of improvement suggestions:
            [
                {
                    "category": "clarity",
                    "issue": "Low readability score (45/100)",
                    "suggestion": "Simplify sentence structure",
                    "priority": "high",
                    "estimated_impact": "+10 points"
                },
                ...
            ]

        Example:
            >>> optimizer = PromptOptimizer(PromptAnalyzer())
            >>> suggestions = optimizer.suggest_improvements(Path("agents/01-api-designer.md"))
            >>> all('priority' in s for s in suggestions)
            True
        """
        analysis = self.analyzer.analyze_prompt(prompt_path, agent_id)
        suggestions = []

        # Analyze each criterion
        for criterion_name, criterion_data in analysis['criteria_scores'].items():
            score = criterion_data['score']

            if score < 70:
                # High priority improvement needed
                suggestions.append({
                    "category": criterion_name,
                    "issue": f"Low {criterion_name} score ({score:.1f}/100)",
                    "suggestion": self._get_criterion_suggestion(criterion_name, criterion_data),
                    "priority": "high",
                    "estimated_impact": f"+{100 - score:.0f} points",
                })
            elif score < 85:
                # Medium priority
                suggestions.append({
                    "category": criterion_name,
                    "issue": f"{criterion_name.capitalize()} could be improved ({score:.1f}/100)",
                    "suggestion": self._get_criterion_suggestion(criterion_name, criterion_data),
                    "priority": "medium",
                    "estimated_impact": f"+{100 - score:.0f} points",
                })

        return suggestions

    def apply_template(
        self,
        prompt_path: Path,
        template_name: str = "standard_agent_template.md"
    ) -> str:
        """Apply standard template to agent prompt.

        Args:
            prompt_path: Path to existing agent file
            template_name: Template file name

        Returns:
            Optimized prompt content

        Example:
            >>> optimizer = PromptOptimizer(PromptAnalyzer())
            >>> optimized = optimizer.apply_template(Path("agents/01-api-designer.md"))
            >>> "## Your Role" in optimized
            True
        """
        # Load template
        template_path = self.template_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        template = template_path.read_text(encoding='utf-8')

        # Extract existing content sections
        existing_content = prompt_path.read_text(encoding='utf-8')
        sections = self._extract_sections(existing_content)

        # Fill template with existing content
        optimized = template

        for section_name, section_content in sections.items():
            placeholder = f"{{{{ {section_name} }}}}"
            if placeholder in optimized:
                optimized = optimized.replace(placeholder, section_content)

        return optimized

    def optimize_for_tokens(
        self,
        prompt_path: Path,
        target_reduction: float = 0.20
    ) -> tuple[str, dict[str, Any]]:
        """Optimize prompt to reduce token count.

        Args:
            prompt_path: Path to agent file
            target_reduction: Target token reduction (0.20 = 20%)

        Returns:
            Tuple of (optimized_content, stats):
            - optimized_content: Reduced prompt
            - stats: {
                "original_tokens": 1200,
                "optimized_tokens": 960,
                "reduction_percentage": 20.0,
                "methods_applied": ["remove_redundancy", "shorten_examples"]
              }

        Example:
            >>> optimizer = PromptOptimizer(PromptAnalyzer())
            >>> content, stats = optimizer.optimize_for_tokens(Path("agents/verbose.md"))
            >>> stats['reduction_percentage'] > 0
            True
        """
        content = prompt_path.read_text(encoding='utf-8')
        original_tokens = len(content.split())

        methods_applied = []

        # Method 1: Remove redundant phrases
        content, reduced = self._remove_redundancy(content)
        if reduced:
            methods_applied.append("remove_redundancy")

        # Method 2: Shorten verbose examples
        content, reduced = self._shorten_examples(content)
        if reduced:
            methods_applied.append("shorten_examples")

        # Method 3: Consolidate bullet points
        content, reduced = self._consolidate_bullets(content)
        if reduced:
            methods_applied.append("consolidate_bullets")

        # Compute stats
        optimized_tokens = len(content.split())
        reduction_percentage = ((original_tokens - optimized_tokens) / original_tokens) * 100

        stats = {
            "original_tokens": original_tokens,
            "optimized_tokens": optimized_tokens,
            "reduction_percentage": round(reduction_percentage, 2),
            "methods_applied": methods_applied,
        }

        return content, stats

    def ab_test_versions(
        self,
        original_path: Path,
        optimized_path: Path,
        days: int = 14
    ) -> dict[str, Any]:
        """Compare original vs optimized prompt using analytics.

        Args:
            original_path: Path to original agent
            optimized_path: Path to optimized version
            days: Days to collect data

        Returns:
            A/B test results:
            {
                "original": {"score": 78.0, "usage": 42, "rating": 3.8},
                "optimized": {"score": 85.0, "usage": 56, "rating": 4.2},
                "improvement": {
                    "score_delta": +7.0,
                    "usage_delta": +33%,
                    "rating_delta": +0.4
                },
                "winner": "optimized"
            }

        Example:
            >>> optimizer = PromptOptimizer(PromptAnalyzer())
            >>> results = optimizer.ab_test_versions(
            ...     Path("agents/01-api-designer.md"),
            ...     Path("agents/01-api-designer-optimized.md"),
            ...     days=14
            ... )
            >>> results['winner'] in ['original', 'optimized', 'tie']
            True
        """
        # Analyze both versions
        original_analysis = self.analyzer.analyze_prompt(original_path)
        optimized_analysis = self.analyzer.analyze_prompt(optimized_path)

        # TODO: Collect real usage data over time period
        # For now, return analysis comparison

        original_score = original_analysis['total_score']
        optimized_score = optimized_analysis['total_score']

        score_delta = optimized_score - original_score

        winner = "tie"
        if score_delta > 5:
            winner = "optimized"
        elif score_delta < -5:
            winner = "original"

        return {
            "original": {
                "score": original_score,
                "grade": original_analysis['grade'],
            },
            "optimized": {
                "score": optimized_score,
                "grade": optimized_analysis['grade'],
            },
            "improvement": {
                "score_delta": round(score_delta, 2),
            },
            "winner": winner,
        }

    def _get_criterion_suggestion(
        self,
        criterion_name: str,
        criterion_data: dict
    ) -> str:
        """Generate specific suggestion for criterion improvement."""
        suggestions_map = {
            "clarity": "Simplify language, reduce jargon, shorten sentences",
            "specificity": "Add more concrete examples and code snippets",
            "consistency": "Follow standard template structure and tone guidelines",
            "effectiveness": "Gather user feedback to improve relevance",
            "constraints": "Explicitly state limitations and out-of-scope items",
        }
        return suggestions_map.get(criterion_name, "Review rubric for details")

    def _extract_sections(self, content: str) -> dict[str, str]:
        """Extract Markdown sections from content."""
        sections = {}
        pattern = r'^##\s+(.+?)\n+(.*?)(?=\n##|\Z)'
        matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)

        for match in matches:
            heading = match.group(1).strip()
            section_content = match.group(2).strip()
            sections[heading] = section_content

        return sections

    def _remove_redundancy(self, content: str) -> tuple[str, bool]:
        """Remove redundant phrases."""
        redundant_phrases = [
            r'\s+basically\s+',
            r'\s+essentially\s+',
            r'\s+in other words\s+',
            r'\s+as mentioned before\s+',
        ]

        modified = content
        for phrase in redundant_phrases:
            modified = re.sub(phrase, ' ', modified, flags=re.IGNORECASE)

        return modified, modified != content

    def _shorten_examples(self, content: str) -> tuple[str, bool]:
        """Shorten verbose examples (keep first 3 lines)."""
        # Find example blocks
        pattern = r'(Example:.*?)(?=\n##|\Z)'
        matches = re.finditer(pattern, content, re.DOTALL)

        modified = content
        for match in matches:
            example_block = match.group(1)
            lines = example_block.split('\n')
            if len(lines) > 5:
                # Keep first 3 lines + ellipsis
                shortened = '\n'.join(lines[:3]) + '\n    ...'
                modified = modified.replace(example_block, shortened)

        return modified, modified != content

    def _consolidate_bullets(self, content: str) -> tuple[str, bool]:
        """Consolidate related bullet points."""
        # Simple heuristic: if 3+ consecutive bullets start with same word, consolidate
        pattern = r'(^-\s+(\w+).*\n(?:-\s+\2.*\n){2,})'
        matches = re.finditer(pattern, content, re.MULTILINE)

        modified = content
        for match in matches:
            bullet_block = match.group(1)
            lines = bullet_block.strip().split('\n')
            first_word = match.group(2)

            # Consolidate to single bullet
            consolidated = f"- {first_word}: " + ", ".join(
                line.split(':', 1)[-1].strip() for line in lines
            )
            modified = modified.replace(bullet_block, consolidated + '\n')

        return modified, modified != content