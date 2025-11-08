"""CLI commands for Mycelium configuration management.

This package provides modular CLI commands for managing configuration,
including viewing, editing, and migrating configuration files.
"""

from mycelium_onboarding.cli_commands.commands.config import config_group
from mycelium_onboarding.cli_commands.commands.config_migrate import migrate_command

__all__ = [
    "config_group",
    "migrate_command",
]
