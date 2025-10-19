# Option B: Agent Prompt Optimization

**Status**: Draft Backlog
**Author**: @claude-code-developer + @project-manager
**Created**: 2025-10-18
**Estimated Effort**: 5-7 days (2-person team)
**Complexity**: Medium
**Dependencies**: Phase 2 Performance Analytics (completed)

---

## Executive Summary

Systematic optimization of all 119 agent prompts using a **data-driven quality rubric** and automated analysis tools. Combines NLP analysis, effectiveness metrics, and best practices to improve agent performance, reduce token usage, and enhance user experience.

**Value Proposition**:
- **Consistency**: Standardize prompt structure across all agents
- **Effectiveness**: Improve agent performance through empirical optimization
- **Token Efficiency**: Reduce prompt length without losing capability
- **Measurability**: A/B test improvements with analytics data

**Expected Improvements**:
- 15-25% reduction in average prompt token count
- 10-20% improvement in agent effectiveness scores
- 100% compliance with quality rubric
- Standardized structure for easier maintenance

---

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────┐
│   Prompt Quality Rubric (YAML Config)       │
│   - Clarity metrics (readability)            │
│   - Specificity metrics (examples, code)     │
│   - Consistency metrics (structure)          │
│   - Effectiveness metrics (usage data)       │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────┐
│   PromptAnalyzer (NLP + Metrics)             │
│   - analyze_readability()                    │
│   - count_examples()                         │
│   - measure_structure_adherence()            │
│   - get_effectiveness_from_analytics()       │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────┐
│   PromptOptimizer (Improvement Engine)       │
│   - suggest_improvements()                   │
│   - apply_template()                         │
│   - optimize_for_tokens()                    │
│   - ab_test_versions()                       │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────┐
│   CLI Tool (scripts/optimize_prompt.py)      │
│   - Analyze single agent                     │
│   - Batch optimize category                  │
│   - Generate reports                         │
└─────────────────────────────────────────────┘
```

---

## Prompt Quality Rubric

### Criteria Definition (YAML)

**File**: `/home/gerald/git/mycelium/config/prompt_quality_rubric.yaml`

```yaml
# Prompt Quality Rubric for Mycelium Agents
#
# This rubric defines measurable criteria for evaluating and optimizing
# agent prompt quality. Each criterion has a weight (0-1) and specific
# metrics for automated analysis.
#
# Total score: weighted sum of all criteria (0-100 scale)
#
# Author: @claude-code-developer
# Date: 2025-10-18

version: "1.0"

