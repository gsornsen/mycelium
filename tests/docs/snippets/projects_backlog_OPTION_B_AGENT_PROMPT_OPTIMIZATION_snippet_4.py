# Source: projects/backlog/OPTION_B_AGENT_PROMPT_OPTIMIZATION.md
# Line: 1459
# Valid syntax: True
# Has imports: True
# Has assignments: True

"""Unit tests for prompt analyzer and optimizer."""

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
