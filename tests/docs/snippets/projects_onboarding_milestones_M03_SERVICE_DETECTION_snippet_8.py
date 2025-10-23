# Source: projects/onboarding/milestones/M03_SERVICE_DETECTION.md
# Line: 903
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/cli/detect_commands.py
"""CLI commands for service detection."""

import click
import asyncio
import json

from mycelium_onboarding.detection.orchestrator import detect_all_services


@click.command(name="detect")
@click.option(
    "--no-cache",
    is_flag=True,
    help="Skip cache, always run fresh detection"
)
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format"
)
def detect_services(no_cache: bool, format: str):
    """Detect available services."""
    use_cache = not no_cache

    # Run async detection
    results = asyncio.run(detect_all_services(use_cache=use_cache))

    if format == "json":
        click.echo(json.dumps(results.to_dict(), indent=2))
    else:
        _print_text_results(results)


def _print_text_results(results):
    """Print results in human-readable format."""
    click.echo("=== Service Detection Results ===\n")

    # Docker
    click.echo("Docker:")
    if results.docker.available:
        status = "✓ Available" if results.docker.running else "⚠ Not running"
        click.echo(f"  {status}")
        if results.docker.version:
            click.echo(f"  Version: {results.docker.version}")
        if results.docker.compose_available:
            click.echo(f"  Compose: {results.docker.compose_version or 'available'}")
    else:
        click.echo(f"  ✗ Not available ({results.docker.error})")

    # Redis
    click.echo("\nRedis:")
    if results.redis.available:
        click.echo(f"  ✓ Available at {results.redis.host}:{results.redis.port}")
        if results.redis.version:
            click.echo(f"  Version: {results.redis.version}")
    else:
        click.echo(f"  ✗ Not available ({results.redis.error})")

    # ... similar for postgres, temporal, gpu ...