# Source: projects/onboarding/milestones/M06_COORDINATION_TESTING.md
# Line: 983
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/cli/test.py
"""CLI command for coordination testing."""

import asyncio
import os

import click
from mycelium_testing.orchestrator import TestOrchestrator, TestSuite
from rich.console import Console

console = Console()

@click.command()
@click.option(
    '--pattern',
    type=click.Choice(['pubsub', 'taskqueue', 'request-reply', 'scatter-gather', 'barrier', 'circuit-breaker', 'all']),
    default='all',
    help='Test pattern to run'
)
@click.option('--mock', is_flag=True, help='Use mock MCP servers')
@click.option('--verbose', is_flag=True, help='Verbose output')
@click.option('--report', is_flag=True, help='Generate metrics report')
@click.option('--fail-fast', is_flag=True, help='Stop on first failure')
def test(pattern: str, mock: bool, verbose: bool, report: bool, fail_fast: bool):
    """Run coordination pattern tests."""

    # Set mock mode
    if mock:
        os.environ['USE_MOCK_MCP'] = 'true'

    console.print(f"[cyan]Running {pattern} tests...[/cyan]\n")

    # Create test suite
    suite = TestSuite(
        name=f"coordination-{pattern}",
        tests=_get_tests_for_pattern(pattern),
    )

    # Run tests
    orchestrator = TestOrchestrator()
    results = asyncio.run(orchestrator.run_suite(suite, fail_fast=fail_fast))

    # Show report
    console.print(orchestrator.generate_report())

    if report:
        # Generate metrics report if requested
        console.print("\n" + metrics.generate_report())

    # Exit with appropriate code
    failed = sum(1 for r in results if r.status == 'failed')
    if failed > 0:
        raise click.ClickException(f"{failed} tests failed")

def _get_tests_for_pattern(pattern: str) -> list:
    """Get test functions for pattern."""
    # Import test module and filter by pattern
    import tests.functional.test_coordination_patterns as tests_module

    if pattern == 'all':
        return [
            getattr(tests_module, name)
            for name in dir(tests_module)
            if name.startswith('test_')
        ]
    pattern_prefix = f"test_{pattern.replace('-', '_')}"
    return [
        getattr(tests_module, name)
        for name in dir(tests_module)
        if name.startswith(pattern_prefix)
    ]

if __name__ == '__main__':
    test()