criteria:
  # ==================================================================
  # CLARITY (Weight: 0.25)
  # Measures how easy the prompt is to understand
  # ==================================================================
  clarity:
    weight: 0.25
    description: "Readability and comprehension ease"

    metrics:
      readability_score:
        type: "flesch_reading_ease"
        target: 60  # "Plain English" (60-70 range)
        weight: 0.4
        formula: "206.835 - 1.015(total_words/total_sentences) - 84.6(total_syllables/total_words)"
        scoring:
          excellent: [60, 100]   # Score 100%
          good: [50, 60]          # Score 80%
          acceptable: [40, 50]    # Score 60%
          needs_improvement: [0, 40]  # Score 40%

      sentence_complexity:
        type: "avg_sentence_length"
        target: 20  # Words per sentence
        weight: 0.3
        scoring:
          excellent: [10, 20]     # Score 100%
          good: [20, 25]          # Score 80%
          acceptable: [25, 30]    # Score 60%
          needs_improvement: [30, 100]  # Score 40%

      jargon_ratio:
        type: "technical_terms_percentage"
        target: 0.15  # 15% max technical terms
        weight: 0.3
        description: "Ratio of technical jargon to total words"
        technical_terms_list: "config/technical_terms.txt"
        scoring:
          excellent: [0, 0.10]    # Score 100%
          good: [0.10, 0.15]      # Score 80%
          acceptable: [0.15, 0.25]  # Score 60%
          needs_improvement: [0.25, 1.0]  # Score 40%

  # ==================================================================
  # SPECIFICITY (Weight: 0.25)
  # Measures how concrete and actionable the prompt is
  # ==================================================================
  specificity:
    weight: 0.25
    description: "Concrete examples and actionable guidance"

    metrics:
      example_count:
        type: "count"
        target: 3  # Minimum 3 examples per prompt
        weight: 0.35
        patterns:
          - "Example:"
          - "For example"
          - "For instance"
          - "Consider:"
          - "Such as:"
        scoring:
          excellent: [3, 100]     # Score 100%
          good: [2, 3]            # Score 80%
          acceptable: [1, 2]      # Score 60%
          needs_improvement: [0, 1]  # Score 40%

      code_snippet_count:
        type: "count"
        target: 2  # Minimum 2 code examples
        weight: 0.35
        patterns:
          - "```"  # Markdown code fences
        scoring:
          excellent: [2, 100]     # Score 100%
          good: [1, 2]            # Score 75%
          acceptable: [0, 1]      # Score 50%
          needs_improvement: [0, 0]  # Score 0%

      concrete_vs_abstract_ratio:
        type: "ratio"
        target: 0.7  # 70% concrete language
        weight: 0.30
        description: "Ratio of concrete nouns/verbs to abstract language"
        concrete_patterns:
          - "file", "directory", "function", "class", "module"
          - "test", "build", "deploy", "run", "execute"
        abstract_patterns:
          - "generally", "usually", "might", "could", "perhaps"
          - "overall", "various", "multiple", "some"
        scoring:
          excellent: [0.7, 1.0]   # Score 100%
          good: [0.5, 0.7]        # Score 80%
          acceptable: [0.3, 0.5]  # Score 60%
          needs_improvement: [0, 0.3]  # Score 40%

  # ==================================================================
  # CONSISTENCY (Weight: 0.20)
  # Measures adherence to standard structure and tone
  # ==================================================================
  consistency:
    weight: 0.20
    description: "Structure and tone standardization"

    metrics:
      structure_adherence:
        type: "section_check"
        target: 1.0  # 100% required sections present
        weight: 0.50
        required_sections:
          - "## Your Role"
          - "## Core Responsibilities"
          - "## Key Capabilities"
          - "## Workflow"
          - "## Quality Standards"
          - "## Communication Protocol"
        scoring:
          excellent: [1.0, 1.0]   # All sections present
          good: [0.83, 1.0]       # 5/6 sections
          acceptable: [0.67, 0.83]  # 4/6 sections
          needs_improvement: [0, 0.67]  # <4 sections

      tone_consistency:
        type: "sentiment_analysis"
        target: "professional_friendly"
        weight: 0.30
        description: "Consistent professional yet approachable tone"
        avoid_patterns:
          - "must", "shall", "always" (overly rigid)
          - "just", "simply", "obviously" (condescending)
        preferred_patterns:
          - "should", "recommend", "suggest"
          - "consider", "typically", "generally"
        scoring:
          excellent: 0  # No problematic patterns
          good: [1, 2]  # 1-2 instances
          acceptable: [3, 5]  # 3-5 instances
          needs_improvement: [6, 100]  # 6+ instances

      format_compliance:
        type: "markdown_validation"
        target: 1.0  # 100% valid Markdown
        weight: 0.20
        checks:
          - valid_headings: true  # Proper heading hierarchy
          - valid_lists: true     # Consistent list formatting
          - valid_code_fences: true  # Proper code block syntax
          - no_broken_links: true  # All links valid
        scoring:
          excellent: [1.0, 1.0]   # All checks pass
          good: [0.75, 1.0]       # 3/4 checks pass
          acceptable: [0.50, 0.75]  # 2/4 checks pass
          needs_improvement: [0, 0.50]  # <2 checks pass

  # ==================================================================
  # EFFECTIVENESS (Weight: 0.20)
  # Measures real-world performance from analytics
  # ==================================================================
  effectiveness:
    weight: 0.20
    description: "Performance metrics from analytics data"

    metrics:
      usage_frequency:
        type: "analytics"
        source: "UsageAnalyzer.get_popularity_ranking()"
        target: "top_50_percent"  # At least median usage
        weight: 0.30
        description: "How often agent is used (higher = more useful)"
        scoring:
          excellent: "top_25_percent"   # Score 100%
          good: "top_50_percent"        # Score 80%
          acceptable: "top_75_percent"  # Score 60%
          needs_improvement: "bottom_25_percent"  # Score 40%

      cache_hit_rate:
        type: "analytics"
        source: "MetricsAnalyzer.get_cache_performance()"
        target: 0.70  # 70% cache hit rate
        weight: 0.30
        description: "How often agent content is reused from cache"
        scoring:
          excellent: [0.70, 1.0]  # Score 100%
          good: [0.50, 0.70]      # Score 80%
          acceptable: [0.30, 0.50]  # Score 60%
          needs_improvement: [0, 0.30]  # Score 40%

      effectiveness_score:
        type: "analytics"
        source: "UsageAnalyzer.get_popularity_ranking()['avg_effectiveness_score']"
        target: 4.0  # 4.0/5.0 average rating
        weight: 0.40
        description: "User-provided effectiveness ratings (1-5 scale)"
        scoring:
          excellent: [4.5, 5.0]   # Score 100%
          good: [4.0, 4.5]        # Score 85%
          acceptable: [3.5, 4.0]  # Score 70%
          needs_improvement: [0, 3.5]  # Score 50%

  # ==================================================================
  # CONSTRAINTS (Weight: 0.10)
  # Ensures proper boundaries and scope definition
  # ==================================================================
  constraints:
    weight: 0.10
    description: "Clear boundaries and limitations"

    metrics:
      boundary_clarity:
        type: "section_content_check"
        target: true
        weight: 0.40
        description: "Explicit statement of what agent does NOT do"
        patterns:
          - "Out of Scope:"
          - "Limitations:"
          - "Not Responsible For:"
          - "Does NOT:"
        scoring:
          excellent: 2  # 2+ boundary statements
          good: 1       # 1 boundary statement
          needs_improvement: 0  # No boundaries

      scope_definition:
        type: "word_count"
        target: [200, 800]  # Sweet spot for scope clarity
        weight: 0.30
        description: "Scope section is neither too brief nor too verbose"
        section: "## Your Role"
        scoring:
          excellent: [200, 500]   # Score 100%
          good: [500, 800]        # Score 85%
          acceptable: [100, 200]  # Score 70%
          needs_improvement: [0, 100]  # Score 50%

      limitation_explicitness:
        type: "count"
        target: 3  # At least 3 explicit limitations
        weight: 0.30
        description: "Number of explicitly stated limitations"
        patterns:
          - "cannot", "does not", "will not"
          - "outside the scope", "not designed for"
          - "defer to", "escalate to"
        scoring:
          excellent: [3, 100]     # Score 100%
          good: [2, 3]            # Score 80%
          acceptable: [1, 2]      # Score 60%
          needs_improvement: [0, 1]  # Score 40%

