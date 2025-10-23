# Source: projects/backlog/OPTION_B_AGENT_PROMPT_OPTIMIZATION.md
# Line: 387
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: unterminated string literal (detected at line 186) (<unknown>, line 186)

"""Prompt quality analysis using rubric and NLP.

Analyzes agent prompts against quality rubric to identify improvement
opportunities. Combines static analysis (readability, structure) with
dynamic metrics (usage analytics).

Author: @claude-code-developer
Date: 2025-10-18
"""

import re
import yaml
from pathlib import Path
from typing import Any
import textstat  # For readability metrics
from mycelium_analytics import EventStorage
from mycelium_analytics.metrics import UsageAnalyzer


class PromptAnalyzer:
    """Analyzes agent prompt quality against rubric.

    Computes scores for clarity, specificity, consistency, effectiveness,
    and constraints based on automated analysis and analytics data.

    Attributes:
        rubric: Quality rubric configuration (from YAML)
        usage_analyzer: UsageAnalyzer for effectiveness metrics

    Example:
        >>> analyzer = PromptAnalyzer()
        >>> result = analyzer.analyze_prompt("path/to/agent.md")
        >>> result['total_score']
        82.5
        >>> result['grade']
        'B'
    """

    def __init__(
        self,
        rubric_path: Path | None = None,
        usage_analyzer: UsageAnalyzer | None = None
    ):
        """Initialize analyzer with rubric and analytics.

        Args:
            rubric_path: Path to rubric YAML (default: config/prompt_quality_rubric.yaml)
            usage_analyzer: Optional UsageAnalyzer for effectiveness metrics
        """
        if rubric_path is None:
            rubric_path = Path("config/prompt_quality_rubric.yaml")

        with open(rubric_path) as f:
            self.rubric = yaml.safe_load(f)

        self.usage_analyzer = usage_analyzer

    def analyze_prompt(
        self,
        prompt_path: Path,
        agent_id: str | None = None
    ) -> dict[str, Any]:
        """Analyze prompt against quality rubric.

        Args:
            prompt_path: Path to agent markdown file
            agent_id: Optional agent ID for analytics lookup

        Returns:
            Analysis result dictionary:
            {
                "total_score": 82.5,
                "grade": "B",
                "criteria_scores": {
                    "clarity": {"score": 85.0, "metrics": {...}},
                    "specificity": {...},
                    ...
                },
                "suggestions": ["Improve readability...", ...]
            }

        Example:
            >>> analyzer = PromptAnalyzer()
            >>> result = analyzer.analyze_prompt(Path("agents/01-core-api-designer.md"))
            >>> result['grade'] in ['A', 'B', 'C', 'D', 'F']
            True
        """
        # Read prompt content
        content = prompt_path.read_text(encoding='utf-8')

        # Analyze each criterion
        criteria_scores = {}

        criteria_scores['clarity'] = self._analyze_clarity(content)
        criteria_scores['specificity'] = self._analyze_specificity(content)
        criteria_scores['consistency'] = self._analyze_consistency(content)
        criteria_scores['effectiveness'] = self._analyze_effectiveness(
            agent_id=agent_id
        )
        criteria_scores['constraints'] = self._analyze_constraints(content)

        # Compute total score
        total_score = 0.0
        for criterion_name, criterion_data in criteria_scores.items():
            criterion_weight = self.rubric['criteria'][criterion_name]['weight']
            criterion_score = criterion_data['score']
            total_score += criterion_weight * criterion_score

        # Determine grade
        grade = self._get_grade(total_score)

        # Generate suggestions
        suggestions = self._generate_suggestions(criteria_scores)

        return {
            "total_score": round(total_score, 2),
            "grade": grade,
            "criteria_scores": criteria_scores,
            "suggestions": suggestions,
            "token_count": len(content.split()),  # Rough estimate
            "char_count": len(content),
        }

    def _analyze_clarity(self, content: str) -> dict[str, Any]:
        """Analyze clarity metrics (readability, sentence complexity, jargon)."""
        metrics = {}

        # Readability score (Flesch Reading Ease)
        readability = textstat.flesch_reading_ease(content)
        metrics['readability_score'] = {
            "value": readability,
            "score": self._score_metric(readability, 'clarity', 'readability_score'),
        }

        # Sentence complexity (average sentence length)
        sentences = re.split(r'[.!?]+', content)
        words = content.split()
        avg_sentence_length = len(words) / max(len(sentences), 1)
        metrics['sentence_complexity'] = {
            "value": avg_sentence_length,
            "score": self._score_metric(avg_sentence_length, 'clarity', 'sentence_complexity'),
        }

        # Jargon ratio (technical terms / total words)
        # Load technical terms list
        tech_terms_path = Path(self.rubric['criteria']['clarity']['metrics']['jargon_ratio'].get('technical_terms_list', 'config/technical_terms.txt'))
        tech_terms = set()
        if tech_terms_path.exists():
            tech_terms = set(tech_terms_path.read_text().strip().split('\n'))

        content_lower = content.lower()
        jargon_count = sum(1 for term in tech_terms if term.lower() in content_lower)
        jargon_ratio = jargon_count / max(len(words), 1)
        metrics['jargon_ratio'] = {
            "value": jargon_ratio,
            "score": self._score_metric(jargon_ratio, 'clarity', 'jargon_ratio'),
        }

        # Weighted average of clarity metrics
        total_score = sum(
            m['score'] * self.rubric['criteria']['clarity']['metrics'][metric_name]['weight']
            for metric_name, m in metrics.items()
        )

        return {
            "score": round(total_score, 2),
            "metrics": metrics,
        }

    def _analyze_specificity(self, content: str) -> dict[str, Any]:
        """Analyze specificity metrics (examples, code snippets, concrete language)."""
        metrics = {}

        # Example count
        example_patterns = self.rubric['criteria']['specificity']['metrics']['example_count']['patterns']
        example_count = sum(
            len(re.findall(pattern, content, re.IGNORECASE))
            for pattern in example_patterns
        )
        metrics['example_count'] = {
            "value": example_count,
            "score": self._score_metric(example_count, 'specificity', 'example_count'),
        }

        # Code snippet count
        code_snippet_count = content.count('