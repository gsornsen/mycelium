"""Mycelium CLI entry point.

Modern CLI using Click with type hints and clear error messages.
Follows DX requirements: zero-friction start, clear errors, fast responses.
Includes shell completion support for bash, zsh, and fish.
Uses Rich library for beautiful terminal output.
"""

from pathlib import Path

import click

from mycelium.cli.completion import (
    complete_agent_names,
    complete_categories,
    complete_running_agent_names,
    complete_shell_types,
)
from mycelium.cli.output import (
    console,
    create_spinner,
    print_agent_started,
    print_agent_stopped,
    print_agent_table,
    print_discovery_summary,
    print_error,
    print_info,
    print_registry_status,
    print_success,
    print_warning,
)
from mycelium.cli.selector import select_agent_interactive
from mycelium.discovery.scanner import AgentScanner
from mycelium.errors import MyceliumError
from mycelium.registry.client import RegistryClient
from mycelium.supervisor.manager import ProcessManager

# Default plugin directory
DEFAULT_PLUGIN_DIR = Path.home() / "git" / "mycelium" / "plugins" / "mycelium-core" / "agents"


@click.group()
@click.version_option(version="0.1.0")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Mycelium - Multi-agent development orchestration platform.

    Get started:
        mycelium agent list         # List available agents
        mycelium agent select       # Fuzzy-search agents
        mycelium agent start NAME   # Start an agent
        mycelium agent stop NAME    # Stop an agent
        mycelium api start          # Start the REST API server

    For help on any command:
        mycelium COMMAND --help

    Shell completion:
        mycelium completion install  # Install shell completion
    """
    ctx.ensure_object(dict)
    ctx.obj["registry"] = RegistryClient()
    ctx.obj["supervisor"] = ProcessManager()
    ctx.obj["scanner"] = AgentScanner(registry=ctx.obj["registry"])


@cli.group()
def agent() -> None:
    """Manage agents (list, start, stop, select)."""
    pass


@agent.command()
@click.option(
    "--category",
    "-c",
    help="Filter by category",
    type=str,
    shell_complete=complete_categories,
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON for scripting",
)
@click.option(
    "--discover",
    "-d",
    is_flag=True,
    help="Discover agents from plugin directory",
)
@click.pass_context
def list(ctx: click.Context, category: str | None, output_json: bool, discover: bool) -> None:
    """List available agents.

    Examples:
        mycelium agent list
        mycelium agent list --category backend
        mycelium agent list --discover
        mycelium agent list --json
    """
    try:
        registry: RegistryClient = ctx.obj["registry"]
        scanner: AgentScanner = ctx.obj["scanner"]

        # Optionally discover agents from plugins
        if discover:
            plugin_dir = DEFAULT_PLUGIN_DIR
            if plugin_dir.exists():
                with create_spinner(f"Scanning {plugin_dir} for agents..."):
                    discovered = scanner.scan_directory(plugin_dir)
                    discovered_count = len(discovered)
                    # Register discovered agents
                    scanner.register_discovered_agents()

                if not output_json:
                    print_info(f"Discovered {discovered_count} agent(s) from {plugin_dir}")
                    console.print()
            else:
                if not output_json:
                    print_warning(f"Plugin directory not found: {plugin_dir}")
                    console.print()

        # List registered agents
        agents = registry.list_agents(category=category)

        if output_json:
            import json
            click.echo(json.dumps([a.to_dict() for a in agents], indent=2))
        else:
            if not agents:
                console.print()
                print_info("No agents registered.")
                console.print()
                console.print("[dim]Tip: Discover agents from plugins:[/dim]")
                console.print("  [bold]mycelium agent list --discover[/bold]")
                console.print()
                console.print("[dim]Or check if agent registry is running:[/dim]")
                console.print("  [bold]mycelium registry status[/bold]")
                console.print()
                return

            print_agent_table(agents, category)

    except MyceliumError:
        raise
    except Exception as e:
        raise MyceliumError(
            f"Failed to list agents: {str(e)}",
            suggestion="Ensure Redis is running: redis-cli ping",
            docs_url="https://docs.mycelium.dev/quickstart/setup",
            debug_info={"category": category}
        )


@agent.command()
@click.option(
    "--category",
    "-c",
    help="Filter by category",
    type=str,
    shell_complete=complete_categories,
)
@click.option(
    "--copy",
    is_flag=True,
    help="Copy selected agent name to clipboard",
)
@click.pass_context
def select(ctx: click.Context, category: str | None, copy: bool) -> None:
    """Fuzzy-search and select an agent interactively using fzf.

    Opens an interactive fzf interface with:
    - Fuzzy search across all agent names
    - Preview pane showing agent details
    - Category filtering
    - Fast keyboard navigation

    Examples:
        mycelium agent select
        mycelium agent select --category backend
        mycelium agent select --copy

    Requirements:
        - fzf must be installed (https://github.com/junegunn/fzf)

    Keyboard shortcuts:
        - Type to fuzzy search
        - Up/Down arrows to navigate
        - Enter to select
        - Ctrl+C or ESC to cancel
    """
    try:
        registry: RegistryClient = ctx.obj["registry"]

        # Run interactive selector
        selected_agent = select_agent_interactive(registry, category=category)

        if not selected_agent:
            console.print()
            print_info("Selection cancelled.")
            console.print()
            return

        # Display selected agent
        console.print()
        print_success(f"Selected: [bold]{selected_agent.name}[/bold]")
        console.print()
        console.print(f"  Category: [magenta]{selected_agent.category}[/magenta]")
        if selected_agent.description:
            console.print(f"  Description: [dim]{selected_agent.description}[/dim]")
        console.print()

        # Copy to clipboard if requested
        if copy:
            try:
                import pyperclip
                pyperclip.copy(selected_agent.name)
                print_success("Agent name copied to clipboard")
                console.print()
            except ImportError:
                print_warning("pyperclip not installed - cannot copy to clipboard")
                print_info("Install with: uv add pyperclip")
                console.print()

        # Show next steps
        console.print("[dim]Next steps:[/dim]")
        console.print(f"  [bold]mycelium agent start {selected_agent.name}[/bold]")
        console.print()

    except MyceliumError:
        raise
    except KeyboardInterrupt:
        console.print()
        print_info("Selection cancelled.")
        console.print()
    except Exception as e:
        raise MyceliumError(
            f"Failed to select agent: {str(e)}",
            suggestion="Check fzf is installed and agent registry is running",
            docs_url="https://docs.mycelium.dev/cli/select",
            debug_info={"category": category}
        )


@agent.command()
@click.argument("name", shell_complete=complete_agent_names)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to agent configuration file",
)
@click.pass_context
def start(ctx: click.Context, name: str, config: Path | None) -> None:
    """Start an agent.

    Examples:
        mycelium agent start backend-engineer
        mycelium agent start backend-engineer --config ./config.yaml
    """
    try:
        supervisor: ProcessManager = ctx.obj["supervisor"]
        registry: RegistryClient = ctx.obj["registry"]

        # Check if agent exists in registry
        agent_info = registry.get_agent(name)
        if not agent_info:
            raise MyceliumError(
                f"Agent '{name}' not found in registry",
                suggestion="List available agents: mycelium agent list --discover",
                docs_url="https://docs.mycelium.dev/agents/overview"
            )

        # Start process with spinner
        with create_spinner(f"Starting agent '{name}'..."):
            process_id = supervisor.start_agent(name, config=config)

        print_agent_started(name, process_id)

    except MyceliumError:
        raise
    except Exception as e:
        raise MyceliumError(
            f"Failed to start agent '{name}': {str(e)}",
            suggestion="Check agent configuration and system resources",
            docs_url="https://docs.mycelium.dev/troubleshooting/agent-start",
            debug_info={"agent": name, "config": str(config) if config else None}
        )


@agent.command()
@click.argument("name", shell_complete=complete_running_agent_names)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force stop without graceful shutdown",
)
@click.pass_context
def stop(ctx: click.Context, name: str, force: bool) -> None:
    """Stop a running agent.

    Examples:
        mycelium agent stop backend-engineer
        mycelium agent stop backend-engineer --force
    """
    try:
        supervisor: ProcessManager = ctx.obj["supervisor"]

        if not force:
            click.confirm(
                f"Stop agent '{name}'?",
                default=True,
                abort=True
            )

        with create_spinner(f"Stopping agent '{name}'..."):
            supervisor.stop_agent(name, graceful=not force)

        print_agent_stopped(name)

    except click.Abort:
        console.print()
        print_info("Cancelled.")
        console.print()
    except MyceliumError:
        # Let MyceliumError (including SupervisorError) pass through unchanged
        raise
    except Exception as e:
        raise MyceliumError(
            f"Failed to stop agent '{name}': {str(e)}",
            suggestion="Try force stop: mycelium agent stop {name} --force",
            docs_url="https://docs.mycelium.dev/troubleshooting/agent-stop",
            debug_info={"agent": name, "force": force}
        )


@agent.command()
@click.argument("name", shell_complete=complete_running_agent_names)
@click.option(
    "--follow",
    "-f",
    is_flag=True,
    help="Follow log output (like tail -f)",
)
@click.option(
    "--lines",
    "-n",
    default=50,
    help="Number of lines to show",
    type=int,
)
@click.pass_context
def logs(ctx: click.Context, name: str, follow: bool, lines: int) -> None:
    """View agent logs.

    Examples:
        mycelium agent logs backend-engineer
        mycelium agent logs backend-engineer --follow
        mycelium agent logs backend-engineer --lines 100
    """
    try:
        supervisor: ProcessManager = ctx.obj["supervisor"]

        if follow:
            console.print()
            print_info(f"Following logs for '{name}' (Ctrl+C to stop)...")
            console.print()
            supervisor.stream_logs(name)
        else:
            logs_output = supervisor.get_logs(name, lines=lines)
            click.echo(logs_output)

    except KeyboardInterrupt:
        console.print()
        print_info("Stopped following logs.")
        console.print()
    except MyceliumError:
        raise
    except Exception as e:
        raise MyceliumError(
            f"Failed to retrieve logs for '{name}': {str(e)}",
            suggestion="Check if agent is running: mycelium agent list",
            docs_url="https://docs.mycelium.dev/cli/logs",
            debug_info={"agent": name, "follow": follow, "lines": lines}
        )


@agent.command()
@click.option(
    "--plugin-dir",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    default=DEFAULT_PLUGIN_DIR,
    help="Plugin directory to scan",
)
@click.pass_context
def discover(ctx: click.Context, plugin_dir: Path) -> None:
    """Discover and register agents from plugin directory.

    Examples:
        mycelium agent discover
        mycelium agent discover --plugin-dir /path/to/plugins
    """
    try:
        scanner: AgentScanner = ctx.obj["scanner"]

        # Scan with spinner
        with create_spinner(f"Scanning {plugin_dir} for agents..."):
            discovered = scanner.scan_directory(plugin_dir)

        if not discovered:
            console.print()
            print_info("No agents found.")
            console.print()
            return

        # Register them
        registered = scanner.register_discovered_agents()

        # Print summary
        print_discovery_summary(len(discovered), registered, discovered)

    except MyceliumError:
        raise
    except Exception as e:
        raise MyceliumError(
            f"Failed to discover agents: {str(e)}",
            suggestion="Check plugin directory path and permissions",
            docs_url="https://docs.mycelium.dev/plugins/discovery",
            debug_info={"plugin_dir": str(plugin_dir)}
        )


@cli.group()
def registry() -> None:
    """Manage agent registry."""
    pass


@registry.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Check registry status.

    Example:
        mycelium registry status
    """
    try:
        registry: RegistryClient = ctx.obj["registry"]

        is_healthy = registry.health_check()

        if is_healthy:
            stats = registry.get_stats()
            plugin_dir = str(DEFAULT_PLUGIN_DIR) if DEFAULT_PLUGIN_DIR.exists() else None
            print_registry_status(is_healthy, stats, plugin_dir)
        else:
            print_registry_status(is_healthy)

    except MyceliumError:
        raise
    except Exception as e:
        raise MyceliumError(
            f"Failed to check registry status: {str(e)}",
            suggestion="Ensure Redis is running on the default port",
            docs_url="https://docs.mycelium.dev/setup/redis",
            debug_info={"error": str(e)}
        )


@cli.group()
def api() -> None:
    """Manage REST API server."""
    pass


@api.command()
@click.option(
    "--port",
    "-p",
    default=8080,
    help="Port to bind to",
    type=int,
)
@click.option(
    "--redis-url",
    default="redis://localhost:6379",
    help="Redis connection URL",
    type=str,
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload for development",
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(["debug", "info", "warning", "error"], case_sensitive=False),
    help="Logging level",
)
def start(port: int, redis_url: str, reload: bool, log_level: str) -> None:
    """Start the REST API server.

    The API server provides programmatic access to agent and workflow status.

    SECURITY: The server binds to 127.0.0.1 (localhost) only for security.
    This is an unauthenticated API and should never be exposed to the network.

    Examples:
        mycelium api start
        mycelium api start --port 9000
        mycelium api start --reload  # Development mode with auto-reload

    Once started, you can access:
        - API docs: http://localhost:8080/docs
        - Health check: http://localhost:8080/api/v1/health
        - List agents: http://localhost:8080/api/v1/agents
    """
    try:
        from mycelium.api.server import start_server

        console.print()
        print_info(f"Starting Mycelium API server on port {port}...")
        console.print()
        console.print(f"[bold]OpenAPI docs:[/bold] http://127.0.0.1:{port}/docs")
        console.print(f"[bold]Health check:[/bold] http://127.0.0.1:{port}/api/v1/health")
        console.print(f"[bold]List agents:[/bold] http://127.0.0.1:{port}/api/v1/agents")
        console.print()
        console.print("[yellow]Security:[/yellow] Server bound to 127.0.0.1 (localhost only)")
        console.print()

        # Start the server (this blocks until shutdown)
        start_server(
            port=port,
            redis_url=redis_url,
            reload=reload,
            log_level=log_level.lower(),
        )

    except KeyboardInterrupt:
        console.print()
        print_info("API server stopped.")
        console.print()
    except MyceliumError:
        raise
    except Exception as e:
        raise MyceliumError(
            f"Failed to start API server: {str(e)}",
            suggestion="Check if port is already in use or Redis is running",
            docs_url="https://docs.mycelium.dev/api/setup",
            debug_info={"port": port, "redis_url": redis_url}
        )


@cli.group()
def completion() -> None:
    """Shell completion management."""
    pass


@completion.command()
@click.argument(
    "shell",
    type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False),
    required=False,
    shell_complete=complete_shell_types,
)
def install(shell: str | None) -> None:
    """Install shell completion for Mycelium CLI.

    If no shell is specified, installation instructions for the current shell
    are displayed.

    Examples:
        mycelium completion install bash
        mycelium completion install zsh
        mycelium completion install fish
    """
    if not shell:
        # Auto-detect shell from environment
        import os
        shell_path = os.environ.get("SHELL", "")
        if "bash" in shell_path:
            shell = "bash"
        elif "zsh" in shell_path:
            shell = "zsh"
        elif "fish" in shell_path:
            shell = "fish"

    if not shell:
        click.echo("Could not auto-detect shell. Please specify shell type:")
        click.echo("  mycelium completion install bash")
        click.echo("  mycelium completion install zsh")
        click.echo("  mycelium completion install fish")
        return

    shell_lower = shell.lower()

    click.echo(f"Installing {shell_lower} completion for Mycelium CLI...\n")

    if shell_lower == "bash":
        click.echo("Add the following to your ~/.bashrc:\n")
        click.echo('eval "$(_MYCELIUM_COMPLETE=bash_source mycelium)"\n')
        click.echo("Then run: source ~/.bashrc")

    elif shell_lower == "zsh":
        click.echo("Add the following to your ~/.zshrc:\n")
        click.echo('eval "$(_MYCELIUM_COMPLETE=zsh_source mycelium)"\n')
        click.echo("Then run: source ~/.zshrc")

    elif shell_lower == "fish":
        click.echo("Add the following to ~/.config/fish/completions/mycelium.fish:\n")
        click.echo('_MYCELIUM_COMPLETE=fish_source mycelium | source\n')
        click.echo("Or run directly:")
        click.echo("  mkdir -p ~/.config/fish/completions")
        click.echo('  _MYCELIUM_COMPLETE=fish_source mycelium > ~/.config/fish/completions/mycelium.fish')

    click.echo("\nNote: Completion provides:")
    click.echo("  - Agent name suggestions for start/stop/logs commands")
    click.echo("  - Category filtering for list command")
    click.echo("  - All command and option completions")


@completion.command()
@click.argument(
    "shell",
    type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False),
    shell_complete=complete_shell_types,
)
def show(shell: str) -> None:
    """Show completion script for a specific shell.

    Examples:
        mycelium completion show bash
        mycelium completion show zsh > /tmp/completion.zsh
    """
    shell_lower = shell.lower()

    click.echo(f"# Mycelium CLI completion for {shell_lower}")
    click.echo("# Generated completion script\n")

    if shell_lower == "bash":
        click.echo('eval "$(_MYCELIUM_COMPLETE=bash_source mycelium)"')
    elif shell_lower == "zsh":
        click.echo('eval "$(_MYCELIUM_COMPLETE=zsh_source mycelium)"')
    elif shell_lower == "fish":
        click.echo('_MYCELIUM_COMPLETE=fish_source mycelium | source')


def main() -> None:
    """CLI entry point with error handling."""
    try:
        cli(obj={})
    except MyceliumError as e:
        console.print()
        print_error(str(e))
        console.print()
        raise SystemExit(1)
    except Exception as e:
        console.print()
        print_error(f"Unexpected error: {str(e)}")
        console.print("[dim]Please report this issue: https://github.com/mycelium/issues[/dim]")
        console.print()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
