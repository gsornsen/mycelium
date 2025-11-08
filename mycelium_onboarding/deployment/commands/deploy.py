"""Unified deployment command implementation.

This module provides the complete `mycelium deploy` command suite that handles
auto-detection, planning, generation, and service lifecycle management. It works
from any directory and integrates with smart service detection.

Features:
    - Smart service detection and reuse
    - Automatic deployment planning
    - Multi-method deployment (Docker, Kubernetes, systemd)
    - Dry-run mode for safe testing
    - Force mode for override scenarios
    - Rich progress indicators and error messages
    - Works from any directory context
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import click
from pydantic import BaseModel, Field
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from mycelium_onboarding.config.manager import ConfigManager
from mycelium_onboarding.config.schema import DeploymentMethod, MyceliumConfig
from mycelium_onboarding.deployment.generator import DeploymentGenerator
from mycelium_onboarding.deployment.secrets import SecretsManager
from mycelium_onboarding.deployment.strategy import DeploymentPlanSummary
from mycelium_onboarding.deployment.strategy.detector import (
    DetectedService,
    ServiceDetector,
    ServiceStatus,
)
from mycelium_onboarding.deployment.strategy.planner import ServiceDeploymentPlanner
from mycelium_onboarding.xdg_dirs import get_data_dir

logger = logging.getLogger(__name__)
console = Console()


class DeploymentPhase(str, Enum):
    """Phases of the deployment process."""

    DETECTION = "detection"
    PLANNING = "planning"
    VALIDATION = "validation"
    GENERATION = "generation"
    DEPLOYMENT = "deployment"
    STARTUP = "startup"
    VERIFICATION = "verification"
    COMPLETE = "complete"


class DeploymentStatus(str, Enum):
    """Status of a deployment operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DeploymentStep:
    """Represents a single deployment step."""

    name: str
    phase: DeploymentPhase
    description: str
    status: DeploymentStatus = DeploymentStatus.PENDING
    start_time: datetime | None = None
    end_time: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None

    def execute(self) -> bool:
        """Execute the deployment step.

        Returns:
            True if successful, False otherwise
        """
        self.start_time = datetime.now()
        self.status = DeploymentStatus.IN_PROGRESS

        try:
            # Step execution logic would go here
            # For now, simulate with a small delay
            time.sleep(0.5)
            self.status = DeploymentStatus.SUCCESS
            self.end_time = datetime.now()
            return True
        except Exception as e:
            self.status = DeploymentStatus.FAILED
            self.error = str(e)
            self.end_time = datetime.now()
            return False

    @property
    def duration(self) -> float | None:
        """Get step execution duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class DeploymentPlan(BaseModel):
    """Deployment plan generated from detection results."""

    plan_id: str = Field(description="Unique plan identifier")
    created_at: datetime = Field(default_factory=datetime.now, description="Plan creation time")
    detected_services: list[DetectedService] = Field(default_factory=list, description="Detected services")
    reusable_services: list[str] = Field(default_factory=list, description="Services that will be reused")
    new_services: list[str] = Field(default_factory=list, description="Services to be deployed")
    deployment_steps: list[DeploymentStep] = Field(default_factory=list, description="Ordered deployment steps")
    estimated_duration: int = Field(default=0, description="Estimated duration in seconds")
    configuration: dict[str, Any] = Field(default_factory=dict, description="Deployment configuration")
    smart_plan: DeploymentPlanSummary | None = Field(default=None, description="Smart deployment plan with strategies")

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True

    def add_step(self, step: DeploymentStep) -> None:
        """Add a deployment step to the plan."""
        self.deployment_steps.append(step)
        # Update estimated duration (rough estimate)
        self.estimated_duration += 5  # 5 seconds per step average

    def get_current_phase(self) -> DeploymentPhase:
        """Get the current deployment phase."""
        for step in self.deployment_steps:
            if step.status in [DeploymentStatus.PENDING, DeploymentStatus.IN_PROGRESS]:
                return step.phase
        return DeploymentPhase.COMPLETE

    def get_progress(self) -> float:
        """Get deployment progress as percentage."""
        if not self.deployment_steps:
            return 0.0
        completed = sum(
            1 for step in self.deployment_steps if step.status in [DeploymentStatus.SUCCESS, DeploymentStatus.SKIPPED]
        )
        return (completed / len(self.deployment_steps)) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert plan to dictionary for serialization."""
        return {
            "plan_id": self.plan_id,
            "created_at": self.created_at.isoformat(),
            "detected_services": [s.dict() for s in self.detected_services],
            "reusable_services": self.reusable_services,
            "new_services": self.new_services,
            "steps": [
                {
                    "name": step.name,
                    "phase": step.phase.value,
                    "status": step.status.value,
                    "duration": step.duration,
                }
                for step in self.deployment_steps
            ],
            "progress": self.get_progress(),
            "estimated_duration": self.estimated_duration,
        }


