"""Rich output helpers for Mycelium CLI.

Provides beautiful, colorful terminal output using the Rich library.
Handles tables, status indicators, panels, spinners, and progress bars.
"""


from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table

from mycelium.discovery.scanner import DiscoveredAgent
from mycelium.registry.client import AgentInfo

# Create console instance for consistent output
console = Console()


def get_status_indicator(status: str) -> str:
    """Get colored status indicator for agent status.

    Args:
        status: Agent status ("healthy", "starting", "stopping", "unhealthy", etc.)

    Returns:
        Colored unicode indicator (green, yellow, red, or gray)
    """
    status_lower = status.lower()
    if status_lower == "healthy":
        return "[green]●[/green]"
    if status_lower in ("starting", "stopping"):
        return "[yellow]◐[/yellow]"
    if status_lower in ("unhealthy", "stopped"):
        return "[red]○[/red]"
    return "[dim]?[/dim]"


def create_agent_table(agents: list[AgentInfo], category_filter: str | None = None) -> Table:
    """Create a Rich table for agent listing.

    Args:
        agents: List of agent info objects
        category_filter: Optional category filter to show in title

    Returns:
        Rich Table object ready to display
    """
    title = "Agents"
    if category_filter:
        title = f"Agents (Category: {category_filter})"

    table = Table(
        title=title,
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Status", justify="center", style="", width=8)
    table.add_column("Agent", style="bold", no_wrap=True)
    table.add_column("Category", style="magenta")
    table.add_column("Description", style="dim")

    for agent in agents:
        status_icon = get_status_indicator(agent.status)
        description = agent.description or ""
        if len(description) > 60:
            description = description[:57] + "..."

        table.add_row(
            status_icon,
            agent.name,
            agent.category,
            description,
        )

    return table


def create_registry_status_panel(
    is_healthy: bool,
    stats: dict[str, int] | None = None,
    plugin_dir: str | None = None,
) -> Panel:
    """Create a Rich panel for registry status display.

    Args:
        is_healthy: Whether registry is healthy
        stats: Optional statistics dictionary with agent_count and active_count
        plugin_dir: Optional plugin directory path to display

    Returns:
        Rich Panel object ready to display
    """
    if is_healthy:
        status_line = f"{get_status_indicator('healthy')} Registry: [bold green]Healthy[/bold green]"
        content_lines = [status_line]

        if stats:
            content_lines.append(f"Registered: [cyan]{stats['agent_count']}[/cyan] agents")
            content_lines.append(f"Active: [green]{stats['active_count']}[/green] agents")

        if plugin_dir:
            content_lines.append("")
            content_lines.append(f"[dim]Plugin directory: {plugin_dir}[/dim]")
            content_lines.append("[dim]Run 'mycelium agent discover' to scan for new agents[/dim]")

        content = "\n".join(content_lines)
        border_style = "green"
    else:
        status_line = f"{get_status_indicator('unhealthy')} Registry: [bold red]Unhealthy[/bold red]"
        content_lines = [
            status_line,
            "",
            "[yellow]Suggestion:[/yellow] Check if Redis is running:",
            "[dim]  redis-cli ping[/dim]",
        ]
        content = "\n".join(content_lines)
        border_style = "red"

    return Panel(
        content,
        title="[bold]Agent Registry Status[/bold]",
        border_style=border_style,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def print_agent_table(agents: list[AgentInfo], category_filter: str | None = None) -> None:
    """Print agent table to console.

    Args:
        agents: List of agent info objects
        category_filter: Optional category filter
    """
    table = create_agent_table(agents, category_filter)
    console.print()
    console.print(table)
    console.print()


def print_registry_status(
    is_healthy: bool,
    stats: dict[str, int] | None = None,
    plugin_dir: str | None = None,
) -> None:
    """Print registry status panel to console.

    Args:
        is_healthy: Whether registry is healthy
        stats: Optional statistics dictionary
        plugin_dir: Optional plugin directory path
    """
    panel = create_registry_status_panel(is_healthy, stats, plugin_dir)
    console.print()
    console.print(panel)
    console.print()


def print_success(message: str) -> None:
    """Print success message with green indicator.

    Args:
        message: Success message to display
    """
    console.print(f"[green]✓[/green] {message}")


def print_info(message: str) -> None:
    """Print info message with cyan color.

    Args:
        message: Info message to display
    """
    console.print(f"[cyan]ℹ[/cyan] {message}")


def print_warning(message: str) -> None:
    """Print warning message with yellow color.

    Args:
        message: Warning message to display
    """
    console.print(f"[yellow]⚠[/yellow] {message}")


def print_error(message: str) -> None:
    """Print error message with red color.

    Args:
        message: Error message to display
    """
    console.print(f"[red]✗[/red] {message}")


def create_spinner(text: str) -> Live:
    """Create a Rich spinner for long operations.

    Args:
        text: Text to display next to spinner

    Returns:
        Rich Live object with spinner (use with context manager)

    Example:
        with create_spinner("Loading..."):
            # Do work
            pass
    """
    spinner = Spinner("dots", text=text, style="cyan")
    return Live(spinner, console=console, transient=True)


def print_discovery_summary(
    discovered_count: int,
    registered_count: int,
    agents: list[AgentInfo | DiscoveredAgent],
) -> None:
    """Print discovery operation summary.

    Args:
        discovered_count: Number of agents discovered
        registered_count: Number of agents registered
        agents: List of discovered agents (AgentInfo or DiscoveredAgent)
    """
    console.print()
    if discovered_count == 0:
        print_info("No agents found.")
        return

    console.print(f"[bold cyan]Discovered {discovered_count} agent(s):[/bold cyan]\n")

    for agent in agents:
        console.print(f"  {get_status_indicator('healthy')} [bold]{agent.name}[/bold]")
        console.print(f"     Category: [magenta]{agent.category}[/magenta]")
        if agent.description:
            console.print(f"     [dim]{agent.description}[/dim]")
        console.print()

    if registered_count > 0:
        print_success(f"Registered {registered_count} agent(s) in registry")
    console.print()


def print_agent_started(name: str, process_id: int | str) -> None:
    """Print agent start confirmation.

    Args:
        name: Agent name
        process_id: Process ID (can be int or str)
    """
    console.print()
    print_success(f"Agent '{name}' started successfully")
    console.print(f"  Process ID: [cyan]{process_id}[/cyan]")
    console.print()
    console.print("[dim]Monitor logs:[/dim]")
    console.print(f"  [bold]mycelium agent logs {name}[/bold]")
    console.print()


def print_agent_stopped(name: str) -> None:
    """Print agent stop confirmation.

    Args:
        name: Agent name
    """
    console.print()
    print_success(f"Agent '{name}' stopped")
    console.print()
