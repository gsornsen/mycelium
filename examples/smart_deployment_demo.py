#!/usr/bin/env python3
"""Demonstration of smart service detection and reuse.

This script demonstrates the intelligent service deployment workflow:
1. Detects existing services (Redis, PostgreSQL)
2. Creates a smart deployment plan that reuses compatible services
3. Generates docker-compose.yml with only new services
4. Shows connection information for all services

Usage:
    python examples/smart_deployment_demo.py
"""

from pathlib import Path

from rich.console import Console
from rich.table import Table

from mycelium_onboarding.config.schema import DeploymentMethod, MyceliumConfig
from mycelium_onboarding.deployment.generator import DeploymentGenerator
from mycelium_onboarding.deployment.strategy import (
    ServiceDeploymentPlanner,
    ServiceDetector,
    ServiceStrategy,
)

console = Console()


def main():
    """Run smart deployment demonstration."""
    console.print("\n[bold blue]Smart Service Deployment Demo[/bold blue]\n")

    # Step 1: Create configuration
    console.print("[yellow]Step 1: Creating configuration...[/yellow]")
    config = MyceliumConfig(
        project_name="demo-smart-deploy",
        services={
            "redis": {"enabled": True, "port": 6379},
            "postgres": {"enabled": True, "port": 5432},
            "temporal": {"enabled": True},
        },
    )
    console.print(f"  ✓ Project: {config.project_name}")
    console.print("  ✓ Services: Redis, PostgreSQL, Temporal\n")

    # Step 2: Detect existing services
    console.print("[yellow]Step 2: Detecting existing services...[/yellow]")
    detector = ServiceDetector(scan_system=True, scan_docker=True)
    detected_services = detector.detect_all_services()

    detection_table = Table(title="Detected Services", show_header=True)
    detection_table.add_column("Service", style="cyan")
    detection_table.add_column("Status", style="green")
    detection_table.add_column("Version", style="yellow")
    detection_table.add_column("Port", style="magenta")

    for service in detected_services:
        detection_table.add_row(
            service.name,
            service.status.value,
            service.version,
            str(service.port),
        )

    console.print(detection_table)
    console.print(f"  ✓ Detected {len(detected_services)} service(s)\n")

    # Step 3: Create deployment plan
    console.print("[yellow]Step 3: Creating smart deployment plan...[/yellow]")
    planner = ServiceDeploymentPlanner(
        config=config,
        detected_services=detected_services,
        prefer_reuse=True,
    )

    deployment_plan = planner.create_deployment_plan()

    # Show deployment plan
    plan_table = Table(title="Deployment Plan", show_header=True)
    plan_table.add_column("Service", style="cyan")
    plan_table.add_column("Strategy", style="green")
    plan_table.add_column("Port", style="magenta")
    plan_table.add_column("Reason", style="white")

    for service_name, service_plan in deployment_plan.service_plans.items():
        strategy_emoji = {
            ServiceStrategy.REUSE: "🔄",
            ServiceStrategy.CREATE: "✨",
            ServiceStrategy.ALONGSIDE: "🔀",
            ServiceStrategy.SKIP: "⏭️",
        }
        emoji = strategy_emoji.get(service_plan.strategy, "❓")

        plan_table.add_row(
            f"{emoji} {service_name}",
            service_plan.strategy.value,
            str(service_plan.port),
            service_plan.reason[:60] + "..." if len(service_plan.reason) > 60 else service_plan.reason,
        )

    console.print(plan_table)

    # Show summary
    console.print(f"\n  [green]✓ Services to reuse:[/green] {', '.join(deployment_plan.services_to_reuse) or 'None'}")
    console.print(f"  [blue]✓ Services to create:[/blue] {', '.join(deployment_plan.services_to_create) or 'None'}")
    if deployment_plan.services_alongside:
        console.print(f"  [yellow]⚠ Services alongside:[/yellow] {', '.join(deployment_plan.services_alongside)}")

    # Step 4: Generate deployment files
    console.print("\n[yellow]Step 4: Generating deployment files...[/yellow]")
    output_dir = Path("/tmp/demo-smart-deploy")
    output_dir.mkdir(parents=True, exist_ok=True)

    generator = DeploymentGenerator(
        config=config,
        output_dir=output_dir,
        deployment_plan=deployment_plan,
    )

    result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

    if result.success:
        console.print(f"  [green]✓ Generated {len(result.files_generated)} file(s):[/green]")
        for file_path in result.files_generated:
            console.print(f"    - {file_path}")

        if result.warnings:
            console.print("\n  [yellow]⚠ Warnings:[/yellow]")
            for warning in result.warnings:
                console.print(f"    • {warning}")

        # Show docker-compose.yml preview
        console.print("\n[yellow]Step 5: Docker Compose Preview[/yellow]")
        compose_file = output_dir / "docker-compose.yml"
        if compose_file.exists():
            content = compose_file.read_text()
            lines = content.split("\n")[:30]  # Show first 30 lines
            console.print("[dim]" + "\n".join(lines) + "\n...[/dim]")

        # Show connection information
        console.print("\n[yellow]Step 6: Connection Information[/yellow]")
        conn_table = Table(title="Service Connections", show_header=True)
        conn_table.add_column("Service", style="cyan")
        conn_table.add_column("Connection String", style="green")

        for service_name, service_plan in deployment_plan.service_plans.items():
            conn_table.add_row(
                service_name,
                service_plan.connection_string,
            )

        console.print(conn_table)

        console.print("\n[bold green]✓ Smart deployment complete![/bold green]")
        console.print(f"[dim]Generated files in: {output_dir}[/dim]\n")

        # Show recommendations
        if deployment_plan.recommendations:
            console.print("[bold yellow]Recommendations:[/bold yellow]")
            for rec in deployment_plan.recommendations:
                console.print(f"  • {rec}")

    else:
        console.print("[bold red]✗ Deployment failed![/bold red]")
        for error in result.errors:
            console.print(f"  • {error}")


if __name__ == "__main__":
    main()