class DeployCommand:
    """Unified deployment command handler with smart service management."""

    def __init__(
        self, verbose: bool = False, dry_run: bool = False, force: bool = False, working_dir: Path | None = None
    ):
        """Initialize deployment command.

        Args:
            verbose: Enable verbose output
            dry_run: Perform dry run without actual deployment
            force: Force operations, override safety checks
            working_dir: Working directory context (auto-detected if None)
        """
        self.verbose = verbose
        self.dry_run = dry_run
        self.force = force
        self.working_dir = working_dir or Path.cwd()
        self.detector = ServiceDetector()
        self.current_plan: DeploymentPlan | None = None
        self.config: MyceliumConfig | None = None
        self.deployment_dir: Path | None = None

    def _load_or_find_config(self) -> MyceliumConfig:
        """Load configuration from current context or find it.

        Returns:
            MyceliumConfig instance

        Raises:
            click.ClickException: If config cannot be loaded
        """
        if self.config:
            return self.config

        # Try to load from config manager
        manager = ConfigManager()
        try:
            self.config = manager.load()
            return self.config
        except Exception as e:
            if self.verbose:
                console.print(f"[dim]Config load error: {e}[/dim]")
            raise click.ClickException("Configuration not found. Run 'mycelium init' to create one.")

    def _get_deployment_dir(self) -> Path:
        """Get deployment directory based on config and context.

        Returns:
            Path to deployment directory
        """
        if self.deployment_dir:
            return self.deployment_dir

        config = self._load_or_find_config()
        self.deployment_dir = get_data_dir() / "deployments" / config.project_name
        return self.deployment_dir

    def _save_deployment_plan(self, plan: DeploymentPlan) -> None:
        """Save deployment plan to disk for status command.

        Args:
            plan: DeploymentPlan to persist
        """
        deployment_dir = self._get_deployment_dir()
        plan_file = deployment_dir / "deployment_plan.json"

        # Convert plan to JSON-serializable format
        plan_data = {
            "plan_id": plan.plan_id,
            "created_at": plan.created_at.isoformat(),
            "new_services": plan.new_services,
            "reusable_services": plan.reusable_services,
            "estimated_duration": plan.estimated_duration,
            "smart_plan": None,  # Will serialize separately
        }

        # Add smart plan details if available
        if plan.smart_plan:
            plan_data["smart_plan"] = {
                "plan_id": plan.smart_plan.plan_id,
                "project_name": plan.smart_plan.project_name,
                "created_at": plan.smart_plan.created_at.isoformat(),
                "service_plans": {
                    service_name: {
                        "service_name": p.service_name,
                        "strategy": p.strategy.value,
                        "host": p.host,
                        "port": p.port,
                        "version": p.version,
                        "connection_string": p.connection_string,
                        "reason": p.reason,
                    }
                    for service_name, p in plan.smart_plan.service_plans.items()
                },
            }

        # Save to file
        with open(plan_file, "w") as f:
            json.dump(plan_data, f, indent=2)

        logger.debug(f"Saved deployment plan to {plan_file}")

    def _load_deployment_plan(self) -> DeploymentPlan | None:
        """Load deployment plan from disk.

        Returns:
            DeploymentPlan if found, None otherwise
        """
        try:
            deployment_dir = self._get_deployment_dir()
            plan_file = deployment_dir / "deployment_plan.json"

            if not plan_file.exists():
                logger.debug(f"No deployment plan found at {plan_file}")
                return None

            with open(plan_file) as f:
                plan_data = json.load(f)

            # Reconstruct smart plan if available
            from mycelium_onboarding.deployment.strategy.service_strategy import (
                DeploymentPlanSummary,
                ServiceDeploymentPlan,
                ServiceStrategy,
            )

            smart_plan = None
            if plan_data.get("smart_plan"):
                smart_plan_data = plan_data["smart_plan"]
                service_plans = {}
                for service_name, p_data in smart_plan_data["service_plans"].items():
                    service_plans[service_name] = ServiceDeploymentPlan(
                        service_name=p_data["service_name"],
                        strategy=ServiceStrategy(p_data["strategy"]),
                        host=p_data["host"],
                        port=p_data["port"],
                        version=p_data["version"],
                        connection_string=p_data["connection_string"],
                        reason=p_data["reason"],
                    )
                smart_plan = DeploymentPlanSummary(
                    plan_id=smart_plan_data["plan_id"],
                    project_name=smart_plan_data["project_name"],
                    created_at=datetime.fromisoformat(smart_plan_data["created_at"]),
                    service_plans=service_plans,
                )

            # Reconstruct DeploymentPlan
            plan = DeploymentPlan(
                plan_id=plan_data["plan_id"],
                created_at=datetime.fromisoformat(plan_data["created_at"]),
                new_services=plan_data["new_services"],
                reusable_services=plan_data["reusable_services"],
                estimated_duration=plan_data["estimated_duration"],
                smart_plan=smart_plan,
            )

            logger.debug(f"Loaded deployment plan from {plan_file}")
            return plan

        except Exception as e:
            logger.warning(f"Failed to load deployment plan: {e}")
            return None

    async def start(
        self,
        auto_approve: bool = False,
        config_file: Path | None = None,
        services: list[str] | None = None,
        method: str | None = None,
    ) -> bool:
        """Execute the complete deployment start process.

        This is the main "deploy start" command that:
        1. Detects existing services
        2. Creates deployment plan
        3. Generates configurations
        4. Starts services

        Args:
            auto_approve: Skip confirmation prompts
            config_file: Optional configuration file
            services: Optional list of specific services to deploy
            method: Optional deployment method override

        Returns:
            True if deployment successful, False otherwise
        """
        console.print("\n[bold blue]Starting Mycelium Deployment[/bold blue]\n")

        # Phase 1: Detection
        console.print("[yellow]Phase 1: Service Detection[/yellow]")
        detected_services = await self._detect_services()

        # Phase 2: Load config and determine method
        config = self._load_or_find_config()
        deploy_method = DeploymentMethod(method) if method else config.deployment.method

        console.print(f"[cyan]Deployment Method:[/cyan] {deploy_method.value}")
        console.print(f"[cyan]Project:[/cyan] {config.project_name}\n")

        # Phase 3: Planning (NOW USING SMART PLANNER)
        console.print("[yellow]Phase 2: Deployment Planning[/yellow]")
        plan = await self._create_deployment_plan(detected_services, services, config_file)
        self.current_plan = plan

        # Show plan summary
        self._display_plan_summary(plan)

        # Phase 4: Confirmation
        if not auto_approve and not self.dry_run:
            if not self._confirm_deployment():
                console.print("\n[yellow]Deployment cancelled by user.[/yellow]")
                return False

        if self.dry_run:
            console.print("\n[cyan]Dry run mode - no actual deployment will occur.[/cyan]")
            return True

        # Phase 5: Generate configurations (NOW WITH SMART PLAN)
        console.print("\n[yellow]Phase 3: Generating Configurations[/yellow]")
        if not await self._generate_configs(config, deploy_method):
            console.print("\n[bold red]Configuration generation failed.[/bold red]")
            return False

        # Phase 6: Execute deployment
        console.print("\n[yellow]Phase 4: Starting Services[/yellow]")
        success = await self._execute_deployment(plan, deploy_method)

        if success:
            # Save deployment plan for status command
            self._save_deployment_plan(plan)
            console.print("\n[bold green]✓ Deployment completed successfully![/bold green]")
            self._display_deployment_summary(plan)
        else:
            console.print("\n[bold red]✗ Deployment failed. Check logs for details.[/bold red]")

        return success

    async def stop(self, method: str | None = None, remove_data: bool = False) -> bool:
        """Stop all deployed services.

        Args:
            method: Optional deployment method override
            remove_data: Whether to remove data volumes/directories

        Returns:
            True if successful, False otherwise
        """
        console.print("\n[bold yellow]Stopping Mycelium Services[/bold yellow]\n")

        config = self._load_or_find_config()
        deploy_method = DeploymentMethod(method) if method else config.deployment.method

        console.print(f"[cyan]Method:[/cyan] {deploy_method.value}")
        console.print(f"[cyan]Project:[/cyan] {config.project_name}\n")

        if remove_data and not self.force:
            if not click.confirm("This will remove all data. Are you sure?", default=False):
                console.print("[yellow]Operation cancelled.[/yellow]")
                return False

        try:
            deployment_dir = self._get_deployment_dir()

            if deploy_method == DeploymentMethod.DOCKER_COMPOSE:
                await self._stop_docker_compose(deployment_dir, remove_data)
            elif deploy_method == DeploymentMethod.KUBERNETES:
                await self._stop_kubernetes(config.project_name, remove_data)
            elif deploy_method == DeploymentMethod.SYSTEMD:
                await self._stop_systemd(config, remove_data)

            console.print("\n[bold green]✓ Services stopped successfully![/bold green]")
            return True

        except Exception as e:
            console.print(f"\n[bold red]✗ Error stopping services: {e}[/bold red]")
            if self.verbose:
                logger.exception("Stop operation failed")
            return False

    async def restart(self, method: str | None = None, services: list[str] | None = None) -> bool:
        """Restart deployed services.

        Args:
            method: Optional deployment method override
            services: Optional list of specific services to restart

        Returns:
            True if successful, False otherwise
        """
        console.print("\n[bold yellow]Restarting Mycelium Services[/bold yellow]\n")

        config = self._load_or_find_config()
        deploy_method = DeploymentMethod(method) if method else config.deployment.method

        console.print(f"[cyan]Method:[/cyan] {deploy_method.value}")
        console.print(f"[cyan]Project:[/cyan] {config.project_name}\n")

        try:
            deployment_dir = self._get_deployment_dir()

            if deploy_method == DeploymentMethod.DOCKER_COMPOSE:
                await self._restart_docker_compose(deployment_dir, services)
            elif deploy_method == DeploymentMethod.KUBERNETES:
                await self._restart_kubernetes(config.project_name, services)
            elif deploy_method == DeploymentMethod.SYSTEMD:
                await self._restart_systemd(config, services)

            console.print("\n[bold green]✓ Services restarted successfully![/bold green]")
            return True

        except Exception as e:
            console.print(f"\n[bold red]✗ Error restarting services: {e}[/bold red]")
            if self.verbose:
                logger.exception("Restart operation failed")
            return False

    async def status(self, method: str | None = None, watch: bool = False, format: str = "table") -> dict[str, Any]:
        """Get current deployment status.

        Args:
            method: Optional deployment method override
            watch: Whether to watch for changes
            format: Output format (table, json)

        Returns:
            Status information dictionary
        """
        config = self._load_or_find_config()
        deploy_method = DeploymentMethod(method) if method else config.deployment.method

        try:
            deployment_dir = self._get_deployment_dir()

            # Load deployment plan to access reused services
            self.current_plan = self._load_deployment_plan()

            if deploy_method == DeploymentMethod.DOCKER_COMPOSE:
                status_data = await self._status_docker_compose(deployment_dir)
            elif deploy_method == DeploymentMethod.KUBERNETES:
                status_data = await self._status_kubernetes(config.project_name)
            elif deploy_method == DeploymentMethod.SYSTEMD:
                status_data = await self._status_systemd(config)
            else:
                status_data = {"status": "unknown", "method": deploy_method.value}

            if format == "json":
                console.print_json(data=status_data)
            else:
                self._display_status_table(status_data, config.project_name)

            if watch:
                console.print("\n[yellow]Watch mode: Press Ctrl+C to exit[/yellow]")
                # TODO: Implement watch loop

            return status_data

        except Exception as e:
            console.print(f"[red]Error getting status: {e}[/red]")
            if self.verbose:
                logger.exception("Status check failed")
            return {"status": "error", "error": str(e)}

    async def clean(
        self, method: str | None = None, remove_configs: bool = False, remove_secrets: bool = False
    ) -> bool:
        """Clean up all deployment artifacts.

        Args:
            method: Optional deployment method override
            remove_configs: Whether to remove configuration files
            remove_secrets: Whether to remove secrets

        Returns:
            True if successful, False otherwise
        """
        console.print("\n[bold yellow]Cleaning Mycelium Deployment[/bold yellow]\n")

        config = self._load_or_find_config()
        deploy_method = DeploymentMethod(method) if method else config.deployment.method

        console.print(f"[cyan]Method:[/cyan] {deploy_method.value}")
        console.print(f"[cyan]Project:[/cyan] {config.project_name}\n")

        items_to_clean = []
        if remove_configs:
            items_to_clean.append("configuration files")
        if remove_secrets:
            items_to_clean.append("secrets")
        items_to_clean.append("deployment files")
        items_to_clean.append("generated artifacts")

        console.print("[yellow]This will remove:[/yellow]")
        for item in items_to_clean:
            console.print(f"  • {item}")

        if not self.force:
            if not click.confirm("\nContinue?", default=False):
                console.print("[yellow]Operation cancelled.[/yellow]")
                return False

        try:
            deployment_dir = self._get_deployment_dir()

            # Stop services first
            await self.stop(method=method, remove_data=True)

            # Remove deployment directory
            if deployment_dir.exists():
                shutil.rmtree(deployment_dir)
                console.print("[green]✓[/green] Removed deployment directory")

            # Remove secrets if requested
            if remove_secrets:
                secrets_mgr = SecretsManager(config.project_name)
                if secrets_mgr.secrets_file.exists():
                    secrets_mgr.secrets_file.unlink()
                    console.print("[green]✓[/green] Removed secrets")

            # Remove config if requested
            if remove_configs:
                config_manager = ConfigManager()
                config_file = getattr(config_manager, "config_path", None)
                if config_file and config_file.exists():
                    config_file.unlink()
                    console.print("[green]✓[/green] Removed configuration")

            console.print("\n[bold green]✓ Cleanup completed successfully![/bold green]")
            return True

        except Exception as e:
            console.print(f"\n[bold red]✗ Error during cleanup: {e}[/bold red]")
            if self.verbose:
                logger.exception("Cleanup operation failed")
            return False

    async def _detect_services(self) -> list[DetectedService]:
        """Detect available services.

        Returns:
            List of detected services
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Detecting services...", total=None)

            services = self.detector.detect_all_services()

            progress.update(task, completed=100, description=f"Detected {len(services)} services")

        if self.verbose:
            for service in services:
                status_color = "green" if service.status == ServiceStatus.RUNNING else "yellow"
                console.print(
                    f"  • {service.name} ({service.service_type.value}) "
                    f"- [{status_color}]{service.status.value}[/{status_color}] "
                    f"v{service.version}"
                )

        # DEBUG: Log detected services for troubleshooting
        logger.debug(f"Detected {len(services)} services:")
        for service in services:
            logger.debug(
                f"  - name={service.name}, type={service.service_type}, status={service.status}, port={service.port}"
            )

        return services

    async def _create_deployment_plan(
        self, detected_services: list[DetectedService], requested_services: list[str] | None, config_file: Path | None
    ) -> DeploymentPlan:
        """Create a deployment plan based on detected and requested services.

        Args:
            detected_services: Services detected on the system
            requested_services: Specific services requested for deployment
            config_file: Optional configuration file

        Returns:
            Deployment plan
        """
        config = self._load_or_find_config()

        # Create basic plan wrapper
        plan = DeploymentPlan(
            plan_id=f"deploy-{datetime.now().strftime('%Y%m%d-%H%M%S')}", detected_services=detected_services
        )

        # NEW: Use ServiceDeploymentPlanner for smart strategy decisions
        smart_planner = ServiceDeploymentPlanner(
            config=config,
            detected_services=detected_services,
            prefer_reuse=True,  # Default to reusing services
        )

        # Generate smart deployment plan with strategies
        smart_plan = smart_planner.create_deployment_plan()
        plan.smart_plan = smart_plan

        # Update basic plan fields from smart plan
        plan.reusable_services = smart_plan.services_to_reuse.copy()
        plan.new_services = smart_plan.services_to_create.copy()

        # Override with requested services if provided
        if requested_services:
            # Filter to only deploy requested services
            requested_set = set(requested_services)
            plan.new_services = [s for s in plan.new_services if s in requested_set]
            plan.reusable_services = [s for s in plan.reusable_services if s in requested_set]

        # Create deployment steps
        self._generate_deployment_steps(plan)

        return plan

    def _generate_deployment_steps(self, plan: DeploymentPlan) -> None:
        """Generate deployment steps for the plan.

        Args:
            plan: Deployment plan to add steps to
        """
        # Detection phase steps (already done, mark complete)
        plan.add_step(
            DeploymentStep(
                name="Service Detection",
                phase=DeploymentPhase.DETECTION,
                description="Detect existing services",
                status=DeploymentStatus.SUCCESS,
            )
        )

        # Planning phase steps
        plan.add_step(
            DeploymentStep(
                name="Analyze Dependencies",
                phase=DeploymentPhase.PLANNING,
                description="Analyze service dependencies and requirements",
            )
        )

        # Validation phase steps
        plan.add_step(
            DeploymentStep(
                name="Validate Environment",
                phase=DeploymentPhase.VALIDATION,
                description="Validate deployment environment",
            )
        )

        plan.add_step(
            DeploymentStep(
                name="Check Resources", phase=DeploymentPhase.VALIDATION, description="Check available system resources"
            )
        )

        # Generation phase steps
        if plan.new_services:
            plan.add_step(
                DeploymentStep(
                    name="Generate Configurations",
                    phase=DeploymentPhase.GENERATION,
                    description="Generate service configuration files",
                )
            )

        # Deployment phase steps
        for service in plan.new_services:
            plan.add_step(
                DeploymentStep(
                    name=f"Deploy {service}",
                    phase=DeploymentPhase.DEPLOYMENT,
                    description=f"Deploy and configure {service} service",
                )
            )

        # Startup phase steps
        for service in plan.new_services:
            plan.add_step(
                DeploymentStep(
                    name=f"Start {service}", phase=DeploymentPhase.STARTUP, description=f"Start {service} service"
                )
            )

        # Verification phase steps
        plan.add_step(
            DeploymentStep(
                name="Verify Services",
                phase=DeploymentPhase.VERIFICATION,
                description="Verify all services are running correctly",
            )
        )

    async def _generate_configs(self, config: MyceliumConfig, deploy_method: DeploymentMethod) -> bool:
        """Generate deployment configurations.

        Args:
            config: Mycelium configuration
            deploy_method: Deployment method

        Returns:
            True if successful, False otherwise
        """
        try:
            deployment_dir = self._get_deployment_dir()

            with console.status("[bold green]Generating configurations..."):
                # Generate secrets
                secrets_mgr = SecretsManager(config.project_name)
                secrets_obj = secrets_mgr.generate_secrets(
                    postgres=config.services.postgres.enabled,
                    redis=config.services.redis.enabled,
                    temporal=config.services.temporal.enabled,
                )
                secrets_mgr.save_secrets(secrets_obj)

                # Generate deployment files WITH SMART PLAN
                generator = DeploymentGenerator(
                    config,
                    output_dir=deployment_dir,
                    deployment_plan=self.current_plan.smart_plan if self.current_plan else None,
                )
                result = generator.generate(deploy_method)

            if result.success:
                console.print(f"[green]✓[/green] Generated {len(result.files_generated)} files")

                # Show warnings from smart plan
                if result.warnings:
                    console.print("\n[yellow]Warnings:[/yellow]")
                    for warning in result.warnings:
                        console.print(f"  • {warning}")

                return True
            console.print("[red]✗[/red] Configuration generation failed")
            for error in result.errors:
                console.print(f"  • {error}")
            return False

        except Exception as e:
            console.print(f"[red]✗ Error generating configurations: {e}[/red]")
            if self.verbose:
                logger.exception("Configuration generation failed")
            return False

    async def _execute_deployment(self, plan: DeploymentPlan, deploy_method: DeploymentMethod) -> bool:
        """Execute the deployment plan.

        Args:
            plan: Deployment plan to execute
            deploy_method: Deployment method to use

        Returns:
            True if successful, False otherwise
        """
        deployment_dir = self._get_deployment_dir()

        try:
            if deploy_method == DeploymentMethod.DOCKER_COMPOSE:
                return await self._start_docker_compose(deployment_dir)
            if deploy_method == DeploymentMethod.KUBERNETES:
                config = self._load_or_find_config()
                return await self._start_kubernetes(deployment_dir / "kubernetes", config.project_name)
            if deploy_method == DeploymentMethod.SYSTEMD:
                config = self._load_or_find_config()
                return await self._start_systemd(deployment_dir / "systemd", config)
            console.print(f"[red]Unsupported deployment method: {deploy_method}[/red]")
            return False

        except Exception as e:
            console.print(f"[red]Deployment execution error: {e}[/red]")
            if self.verbose:
                logger.exception("Deployment execution failed")
            return False

    # Docker Compose operations
    async def _start_docker_compose(self, deployment_dir: Path) -> bool:
        """Start Docker Compose deployment."""
        compose_file = deployment_dir / "docker-compose.yml"
        if not compose_file.exists():
            console.print(f"[red]docker-compose.yml not found in {deployment_dir}[/red]")
            return False

        # Check if there are any services to deploy
        # If all services are being reused, docker-compose.yml will be empty
        if self.current_plan and not self.current_plan.new_services:
            console.print("[green]✓[/green] All services are being reused, no new containers to start")
            console.print("[dim]Connection details available in .env file[/dim]")
            return True

        with console.status("[bold green]Starting Docker Compose services..."):
            result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "up", "-d"],
                cwd=deployment_dir,
                capture_output=True,
                text=True,
                check=False,
            )

        if result.returncode == 0:
            console.print("[green]✓[/green] Docker Compose services started")
            if self.verbose and result.stdout:
                console.print(result.stdout)
            return True
        console.print("[red]✗[/red] Failed to start Docker Compose services")
        if result.stderr:
            console.print(f"[red]{result.stderr}[/red]")
        return False

    async def _stop_docker_compose(self, deployment_dir: Path, remove_data: bool) -> None:
        """Stop Docker Compose deployment."""
        compose_file = deployment_dir / "docker-compose.yml"
        if not compose_file.exists():
            console.print(f"[yellow]No docker-compose.yml found in {deployment_dir}[/yellow]")
            return

        cmd = ["docker-compose", "-f", str(compose_file)]
        cmd.extend(["down", "-v"] if remove_data else ["down"])

        with console.status("[bold yellow]Stopping Docker Compose services..."):
            result = subprocess.run(cmd, cwd=deployment_dir, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            console.print("[green]✓[/green] Docker Compose services stopped")
        else:
            console.print(f"[yellow]Warning: {result.stderr}[/yellow]")

    async def _restart_docker_compose(self, deployment_dir: Path, services: list[str] | None) -> None:
        """Restart Docker Compose services."""
        compose_file = deployment_dir / "docker-compose.yml"
        if not compose_file.exists():
            raise FileNotFoundError(f"docker-compose.yml not found in {deployment_dir}")

        cmd = ["docker-compose", "-f", str(compose_file), "restart"]
        if services:
            cmd.extend(services)

        with console.status("[bold yellow]Restarting services..."):
            result = subprocess.run(cmd, cwd=deployment_dir, capture_output=True, text=True, check=True)

        console.print("[green]✓[/green] Services restarted")

    async def _status_docker_compose(self, deployment_dir: Path) -> dict[str, Any]:
        """Get Docker Compose deployment status.

        Shows both deployed services AND reused services from the deployment plan.
        """
        compose_file = deployment_dir / "docker-compose.yml"
        if not compose_file.exists():
            return {"status": "not_deployed", "services": []}

        # Get services from docker-compose
        result = subprocess.run(
            ["docker-compose", "-f", str(compose_file), "ps", "--format", "json"],
            cwd=deployment_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            return {"status": "error", "error": result.stderr}

        deployed_services = []
        if result.stdout.strip():
            try:
                # Handle line-by-line JSON
                for line in result.stdout.strip().split("\n"):
                    if line:
                        deployed_services.append(json.loads(line))
            except json.JSONDecodeError:
                pass

        # Also check for reused services from deployment plan
        reused_services = []
        if self.current_plan and self.current_plan.reusable_services:
            # Get info about reused services
            for service_name in self.current_plan.reusable_services:
                # Get service plan details
                if self.current_plan.smart_plan:
                    service_plan = self.current_plan.smart_plan.get_service_plan(service_name)
                    if service_plan:
                        reused_services.append(
                            {
                                "name": service_name,
                                "status": "reused",
                                "host": service_plan.host,
                                "port": service_plan.port,
                                "version": service_plan.version,
                                "strategy": "REUSE",
                            }
                        )

        return {
            "status": "running" if (deployed_services or reused_services) else "stopped",
            "method": "docker-compose",
            "services": deployed_services,
            "reused_services": reused_services,
        }

    # Kubernetes operations
    async def _start_kubernetes(self, k8s_dir: Path, namespace: str) -> bool:
        """Start Kubernetes deployment."""
        if not k8s_dir.exists():
            console.print(f"[red]Kubernetes directory not found: {k8s_dir}[/red]")
            return False

        with console.status("[bold green]Applying Kubernetes manifests..."):
            result = subprocess.run(
                ["kubectl", "apply", "-k", str(k8s_dir)], capture_output=True, text=True, check=False
            )

        if result.returncode == 0:
            console.print("[green]✓[/green] Kubernetes resources created")
            if self.verbose and result.stdout:
                console.print(result.stdout)
            return True
        console.print("[red]✗[/red] Failed to create Kubernetes resources")
        if result.stderr:
            console.print(f"[red]{result.stderr}[/red]")
        return False

    async def _stop_kubernetes(self, namespace: str, remove_data: bool) -> None:
        """Stop Kubernetes deployment."""
        with console.status("[bold yellow]Deleting Kubernetes resources..."):
            result = subprocess.run(
                ["kubectl", "delete", "all", "--all", "-n", namespace], capture_output=True, text=True, check=False
            )

        if result.returncode == 0:
            console.print("[green]✓[/green] Kubernetes resources deleted")
            if remove_data:
                # Also delete PVCs
                subprocess.run(["kubectl", "delete", "pvc", "--all", "-n", namespace], capture_output=True, check=False)
        else:
            console.print(f"[yellow]Warning: {result.stderr}[/yellow]")

    async def _restart_kubernetes(self, namespace: str, services: list[str] | None) -> None:
        """Restart Kubernetes pods."""
        with console.status("[bold yellow]Restarting pods..."):
            if services:
                for service in services:
                    subprocess.run(
                        ["kubectl", "rollout", "restart", "deployment", service, "-n", namespace],
                        capture_output=True,
                        check=True,
                    )
            else:
                # Restart all deployments
                subprocess.run(
                    ["kubectl", "rollout", "restart", "deployment", "-n", namespace], capture_output=True, check=True
                )

        console.print("[green]✓[/green] Pods restarted")

    async def _status_kubernetes(self, namespace: str) -> dict[str, Any]:
        """Get Kubernetes deployment status."""
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", namespace, "-o", "json"], capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            return {"status": "error", "error": result.stderr}

        try:
            data = json.loads(result.stdout)
            pods = data.get("items", [])
            return {
                "status": "running" if pods else "not_deployed",
                "method": "kubernetes",
                "namespace": namespace,
                "pods": [
                    {
                        "name": pod["metadata"]["name"],
                        "phase": pod["status"].get("phase", "Unknown"),
                        "ready": f"{sum(1 for c in pod['status'].get('containerStatuses', []) if c.get('ready'))}/{len(pod['status'].get('containerStatuses', []))}",
                    }
                    for pod in pods
                ],
            }
        except json.JSONDecodeError:
            return {"status": "error", "error": "Failed to parse kubectl output"}

    # Systemd operations
    async def _start_systemd(self, systemd_dir: Path, config: MyceliumConfig) -> bool:
        """Start systemd services."""
        if not systemd_dir.exists():
            console.print(f"[red]systemd directory not found: {systemd_dir}[/red]")
            return False

        services = self._get_systemd_services(config)

        with console.status("[bold green]Starting systemd services..."):
            for service in services:
                subprocess.run(["sudo", "systemctl", "start", service], check=True)

        console.print(f"[green]✓[/green] Started {len(services)} service(s)")
        return True

    async def _stop_systemd(self, config: MyceliumConfig, remove_data: bool) -> None:
        """Stop systemd services."""
        services = self._get_systemd_services(config)

        with console.status("[bold yellow]Stopping systemd services..."):
            for service in services:
                subprocess.run(["sudo", "systemctl", "stop", service], check=False)

        console.print(f"[green]✓[/green] Stopped {len(services)} service(s)")

    async def _restart_systemd(self, config: MyceliumConfig, services: list[str] | None) -> None:
        """Restart systemd services."""
        if services:
            service_names = [f"{config.project_name}-{s}" for s in services]
        else:
            service_names = self._get_systemd_services(config)

        with console.status("[bold yellow]Restarting services..."):
            for service in service_names:
                subprocess.run(["sudo", "systemctl", "restart", service], check=True)

        console.print("[green]✓[/green] Services restarted")

    async def _status_systemd(self, config: MyceliumConfig) -> dict[str, Any]:
        """Get systemd services status."""
        services = self._get_systemd_services(config)
        service_status = []

        for service in services:
            result = subprocess.run(["systemctl", "is-active", service], capture_output=True, text=True, check=False)
            service_status.append({"name": service, "status": result.stdout.strip()})

        return {
            "status": "running" if any(s["status"] == "active" for s in service_status) else "stopped",
            "method": "systemd",
            "services": service_status,
        }

    def _get_systemd_services(self, config: MyceliumConfig) -> list[str]:
        """Get list of systemd service names."""
        services = []
        if config.services.redis.enabled:
            services.append(f"{config.project_name}-redis")
        if config.services.postgres.enabled:
            services.append(f"{config.project_name}-postgres")
        if config.services.temporal.enabled:
            services.append(f"{config.project_name}-temporal")
        return services

    def _display_plan_summary(self, plan: DeploymentPlan) -> None:
        """Display deployment plan summary.

        Args:
            plan: Deployment plan to display
        """
        table = Table(title="Deployment Plan Summary", show_header=True, header_style="bold cyan")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Plan ID", plan.plan_id)
        table.add_row("Detected Services", str(len(plan.detected_services)))
        table.add_row("Reusable Services", ", ".join(plan.reusable_services) or "None")
        table.add_row("New Services", ", ".join(plan.new_services) or "None")
        table.add_row("Total Steps", str(len(plan.deployment_steps)))
        table.add_row("Estimated Duration", f"{plan.estimated_duration} seconds")

        console.print(table)

        # Show smart plan details if available
        if plan.smart_plan:
            console.print("\n[bold cyan]Smart Deployment Strategy:[/bold cyan]")
            for service_name, service_plan in plan.smart_plan.service_plans.items():
                strategy_color = {"reuse": "green", "create": "blue", "alongside": "yellow", "skip": "dim"}.get(
                    service_plan.strategy.value, "white"
                )
                console.print(
                    f"  • {service_name}: [{strategy_color}]{service_plan.strategy.value.upper()}[/{strategy_color}] "
                    f"- {service_plan.reason}"
                )

    def _display_deployment_summary(self, plan: DeploymentPlan) -> None:
        """Display deployment summary after completion.

        Args:
            plan: Completed deployment plan
        """
        table = Table(title="Deployment Summary", show_header=True, header_style="bold green")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Type", style="yellow")

        # Add reused services
        for service_name in plan.reusable_services:
            table.add_row(service_name, "✓ Reused", "Existing")

        # Add newly deployed services
        for service_name in plan.new_services:
            table.add_row(service_name, "✓ Deployed", "New")

        console.print("\n")
        console.print(table)

        # Calculate and display execution time
        total_duration = sum(step.duration for step in plan.deployment_steps if step.duration is not None)
        console.print(f"\n[green]Total execution time: {total_duration:.1f} seconds[/green]")

        # Display context-aware next steps
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("  1. Check service status: [cyan]mycelium deploy status[/cyan]")

        # Only show docker-compose logs if we actually deployed containers
        if plan.new_services:
            console.print("  2. View service logs: [cyan]docker-compose logs -f[/cyan]")
            console.print("  3. Stop services: [cyan]mycelium deploy stop[/cyan]")
        else:
            # All services were reused
            console.print("  2. View Redis logs: [cyan]docker logs -f <redis-container>[/cyan]")
            console.print("  3. View PostgreSQL logs: [cyan]docker logs -f <postgres-container>[/cyan]")
            console.print(
                "  4. Connection details: [cyan]cat ~/.local/share/mycelium/deployments/test-project/.env[/cyan]"
            )

    def _display_status_table(self, status_data: dict[str, Any], project_name: str) -> None:
        """Display status information as a table.

        Args:
            status_data: Status data dictionary
            project_name: Project name for title
        """
        table = Table(title=f"{project_name} - Deployment Status", show_header=True)
        table.add_column("Service/Pod", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Details")

        method = status_data.get("method", "unknown")

        if method == "docker-compose":
            services = status_data.get("services", [])
            reused_services = status_data.get("reused_services", [])

            if not services and not reused_services:
                console.print("[yellow]No running containers found[/yellow]")
                return

            # Display deployed services
            for service in services:
                status = service.get("State", "unknown")
                status_str = "[green]Running[/green]" if status == "running" else "[red]Stopped[/red]"
                table.add_row(
                    service.get("Service", service.get("Name", "unknown")), status_str, service.get("Status", "")
                )

            # Display reused services
            for service in reused_services:
                status_str = "[blue]Reused[/blue]"
                details = f"{service['host']}:{service['port']} (v{service['version']})"
                table.add_row(service["name"], status_str, details)

        elif method == "kubernetes":
            pods = status_data.get("pods", [])
            if not pods:
                console.print("[yellow]No pods found[/yellow]")
                return

            for pod in pods:
                phase = pod.get("phase", "Unknown")
                if phase == "Running":
                    status_str = "[green]Running[/green]"
                elif phase == "Pending":
                    status_str = "[yellow]Pending[/yellow]"
                else:
                    status_str = f"[red]{phase}[/red]"

                table.add_row(pod["name"], status_str, f"Ready: {pod.get('ready', 'Unknown')}")

        elif method == "systemd":
            services = status_data.get("services", [])
            for service in services:
                status = service["status"]
                if status == "active":
                    status_str = "[green]Active[/green]"
                elif status == "inactive":
                    status_str = "[yellow]Inactive[/yellow]"
                else:
                    status_str = f"[red]{status}[/red]"

                table.add_row(service["name"], status_str, "")

        console.print(table)

    def _confirm_deployment(self) -> bool:
        """Confirm deployment with user.

        Returns:
            True if confirmed, False otherwise
        """
        console.print("\n[yellow]Ready to proceed with deployment?[/yellow]")
        return click.confirm("Continue", default=True)


# Module exports for external use
__all__ = [
    "DeployCommand",
    "DeploymentPlan",
    "DeploymentPhase",
    "DeploymentStatus",
    "DeploymentStep",
]