# ==================================================================
# SCORING FORMULA
# ==================================================================
scoring:
  formula: |
    Total Score = Σ (Criterion Weight × Criterion Score)

    Where Criterion Score = Σ (Metric Weight × Metric Score)

    Example:
      Clarity: 0.25 × 85 = 21.25
      Specificity: 0.25 × 90 = 22.50
      Consistency: 0.20 × 75 = 15.00
      Effectiveness: 0.20 × 80 = 16.00
      Constraints: 0.10 × 70 = 7.00
      ────────────────────────────
      Total Score = 81.75/100

  grade_thresholds:
    A: [90, 100]   # Excellent - no changes needed
    B: [80, 90]    # Good - minor improvements
    C: [70, 80]    # Acceptable - moderate improvements
    D: [60, 70]    # Needs work - significant improvements
    F: [0, 60]     # Poor - major rewrite needed

# ==================================================================
# OPTIMIZATION TARGETS
# ==================================================================
optimization_targets:
  minimum_acceptable_score: 70  # Grade C
  target_score: 85  # Grade B+
  excellent_score: 90  # Grade A
  batch_optimization_priority: "lowest_scores_first"
  ab_test_threshold: 5  # Points improvement to justify A/B test
```

---

## Implementation Details

### Phase 1: Analysis Tools (Days 1-2)

**File**: `/home/gerald/git/mycelium/scripts/prompt_analyzer.py`

```python
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
        code_snippet_count = content.count('```')
        metrics['code_snippet_count'] = {
            "value": code_snippet_count,
            "score": self._score_metric(code_snippet_count, 'specificity', 'code_snippet_count'),
        }

        # Concrete vs abstract ratio
        concrete_patterns = self.rubric['criteria']['specificity']['metrics']['concrete_vs_abstract_ratio']['concrete_patterns']
        abstract_patterns = self.rubric['criteria']['specificity']['metrics']['concrete_vs_abstract_ratio']['abstract_patterns']

        content_lower = content.lower()
        concrete_count = sum(
            len(re.findall(r'\b' + pattern + r'\b', content_lower))
            for pattern in concrete_patterns
        )
        abstract_count = sum(
            len(re.findall(r'\b' + pattern + r'\b', content_lower))
            for pattern in abstract_patterns
        )

        concrete_ratio = concrete_count / max(concrete_count + abstract_count, 1)
        metrics['concrete_vs_abstract_ratio'] = {
            "value": concrete_ratio,
            "score": self._score_metric(concrete_ratio, 'specificity', 'concrete_vs_abstract_ratio'),
        }

        # Weighted average
        total_score = sum(
            m['score'] * self.rubric['criteria']['specificity']['metrics'][metric_name]['weight']
            for metric_name, m in metrics.items()
        )

        return {
            "score": round(total_score, 2),
            "metrics": metrics,
        }

    def _analyze_consistency(self, content: str) -> dict[str, Any]:
        """Analyze consistency metrics (structure, tone, format)."""
        metrics = {}

        # Structure adherence (required sections present)
        required_sections = self.rubric['criteria']['consistency']['metrics']['structure_adherence']['required_sections']
        sections_present = sum(1 for section in required_sections if section in content)
        adherence_ratio = sections_present / len(required_sections)
        metrics['structure_adherence'] = {
            "value": adherence_ratio,
            "score": self._score_metric(adherence_ratio, 'consistency', 'structure_adherence'),
        }

        # Tone consistency (avoid problematic patterns)
        avoid_patterns = self.rubric['criteria']['consistency']['metrics']['tone_consistency']['avoid_patterns']
        problematic_count = sum(
            len(re.findall(r'\b' + pattern + r'\b', content, re.IGNORECASE))
            for pattern in avoid_patterns
        )
        # Invert score (fewer problematic = better)
        metrics['tone_consistency'] = {
            "value": problematic_count,
            "score": self._score_metric(problematic_count, 'consistency', 'tone_consistency'),
        }

        # Format compliance (Markdown validation)
        format_checks = {
            'valid_headings': self._check_heading_hierarchy(content),
            'valid_lists': self._check_list_formatting(content),
            'valid_code_fences': self._check_code_fences(content),
            'no_broken_links': self._check_links(content),
        }
        compliance_ratio = sum(format_checks.values()) / len(format_checks)
        metrics['format_compliance'] = {
            "value": compliance_ratio,
            "score": self._score_metric(compliance_ratio, 'consistency', 'format_compliance'),
        }

        # Weighted average
        total_score = sum(
            m['score'] * self.rubric['criteria']['consistency']['metrics'][metric_name]['weight']
            for metric_name, m in metrics.items()
        )

        return {
            "score": round(total_score, 2),
            "metrics": metrics,
        }

    def _analyze_effectiveness(self, agent_id: str | None) -> dict[str, Any]:
        """Analyze effectiveness metrics from analytics data."""
        metrics = {}

        if self.usage_analyzer is None or agent_id is None:
            # No analytics available - skip effectiveness scoring
            return {
                "score": 0.0,
                "metrics": {},
                "note": "Analytics unavailable - effectiveness not scored"
            }

        # Get usage frequency percentile
        ranking = self.usage_analyzer.get_popularity_ranking(days=30)
        agent_ranks = {r['agent_id_hash']: i for i, r in enumerate(ranking)}
        agent_hash = self._hash_agent_id(agent_id)
        agent_rank = agent_ranks.get(agent_hash, len(ranking))
        percentile = (len(ranking) - agent_rank) / max(len(ranking), 1)

        usage_score = 100.0
        if percentile < 0.25:
            usage_score = 40.0  # Bottom 25%
        elif percentile < 0.50:
            usage_score = 60.0  # Bottom 50%
        elif percentile < 0.75:
            usage_score = 80.0  # Top 50%
        else:
            usage_score = 100.0  # Top 25%

        metrics['usage_frequency'] = {
            "value": percentile,
            "score": usage_score,
        }

        # Get cache hit rate
        cache_perf = self.usage_analyzer.get_cache_performance(days=30)
        cache_hit_rate = cache_perf.get('hit_rate_percentage', 0) / 100
        metrics['cache_hit_rate'] = {
            "value": cache_hit_rate,
            "score": self._score_metric(cache_hit_rate, 'effectiveness', 'cache_hit_rate'),
        }

        # Get effectiveness score (user ratings)
        agent_data = next((r for r in ranking if r['agent_id_hash'] == agent_hash), None)
        effectiveness_rating = agent_data.get('avg_effectiveness_score') if agent_data else None

        if effectiveness_rating is not None:
            metrics['effectiveness_score'] = {
                "value": effectiveness_rating,
                "score": self._score_metric(effectiveness_rating, 'effectiveness', 'effectiveness_score'),
            }
        else:
            metrics['effectiveness_score'] = {
                "value": None,
                "score": 50.0,  # Neutral score if no data
            }

        # Weighted average
        total_score = sum(
            m['score'] * self.rubric['criteria']['effectiveness']['metrics'][metric_name]['weight']
            for metric_name, m in metrics.items()
        )

        return {
            "score": round(total_score, 2),
            "metrics": metrics,
        }

    def _analyze_constraints(self, content: str) -> dict[str, Any]:
        """Analyze constraints metrics (boundaries, scope, limitations)."""
        metrics = {}

        # Boundary clarity (explicit out-of-scope statements)
        boundary_patterns = self.rubric['criteria']['constraints']['metrics']['boundary_clarity']['patterns']
        boundary_count = sum(
            1 for pattern in boundary_patterns if pattern in content
        )
        metrics['boundary_clarity'] = {
            "value": boundary_count,
            "score": self._score_metric(boundary_count, 'constraints', 'boundary_clarity'),
        }

        # Scope definition word count
        scope_section = self._extract_section(content, "## Your Role")
        scope_word_count = len(scope_section.split()) if scope_section else 0
        metrics['scope_definition'] = {
            "value": scope_word_count,
            "score": self._score_metric(scope_word_count, 'constraints', 'scope_definition'),
        }

        # Limitation explicitness
        limitation_patterns = self.rubric['criteria']['constraints']['metrics']['limitation_explicitness']['patterns']
        limitation_count = sum(
            len(re.findall(r'\b' + pattern + r'\b', content, re.IGNORECASE))
            for pattern in limitation_patterns
        )
        metrics['limitation_explicitness'] = {
            "value": limitation_count,
            "score": self._score_metric(limitation_count, 'constraints', 'limitation_explicitness'),
        }

        # Weighted average
        total_score = sum(
            m['score'] * self.rubric['criteria']['constraints']['metrics'][metric_name]['weight']
            for metric_name, m in metrics.items()
        )

        return {
            "score": round(total_score, 2),
            "metrics": metrics,
        }

    def _score_metric(
        self,
        value: float,
        criterion: str,
        metric_name: str
    ) -> float:
        """Convert metric value to score (0-100) using rubric thresholds."""
        metric_config = self.rubric['criteria'][criterion]['metrics'][metric_name]
        scoring = metric_config.get('scoring', {})

        # Handle different scoring types
        if isinstance(scoring, dict):
            for grade, threshold in scoring.items():
                if isinstance(threshold, list) and len(threshold) == 2:
                    if threshold[0] <= value <= threshold[1]:
                        # Map grade to score
                        grade_scores = {
                            'excellent': 100.0,
                            'good': 80.0,
                            'acceptable': 60.0,
                            'needs_improvement': 40.0,
                        }
                        return grade_scores.get(grade, 50.0)
                elif isinstance(threshold, (int, float)):
                    if value >= threshold:
                        return 100.0 if grade == 'excellent' else 80.0
                    else:
                        return 60.0 if grade == 'acceptable' else 40.0

        # Default: linear scale 0-100
        return min(100.0, max(0.0, value * 100))

    def _get_grade(self, total_score: float) -> str:
        """Convert total score to letter grade."""
        thresholds = self.rubric['scoring']['grade_thresholds']
        for grade, (min_score, max_score) in thresholds.items():
            if min_score <= total_score <= max_score:
                return grade
        return 'F'

    def _generate_suggestions(self, criteria_scores: dict) -> list[str]:
        """Generate improvement suggestions based on scores."""
        suggestions = []

        for criterion_name, criterion_data in criteria_scores.items():
            if criterion_data['score'] < 70:
                suggestions.append(
                    f"Improve {criterion_name}: score {criterion_data['score']:.1f}/100"
                )

                # Add specific metric suggestions
                for metric_name, metric_data in criterion_data.get('metrics', {}).items():
                    if metric_data['score'] < 70:
                        suggestions.append(f"  - {metric_name}: {metric_data['value']}")

        return suggestions

    # Helper methods for format validation
    def _check_heading_hierarchy(self, content: str) -> bool:
        """Check if headings follow proper hierarchy (##, ###, etc.)."""
        headings = re.findall(r'^(#{1,6})\s', content, re.MULTILINE)
        # Simple check: no skipping levels
        prev_level = 0
        for heading in headings:
            level = len(heading)
            if level > prev_level + 1:
                return False
            prev_level = level
        return True

    def _check_list_formatting(self, content: str) -> bool:
        """Check if lists use consistent formatting."""
        # Check for mixed bullet styles (-, *, +)
        bullets = re.findall(r'^([-*+])\s', content, re.MULTILINE)
        return len(set(bullets)) <= 1  # Only one bullet style

    def _check_code_fences(self, content: str) -> bool:
        """Check if code fences are balanced."""
        return content.count('```') % 2 == 0

    def _check_links(self, content: str) -> bool:
        """Check for broken Markdown links (basic validation)."""
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        # Basic check: no empty URLs
        return all(url.strip() for _, url in links)

    def _extract_section(self, content: str, heading: str) -> str:
        """Extract content of specific Markdown section."""
        pattern = rf'{re.escape(heading)}\n+(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _hash_agent_id(agent_id: str) -> str:
        """Hash agent ID (matches TelemetryCollector)."""
        import hashlib
        return hashlib.sha256(agent_id.encode()).hexdigest()[:8]
