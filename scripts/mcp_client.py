#!/usr/bin/env python3
"""Interactive MCP test client for Mycelium agent discovery and execution.

This tool provides a user-friendly interface for testing and validating
the Mycelium MCP server during development.

Usage:
    # Interactive mode (default)
    uv run python scripts/mcp_client.py

    # Command mode
    uv run python scripts/mcp_client.py discover "Python backend"
    uv run python scripts/mcp_client.py invoke python-pro "Build a CLI tool"
    uv run python scripts/mcp_client.py status wf_abc123

    # Verbose mode
    uv run python scripts/mcp_client.py --verbose discover "React"
"""

import argparse
import asyncio
import json
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.table import Table

console = Console()


class MCPClient:
    """MCP client for communicating with Mycelium MCP server via stdio."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialize MCP client.

        Args:
            verbose: Enable verbose logging of JSON-RPC messages
        """
        self.verbose = verbose
        self.session: ClientSession | None = None
        self.last_workflow_id: str | None = None

    async def connect(self) -> None:
        """Start the MCP server and establish connection."""
        if self.verbose:
            console.print("[dim]Starting MCP server...[/dim]")

        # Create server parameters for stdio transport
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "mycelium.mcp.server"],
            env=None,
        )

        # Connect using stdio client
        # The stdio_client context manager handles the connection lifecycle
        self.stdio_context = stdio_client(server_params)
        self.read, self.write = await self.stdio_context.__aenter__()

        # Initialize the session
        self.session = ClientSession(self.read, self.write)
        await self.session.__aenter__()

        # Initialize the connection
        await self.session.initialize()

        if self.verbose:
            console.print("[dim]MCP server connected[/dim]")

    async def disconnect(self) -> None:
        """Stop the MCP server and close connection."""
        if self.session:
            await self.session.__aexit__(None, None, None)
        if hasattr(self, "stdio_context"):
            await self.stdio_context.__aexit__(None, None, None)
        if self.verbose:
            console.print("[dim]MCP server disconnected[/dim]")

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call an MCP tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result

        Raises:
            RuntimeError: If not connected
        """
        if not self.session:
            raise RuntimeError("MCP server not connected. Call connect() first.")

        if self.verbose:
            console.print(f"\n[bold cyan]Calling tool:[/bold cyan] {tool_name}")
            console.print(JSON(json.dumps(arguments, indent=2)))

        # Call the tool
        result = await self.session.call_tool(tool_name, arguments)

        if self.verbose:
            console.print("\n[bold cyan]Tool result:[/bold cyan]")
            console.print(JSON(json.dumps(result.model_dump(), indent=2)))

        # Extract content from MCP response
        if result.content:
            # Handle list of content items
            for item in result.content:
                if hasattr(item, "text"):
                    # Parse JSON text content
                    try:
                        return json.loads(item.text)
                    except json.JSONDecodeError:
                        return item.text

        return result.model_dump()

    async def discover_agents(self, query: str) -> list[dict[str, Any]]:
        """Search for agents using natural language query.

        Args:
            query: Search query

        Returns:
            List of matching agents
        """
        return await self.call_tool("discover_agents", {"query": query})

    async def get_agent_details(self, name: str) -> dict[str, Any]:
        """Get full metadata for a specific agent.

        Args:
            name: Agent name

        Returns:
            Agent details dictionary
        """
        return await self.call_tool("get_agent_details", {"name": name})

    async def list_categories(self) -> list[dict[str, Any]]:
        """List all available agent categories.

        Returns:
            List of categories with counts
        """
        return await self.call_tool("list_categories", {})

    async def invoke_agent(
        self, agent_name: str, task_description: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Invoke an agent to execute a task.

        Args:
            agent_name: Name of agent to invoke
            task_description: Task description
            context: Optional context dictionary

        Returns:
            Invocation result with workflow_id
        """
        args = {"agent_name": agent_name, "task_description": task_description}
        if context:
            args["context"] = context

        result = await self.call_tool("invoke_agent", args)

        # Store workflow_id for easy status checks
        if isinstance(result, dict) and result.get("workflow_id"):
            self.last_workflow_id = result["workflow_id"]

        return result

    async def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
        """Get status of a running workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow status dictionary
        """
        return await self.call_tool("get_workflow_status", {"workflow_id": workflow_id})


