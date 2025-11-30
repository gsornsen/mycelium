"""Shell completion support for Mycelium CLI.

Provides dynamic completions for agent names, categories, and other CLI arguments.
Uses Click's built-in shell completion framework.
"""


import click

from mycelium.registry.client import RegistryClient


def complete_agent_names(
    _ctx: click.Context,
    _param: click.Parameter,
    incomplete: str,
) -> list[str]:
    """Complete agent names from the registry.

    Args:
        _ctx: Click context (unused but required by Click API)
        _param: Click parameter (unused but required by Click API)
        incomplete: Partial input from user

    Returns:
        List of matching agent names
    """
    try:
        registry = RegistryClient()
        agents = registry.list_agents()
        agent_names = [agent.name for agent in agents]
        return [name for name in agent_names if name.startswith(incomplete)]
    except Exception:
        # If registry is unavailable, return empty list
        return []


def complete_running_agent_names(
    _ctx: click.Context,
    _param: click.Parameter,
    incomplete: str,
) -> list[str]:
    """Complete running agent names from the registry.

    Args:
        _ctx: Click context (unused but required by Click API)
        _param: Click parameter (unused but required by Click API)
        incomplete: Partial input from user

    Returns:
        List of matching running agent names
    """
    try:
        registry = RegistryClient()
        agents = registry.list_agents()
        # Filter for running agents (healthy status)
        running_names = [
            agent.name for agent in agents
            if agent.status in ("healthy", "starting")
        ]
        return [name for name in running_names if name.startswith(incomplete)]
    except Exception:
        return []


def complete_categories(
    _ctx: click.Context,
    _param: click.Parameter,
    incomplete: str,
) -> list[str]:
    """Complete agent category names from the registry.

    Args:
        _ctx: Click context (unused but required by Click API)
        _param: Click parameter (unused but required by Click API)
        incomplete: Partial input from user

    Returns:
        List of matching category names
    """
    try:
        registry = RegistryClient()
        agents = registry.list_agents()
        # Get unique categories
        categories = list({agent.category for agent in agents})
        return [cat for cat in categories if cat.startswith(incomplete)]
    except Exception:
        return []


def complete_shell_types(
    _ctx: click.Context,
    _param: click.Parameter,
    incomplete: str,
) -> list[str]:
    """Complete supported shell types.

    Args:
        _ctx: Click context (unused but required by Click API)
        _param: Click parameter (unused but required by Click API)
        incomplete: Partial input from user

    Returns:
        List of supported shell types
    """
    shells = ["bash", "zsh", "fish"]
    return [shell for shell in shells if shell.startswith(incomplete)]