```

**Dependencies**: Install `textstat` for readability metrics:

```bash
uv pip install textstat
```

### Phase 2: Optimization Engine (Days 3-4)

**File**: `/home/gerald/git/mycelium/scripts/prompt_optimizer.py`

```python
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
```

### Phase 3: CLI Tool + Batch Processing (Day 5)

**File**: `/home/gerald/git/mycelium/scripts/optimize_agent.py`

```python
#!/usr/bin/env python3
"""CLI tool for agent prompt optimization.

Usage:
    # Analyze single agent
    python scripts/optimize_agent.py analyze agents/01-api-designer.md

    # Batch analyze category
    python scripts/optimize_agent.py batch-analyze --category core-development

    # Optimize single agent
    python scripts/optimize_agent.py optimize agents/01-api-designer.md --output agents/01-api-designer-v2.md

    # Batch optimize (lowest scores first)
    python scripts/optimize_agent.py batch-optimize --min-score 70 --dry-run

Author: @claude-code-developer + @documentation-engineer
Date: 2025-10-18
"""

import argparse
from pathlib import Path
from mycelium_analytics import EventStorage
from mycelium_analytics.metrics import UsageAnalyzer
from scripts.prompt_analyzer import PromptAnalyzer
from scripts.prompt_optimizer import PromptOptimizer
from scripts.agent_discovery import AgentDiscovery