class InteractiveCLI:
    """Interactive CLI for MCP testing."""

    def __init__(self, client: MCPClient) -> None:
        """Initialize interactive CLI.

        Args:
            client: MCP client instance
        """
        self.client = client

    def show_welcome(self) -> None:
        """Display welcome message."""
        welcome = """
[bold green]Mycelium MCP Test Client[/bold green]
[dim]Interactive testing tool for MCP server[/dim]

[bold]Commands:[/bold]
  [cyan]discover <query>[/cyan]     - Search for agents
  [cyan]details <name>[/cyan]       - Get agent details
  [cyan]categories[/cyan]           - List categories
  [cyan]invoke <name> <task>[/cyan] - Invoke agent
  [cyan]status [workflow_id][/cyan] - Check workflow status
  [cyan]last[/cyan]                 - Show last workflow_id
  [cyan]help[/cyan]                 - Show this help
  [cyan]quit[/cyan] / [cyan]exit[/cyan]         - Exit

[bold]Shortcuts:[/bold]
  [cyan]d[/cyan] = discover, [cyan]i[/cyan] = invoke, [cyan]s[/cyan] = status, [cyan]c[/cyan] = categories
        """
        console.print(Panel(welcome, border_style="green"))

    async def run(self) -> None:
        """Run interactive REPL loop."""
        self.show_welcome()

        while True:
            try:
                # Prompt for command
                command_input = Prompt.ask("\n[bold cyan]>[/bold cyan]")

                if not command_input.strip():
                    continue

                # Parse command
                parts = command_input.strip().split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                # Handle shortcuts
                command_map = {
                    "d": "discover",
                    "i": "invoke",
                    "s": "status",
                    "c": "categories",
                    "h": "help",
                    "q": "quit",
                }
                command = command_map.get(command, command)

                # Execute command
                if command in ("quit", "exit"):
                    console.print("[dim]Goodbye![/dim]")
                    break
                elif command == "help":
                    self.show_welcome()
                elif command == "discover":
                    await self.cmd_discover(args)
                elif command == "details":
                    await self.cmd_details(args)
                elif command == "categories":
                    await self.cmd_categories()
                elif command == "invoke":
                    await self.cmd_invoke(args)
                elif command == "status":
                    await self.cmd_status(args)
                elif command == "last":
                    self.cmd_last()
                else:
                    console.print(f"[red]Unknown command: {command}[/red]")
                    console.print("[dim]Type 'help' for available commands[/dim]")

            except KeyboardInterrupt:
                console.print("\n[dim]Use 'quit' to exit[/dim]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    async def cmd_discover(self, query: str) -> None:
        """Execute discover command.

        Args:
            query: Search query
        """
        if not query:
            query = Prompt.ask("Enter search query")

        console.print(f"\n[dim]Searching for: {query}[/dim]")

        try:
            agents = await self.client.discover_agents(query)

            if not agents:
                console.print("[yellow]No agents found[/yellow]")
                return

            # Display results in a table
            table = Table(title=f"Found {len(agents)} agent(s)", show_header=True)
            table.add_column("Name", style="cyan")
            table.add_column("Category", style="magenta")
            table.add_column("Description", style="white")

            for agent in agents:
                desc = agent.get("description", "")
                truncated_desc = desc[:80] + "..." if len(desc) > 80 else desc
                table.add_row(
                    agent.get("name", ""),
                    agent.get("category", ""),
                    truncated_desc,
                )

            console.print(table)

        except Exception as e:
            console.print(f"[red]Discovery failed: {e}[/red]")

    async def cmd_details(self, name: str) -> None:
        """Execute details command.

        Args:
            name: Agent name
        """
        if not name:
            name = Prompt.ask("Enter agent name")

        console.print(f"\n[dim]Getting details for: {name}[/dim]")

        try:
            details = await self.client.get_agent_details(name)

            if details.get("error"):
                console.print(f"[red]{details['error']}[/red]")
                return

            # Display agent details
            tools_str = ", ".join(details.get("tools", [])) if details.get("tools") else "None"
            panel_content = f"""[bold]Name:[/bold] {details.get('name', 'N/A')}
[bold]Category:[/bold] {details.get('category', 'N/A')}

[bold]Description:[/bold]
{details.get('description', 'N/A')}

[bold]Tools:[/bold]
{tools_str}

[bold]Command:[/bold]
{details.get('command', 'N/A')}
"""
            console.print(Panel(panel_content, title=f"Agent: {name}", border_style="cyan"))

        except Exception as e:
            console.print(f"[red]Failed to get details: {e}[/red]")

    async def cmd_categories(self) -> None:
        """Execute categories command."""
        console.print("\n[dim]Listing categories...[/dim]")

        try:
            categories = await self.client.list_categories()

            if not categories:
                console.print("[yellow]No categories found[/yellow]")
                return

            # Display categories in a table
            table = Table(title="Agent Categories", show_header=True)
            table.add_column("Category", style="cyan")
            table.add_column("Count", style="magenta", justify="right")

            for cat in categories:
                table.add_row(cat.get("category", ""), str(cat.get("count", 0)))

            console.print(table)

        except Exception as e:
            console.print(f"[red]Failed to list categories: {e}[/red]")

    async def cmd_invoke(self, args: str) -> None:
        """Execute invoke command.

        Args:
            args: Agent name and task description
        """
        if not args:
            agent_name = Prompt.ask("Enter agent name")
            task_description = Prompt.ask("Enter task description")
        else:
            # Parse agent name and task
            parts = args.split(maxsplit=1)
            if len(parts) < 2:
                console.print("[red]Usage: invoke <agent_name> <task_description>[/red]")
                return
            agent_name, task_description = parts

        console.print(f"\n[dim]Invoking agent: {agent_name}[/dim]")
        console.print(f"[dim]Task: {task_description}[/dim]")

        try:
            result = await self.client.invoke_agent(agent_name, task_description)

            # Check for high-risk warning
            if result.get("risk_level") == "high":
                console.print("[yellow]HIGH RISK AGENT - Consent required[/yellow]")

            # Display result
            if result.get("status") == "started":
                panel_content = f"""[bold green]Workflow Started[/bold green]

[bold]Workflow ID:[/bold] {result.get('workflow_id')}
[bold]Agent:[/bold] {result.get('agent_name')}
[bold]Status:[/bold] {result.get('status')}
[bold]PID:[/bold] {result.get('pid', 'N/A')}
[bold]Risk Level:[/bold] {result.get('risk_level', 'N/A')}

{result.get('message', '')}
"""
                console.print(Panel(panel_content, border_style="green"))
            else:
                panel_content = f"""[bold red]Invocation Failed[/bold red]

[bold]Agent:[/bold] {result.get('agent_name')}
[bold]Status:[/bold] {result.get('status')}
[bold]Error:[/bold] {result.get('error', result.get('message', 'Unknown error'))}
"""
                console.print(Panel(panel_content, border_style="red"))

        except Exception as e:
            console.print(f"[red]Invocation failed: {e}[/red]")

    async def cmd_status(self, workflow_id: str) -> None:
        """Execute status command.

        Args:
            workflow_id: Workflow ID (optional, uses last if not provided)
        """
        if not workflow_id:
            if self.client.last_workflow_id:
                workflow_id = self.client.last_workflow_id
                console.print(f"[dim]Using last workflow: {workflow_id}[/dim]")
            else:
                console.print("[yellow]No workflow ID provided and no previous workflow found[/yellow]")
                console.print("[dim]Usage: status <workflow_id>[/dim]")
                return

        console.print(f"\n[dim]Checking status for: {workflow_id}[/dim]")

        try:
            status = await self.client.get_workflow_status(workflow_id)

            # Display status
            if status.get("status") == "not_found":
                console.print(f"[red]Workflow not found: {workflow_id}[/red]")
                return

            # Color-code status
            status_text = status.get("status", "unknown")
            if status_text == "running":
                status_color = "yellow"
            elif status_text == "completed":
                status_color = "green"
            elif status_text == "failed":
                status_color = "red"
            else:
                status_color = "white"

            panel_content = f"""[bold]Workflow ID:[/bold] {status.get('workflow_id')}
[bold]Status:[/bold] [{status_color}]{status_text}[/{status_color}]
[bold]Agent:[/bold] {status.get('agent_name', 'N/A')}
[bold]Task:[/bold] {status.get('task', 'N/A')}
[bold]Started:[/bold] {status.get('started_at', 'N/A')}
"""

            if status.get("completed_at"):
                panel_content += f"[bold]Completed:[/bold] {status['completed_at']}\n"

            if status.get("error"):
                panel_content += f"\n[bold red]Error:[/bold red] {status['error']}\n"
                if status.get("exit_code") is not None:
                    panel_content += f"[bold]Exit Code:[/bold] {status['exit_code']}\n"

            console.print(Panel(panel_content, title="Workflow Status", border_style=status_color))

        except Exception as e:
            console.print(f"[red]Failed to get status: {e}[/red]")

    def cmd_last(self) -> None:
        """Display last workflow ID."""
        if self.client.last_workflow_id:
            console.print(f"\n[bold]Last workflow ID:[/bold] [cyan]{self.client.last_workflow_id}[/cyan]")
        else:
            console.print("\n[yellow]No previous workflow found[/yellow]")


async def async_main(args: argparse.Namespace) -> None:
    """Async main entry point.

    Args:
        args: Parsed command-line arguments
    """
    # Create client
    client = MCPClient(verbose=args.verbose)

    try:
        # Connect to server
        await client.connect()

        # Direct command mode
        if args.command:
            if args.command == "discover":
                agents = await client.discover_agents(args.query)
                console.print(JSON(json.dumps(agents, indent=2)))

            elif args.command == "details":
                details = await client.get_agent_details(args.name)
                console.print(JSON(json.dumps(details, indent=2)))

            elif args.command == "categories":
                categories = await client.list_categories()
                console.print(JSON(json.dumps(categories, indent=2)))

            elif args.command == "invoke":
                result = await client.invoke_agent(args.agent_name, args.task)
                console.print(JSON(json.dumps(result, indent=2)))

            elif args.command == "status":
                status = await client.get_workflow_status(args.workflow_id)
                console.print(JSON(json.dumps(status, indent=2)))

        # Interactive mode
        else:
            cli = InteractiveCLI(client)
            await cli.run()

    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted[/dim]")
        sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if args.verbose:
            import traceback

            console.print(Syntax(traceback.format_exc(), "python", theme="monokai"))
        sys.exit(1)

    finally:
        await client.disconnect()


def main() -> None:
    """Main entry point for MCP test client."""
    parser = argparse.ArgumentParser(
        description="Mycelium MCP Test Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  %(prog)s

  # Direct commands
  %(prog)s discover "Python backend"
  %(prog)s details python-pro
  %(prog)s categories
  %(prog)s invoke python-pro "Build a CLI tool"
  %(prog)s status wf_abc123

  # Verbose mode
  %(prog)s --verbose discover "React"
        """,
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose JSON-RPC logging")

    # Subcommands for direct mode
    subparsers = parser.add_subparsers(dest="command", help="Direct command (optional)")

    # discover command
    discover_parser = subparsers.add_parser("discover", help="Search for agents")
    discover_parser.add_argument("query", help="Search query")

    # details command
    details_parser = subparsers.add_parser("details", help="Get agent details")
    details_parser.add_argument("name", help="Agent name")

    # categories command
    subparsers.add_parser("categories", help="List agent categories")

    # invoke command
    invoke_parser = subparsers.add_parser("invoke", help="Invoke an agent")
    invoke_parser.add_argument("agent_name", help="Agent name")
    invoke_parser.add_argument("task", help="Task description")

    # status command
    status_parser = subparsers.add_parser("status", help="Check workflow status")
    status_parser.add_argument("workflow_id", help="Workflow ID")

    args = parser.parse_args()

    # Run async main
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