def cmd_analyze(args):
    """Analyze single agent prompt."""
    analyzer = PromptAnalyzer(
        usage_analyzer=UsageAnalyzer(EventStorage()) if args.include_analytics else None
    )

    result = analyzer.analyze_prompt(
        Path(args.agent_path),
        agent_id=args.agent_id
    )

    print(f"\n=== Analysis: {args.agent_path} ===\n")
    print(f"Total Score: {result['total_score']:.1f}/100  (Grade: {result['grade']})")
    print(f"Token Count: {result['token_count']}")
    print()

    print("Criterion Scores:")
    for criterion, data in result['criteria_scores'].items():
        print(f"  {criterion.capitalize():15s}: {data['score']:5.1f}/100")
    print()

    if result['suggestions']:
        print("Suggestions for Improvement:")
        for suggestion in result['suggestions']:
            print(f"  - {suggestion}")
        print()


def cmd_batch_analyze(args):
    """Batch analyze agents by category."""
    # Load agent discovery
    index_path = Path("plugins/mycelium-core/agents/index.json")
    discovery = AgentDiscovery(index_path)

    # Get agents in category
    agents = discovery.list_agents(category=args.category)

    analyzer = PromptAnalyzer(
        usage_analyzer=UsageAnalyzer(EventStorage()) if args.include_analytics else None
    )

    print(f"\n=== Batch Analysis: {args.category} ===\n")
    print(f"Analyzing {len(agents)} agents...\n")

    results = []
    for agent in agents:
        agent_path = Path(agent['file_path'])
        result = analyzer.analyze_prompt(agent_path, agent_id=agent['id'])
        results.append({
            'agent_id': agent['id'],
            'score': result['total_score'],
            'grade': result['grade'],
            'token_count': result['token_count'],
        })

    # Sort by score (lowest first)
    results.sort(key=lambda x: x['score'])

    # Print summary
    for r in results:
        print(f"{r['agent_id']:40s}  {r['score']:5.1f}  ({r['grade']})  {r['token_count']} tokens")

    print()
    avg_score = sum(r['score'] for r in results) / len(results)
    print(f"Average Score: {avg_score:.1f}/100")
    print(f"Agents below 70: {sum(1 for r in results if r['score'] < 70)}")


def cmd_optimize(args):
    """Optimize single agent."""
    optimizer = PromptOptimizer(
        analyzer=PromptAnalyzer(usage_analyzer=UsageAnalyzer(EventStorage()))
    )

    suggestions = optimizer.suggest_improvements(
        Path(args.agent_path)
    )

    print(f"\n=== Optimization Suggestions: {args.agent_path} ===\n")

    for s in suggestions:
        print(f"[{s['priority'].upper()}] {s['category'].capitalize()}")
        print(f"  Issue: {s['issue']}")
        print(f"  Suggestion: {s['suggestion']}")
        print(f"  Estimated Impact: {s['estimated_impact']}")
        print()

    if args.apply:
        print("Applying template...")
        optimized = optimizer.apply_template(Path(args.agent_path))

        output_path = Path(args.output) if args.output else Path(args.agent_path).with_suffix('.optimized.md')
        output_path.write_text(optimized, encoding='utf-8')
        print(f"Optimized prompt written to: {output_path}")


def cmd_batch_optimize(args):
    """Batch optimize agents below score threshold."""
    # Load agent discovery
    index_path = Path("plugins/mycelium-core/agents/index.json")
    discovery = AgentDiscovery(index_path)

    analyzer = PromptAnalyzer(
        usage_analyzer=UsageAnalyzer(EventStorage())
    )
    optimizer = PromptOptimizer(analyzer=analyzer)

    # Analyze all agents
    all_agents = discovery.list_agents()
    candidates = []

    for agent in all_agents:
        agent_path = Path(agent['file_path'])
        result = analyzer.analyze_prompt(agent_path, agent_id=agent['id'])

        if result['total_score'] < args.min_score:
            candidates.append({
                'agent_id': agent['id'],
                'path': agent_path,
                'score': result['total_score'],
            })

    # Sort by score (lowest first)
    candidates.sort(key=lambda x: x['score'])

    print(f"\n=== Batch Optimization ===\n")
    print(f"Found {len(candidates)} agents below {args.min_score}/100\n")

    for candidate in candidates[:args.limit]:
        print(f"Optimizing: {candidate['agent_id']} ({candidate['score']:.1f}/100)")

        if not args.dry_run:
            suggestions = optimizer.suggest_improvements(candidate['path'])
            # TODO: Apply optimizations
            print(f"  - {len(suggestions)} improvements suggested")
        else:
            print("  [DRY RUN - skipped]")


def main():
    parser = argparse.ArgumentParser(description="Agent prompt optimization CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze single agent")
    analyze_parser.add_argument("agent_path", help="Path to agent markdown file")
    analyze_parser.add_argument("--agent-id", help="Agent ID for analytics lookup")
    analyze_parser.add_argument("--include-analytics", action="store_true", help="Include effectiveness metrics")

    # Batch analyze command
    batch_analyze_parser = subparsers.add_parser("batch-analyze", help="Analyze category")
    batch_analyze_parser.add_argument("--category", required=True, help="Agent category")
    batch_analyze_parser.add_argument("--include-analytics", action="store_true")

    # Optimize command
    optimize_parser = subparsers.add_parser("optimize", help="Optimize single agent")
    optimize_parser.add_argument("agent_path", help="Path to agent markdown file")
    optimize_parser.add_argument("--output", help="Output path for optimized version")
    optimize_parser.add_argument("--apply", action="store_true", help="Apply template")

    # Batch optimize command
    batch_optimize_parser = subparsers.add_parser("batch-optimize", help="Batch optimize low-scoring agents")
    batch_optimize_parser.add_argument("--min-score", type=float, default=70, help="Min acceptable score")
    batch_optimize_parser.add_argument("--limit", type=int, default=10, help="Max agents to optimize")
    batch_optimize_parser.add_argument("--dry-run", action="store_true", help="Dry run (no changes)")

    args = parser.parse_args()

    if args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "batch-analyze":
        cmd_batch_analyze(args)
    elif args.command == "optimize":
        cmd_optimize(args)
    elif args.command == "batch-optimize":
        cmd_batch_optimize(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

---

## Testing Strategy

### Unit Tests

```python
"""Unit tests for prompt analyzer and optimizer."""

import pytest
from pathlib import Path
from scripts.prompt_analyzer import PromptAnalyzer
from scripts.prompt_optimizer import PromptOptimizer


def test_analyze_clarity(tmp_path):
    """Test clarity analysis."""
    content = "This is a simple test. It has short sentences. Easy to read."
    test_file = tmp_path / "test.md"
    test_file.write_text(content)

    analyzer = PromptAnalyzer()
    result = analyzer.analyze_prompt(test_file)

    assert 'clarity' in result['criteria_scores']
    assert result['criteria_scores']['clarity']['score'] > 0


def test_token_optimization(tmp_path):
    """Test token reduction."""
    verbose_content = """
    This is basically a very verbose example that essentially contains
    redundant phrases. As mentioned before, we should remove these.
    """
    test_file = tmp_path / "verbose.md"
    test_file.write_text(verbose_content)

    optimizer = PromptOptimizer(PromptAnalyzer())
    optimized, stats = optimizer.optimize_for_tokens(test_file)

    assert stats['reduction_percentage'] > 0
    assert stats['optimized_tokens'] < stats['original_tokens']
```

---

## Implementation Timeline

### Week 1: Days 1-2 (Analysis Tools)
- Build `PromptAnalyzer` class
- Implement rubric scoring logic
- Unit tests for all criteria

### Week 1: Days 3-4 (Optimization Engine)
- Build `PromptOptimizer` class
- Create standard template
- Token reduction methods

### Week 1: Day 5 (CLI + Integration)
- Build `optimize_agent.py` CLI
- Integration tests
- Documentation

### Week 2: Days 1-2 (Pilot Optimization)
- Analyze all 119 agents
- Optimize 10 low-scoring agents
- Measure improvements

### Week 2: Days 3-5 (Batch Optimization)
- Optimize remaining agents
- A/B testing framework
- Final documentation

**Total**: 5-7 days for 2-person team

---

## Effort Estimate

**Complexity**: Medium (NLP + analytics integration)

**Team Composition**:
- 1x @python-pro (lead developer, NLP)
- 1x @documentation-engineer (optimization, templates)

**Breakdown**:
- Analysis tools: 2 days
- Optimization engine: 2 days
- CLI + integration: 1 day
- Pilot optimization: 2 days
- Batch optimization: 2 days

**Total**: 5-7 days (depending on batch size)

---

## Dependencies

**Required**:
- Phase 2 Performance Analytics (✅ Complete)
- Python `textstat` library (readability metrics)
- Agent discovery system (✅ Complete)

**Optional**:
- Option A (Usage Analytics) for effectiveness scoring
- spaCy for advanced NLP (if needed)

---

## Success Metrics

**Acceptance Criteria**:
1. ✅ Rubric covers 5 criteria with measurable metrics
2. ✅ All 119 agents analyzed with scores
3. ✅ Batch optimization of agents < 70/100
4. ✅ 15-25% token reduction achieved
5. ✅ CLI tool supports analyze, optimize, batch operations
6. ✅ A/B testing framework validates improvements
7. ✅ 100% test coverage (unit + integration)

**Performance Targets**:
- Average score improvement: +10-20 points
- Token reduction: 15-25%
- Analysis time: <5s per agent
- Batch optimization: <10 min for 100 agents

---

## Risk Assessment

**Technical Risks**: MEDIUM
- NLP accuracy depends on textstat library quality
- Manual review still needed for quality assurance
- A/B testing requires sufficient usage data

**Blockers**: NONE
- All dependencies available

**Mitigation**:
- Start with pilot (10 agents) to validate approach
- Human review of optimized prompts before rollout
- Gradual rollout with monitoring

---

## Conclusion

Option B provides **systematic quality improvement** across all 119 agents using data-driven analysis and automated optimization. The rubric ensures consistency, while analytics integration validates improvements.

**Recommendation**: **APPROVED for Sprint Planning** (after Option A if effectiveness metrics needed)

---

**Next Steps**:
1. Approve backlog item
2. Install dependencies (`textstat`)
3. Create prompt quality rubric (YAML)
4. Assign to @python-pro + @documentation-engineer
5. Run pilot optimization on 10 agents
