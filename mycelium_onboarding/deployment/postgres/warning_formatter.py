"""PostgreSQL compatibility warning message formatter.

This module provides Rich-based formatters for displaying PostgreSQL-Temporal
compatibility warnings in a user-friendly way on the CLI.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from mycelium_onboarding.deployment.postgres.compatibility import CompatibilityRequirement


class WarningFormatter:
    """Format validation results into beautiful, actionable CLI warnings using Rich.

    This class provides methods to format compatibility warnings, validation results,
    upgrade recommendations, and version information tables with appropriate
    styling and colors.
    """

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the warning formatter.

        Args:
            console: Rich Console instance. If None, creates a new one.
        """
        self.console = console or Console()

    def format_compatibility_warning(
        self,
        temporal_version: str,
        postgres_version: str,
        min_required: str,
        max_supported: str,
        issue_type: str,
    ) -> None:
        """Display a formatted compatibility warning.

        Args:
            temporal_version: Detected Temporal version
            postgres_version: Detected PostgreSQL version
            min_required: Minimum PostgreSQL version required
            max_supported: Maximum PostgreSQL version supported
            issue_type: Type of compatibility issue
                       ("too_old", "too_new", "eol", "deprecated", "unknown")
        """
        if issue_type == "too_old":
            self._format_too_old_warning(temporal_version, postgres_version, min_required, max_supported)
        elif issue_type == "too_new":
            self._format_too_new_warning(temporal_version, postgres_version, min_required, max_supported)
        elif issue_type == "eol":
            self._format_eol_warning(temporal_version, postgres_version, min_required, max_supported)
        elif issue_type == "deprecated":
            self._format_deprecated_warning(temporal_version, postgres_version)
        elif issue_type == "unknown":
            self._format_unknown_version_warning(temporal_version, postgres_version, min_required, max_supported)
        else:
            self._format_generic_warning(temporal_version, postgres_version, min_required, max_supported, issue_type)

    def _format_too_old_warning(
        self,
        temporal_version: str,
        postgres_version: str,
        min_required: str,
        max_supported: str,
    ) -> None:
        """Format warning for PostgreSQL version that is too old."""
        content = Text()
        content.append("\nCurrent Setup:\n", style="bold")
        content.append(f"  Temporal:   {temporal_version}\n", style="cyan")
        content.append(f"  PostgreSQL: {postgres_version}\n", style="red bold")

        content.append("\nRequirements:\n", style="bold")
        content.append(f"  Minimum PostgreSQL: {min_required}\n", style="yellow")
        content.append(f"  Maximum PostgreSQL: {max_supported}\n", style="green")
        content.append(f"  Recommended:        {min_required}\n", style="green bold")

        content.append("\n[red bold]Issue:[/red bold] Your PostgreSQL version is too old\n", style="")

        content.append("\nImpact:\n", style="bold")
        content.append("  • May cause compatibility errors\n", style="yellow")
        content.append("  • Missing required database features\n", style="yellow")
        content.append("  • Temporal may fail to start\n", style="yellow")

        content.append("\nRecommended Actions:\n", style="bold green")
        content.append(f"  1. Upgrade PostgreSQL to {min_required}+ (manual process)\n")
        content.append("     https://www.postgresql.org/docs/current/upgrading.html\n")
        content.append("\n  2. Alternative: Downgrade Temporal (if compatible version exists)\n")
        content.append("\n  3. Continue anyway: Use --force-version flag\n")
        content.append("     ⚠️  Not recommended - may cause failures\n", style="yellow")

        content.append("\nManual Upgrade Steps:\n", style="bold cyan")
        content.append("  1. Backup your database: pg_dump mydb > backup.sql\n")
        content.append(
            f"  2. Install PostgreSQL {min_required}: apt-get install postgresql-{min_required.split('.')[0]}\n"
        )
        content.append("  3. Migrate data: pg_upgrade or logical replication\n")
        content.append("  4. Test thoroughly before deploying Temporal\n")

        panel = Panel(
            content,
            title="⚠️  PostgreSQL Version Incompatibility",
            border_style="yellow",
            padding=(1, 2),
        )
        self.console.print(panel)

    def _format_too_new_warning(
        self,
        temporal_version: str,
        postgres_version: str,
        min_required: str,
        max_supported: str,
    ) -> None:
        """Format warning for PostgreSQL version that is too new."""
        content = Text()
        content.append("\nCurrent Setup:\n", style="bold")
        content.append(f"  Temporal:   {temporal_version}\n", style="cyan")
        content.append(f"  PostgreSQL: {postgres_version}\n", style="magenta bold")

        content.append("\nRequirements:\n", style="bold")
        content.append(f"  Minimum PostgreSQL: {min_required}\n", style="green")
        content.append(f"  Maximum PostgreSQL: {max_supported}\n", style="yellow")
        content.append(f"  Recommended:        {max_supported}\n", style="green bold")

        content.append(
            "\n[magenta bold]Issue:[/magenta bold] Your PostgreSQL version is too new\n",
            style="",
        )

        content.append("\nImpact:\n", style="bold")
        content.append("  • May encounter untested behavior\n", style="yellow")
        content.append("  • Potential compatibility issues\n", style="yellow")
        content.append("  • Not officially supported by Temporal\n", style="yellow")

        content.append("\nRecommended Actions:\n", style="bold green")
        content.append(f"  1. Downgrade PostgreSQL to {max_supported} (manual process)\n")
        content.append("     https://www.postgresql.org/docs/current/upgrading.html\n")
        content.append("\n  2. Alternative: Upgrade Temporal to newer version (if available)\n")
        content.append("\n  3. Continue anyway: Use --force-version flag\n")
        content.append("     ⚠️  Proceed with caution - limited support\n", style="yellow")

        panel = Panel(
            content,
            title="⚠️  PostgreSQL Version Incompatibility",
            border_style="magenta",
            padding=(1, 2),
        )
        self.console.print(panel)

    def _format_eol_warning(
        self,
        temporal_version: str,
        postgres_version: str,
        min_required: str,
        max_supported: str,
    ) -> None:
        """Format warning for PostgreSQL version that is end-of-life."""
        content = Text()
        content.append("\nYour PostgreSQL version has reached End of Life:\n", style="bold red")
        content.append(f"  PostgreSQL: {postgres_version}\n", style="red bold")
        content.append("  Status:     End of Life (EOL)\n", style="red")

        content.append("\n[red bold]Security Risk:[/red bold] No more security updates\n", style="")

        content.append("\nStrongly Recommended:\n", style="bold yellow")
        major_version = min_required.split(".")[0]
        content.append(f"  Manually upgrade to PostgreSQL {major_version}+ (current stable)\n")
        content.append("  See manual upgrade steps in documentation\n")

        content.append("\nCompatibility with Temporal:\n", style="bold")
        content.append(f"  Temporal:   {temporal_version}\n", style="cyan")
        content.append(f"  Minimum PostgreSQL: {min_required}\n", style="yellow")
        content.append(f"  Maximum PostgreSQL: {max_supported}\n", style="green")

        content.append(
            "\nWhile technically compatible with Temporal, using EOL PostgreSQL\nin production is a security risk.\n",
            style="yellow",
        )

        content.append("\nProceed at your own risk: --force-version\n", style="red")

        panel = Panel(
            content,
            title="⚠️  PostgreSQL End of Life Warning",
            border_style="red",
            padding=(1, 2),
        )
        self.console.print(panel)

    def _format_deprecated_warning(self, temporal_version: str, postgres_version: str) -> None:
        """Format warning for deprecated Temporal version."""
        content = Text()
        content.append("\nDeprecated Temporal Version Detected:\n", style="bold yellow")
        content.append(f"  Temporal:   {temporal_version}\n", style="yellow bold")
        content.append(f"  PostgreSQL: {postgres_version}\n", style="cyan")

        content.append("\n[yellow bold]Warning:[/yellow bold] This Temporal version is deprecated\n", style="")

        content.append("\nRecommended Actions:\n", style="bold green")
        content.append("  1. Upgrade to a supported Temporal version\n")
        content.append("  2. Review Temporal release notes for breaking changes\n")
        content.append("  3. Test thoroughly after upgrade\n")

        content.append("\nContinue with deprecated version: --force-version\n", style="yellow")

        panel = Panel(
            content,
            title="⚠️  Deprecated Temporal Version",
            border_style="yellow",
            padding=(1, 2),
        )
        self.console.print(panel)

    def _format_unknown_version_warning(
        self,
        temporal_version: str,
        postgres_version: str,
        min_required: str,
        max_supported: str,
    ) -> None:
        """Format warning for unknown Temporal version."""
        content = Text()
        content.append("\nUnknown Temporal Version Detected:\n", style="bold yellow")
        content.append(f"  Detected:  {temporal_version} (unknown version)\n", style="yellow bold")
        content.append("  Using:     Conservative defaults\n", style="cyan")

        content.append("\nPostgreSQL Requirements (estimated):\n", style="bold")
        content.append(f"  Minimum: {min_required}\n", style="yellow")
        content.append(f"  Maximum: {max_supported}\n", style="green")

        content.append("\nCurrent PostgreSQL:\n", style="bold")
        content.append(f"  PostgreSQL: {postgres_version}\n", style="cyan")

        content.append("\nRecommendation:\n", style="bold green")
        content.append("  Verify compatibility manually at:\n")
        content.append("  https://docs.temporal.io/self-hosted-guide/setup\n", style="blue underline")

        content.append("\nContinue with caution: Proceed or Cancel?\n", style="yellow")

        panel = Panel(
            content,
            title="⚠️  Unknown Temporal Version",
            border_style="yellow",
            padding=(1, 2),
        )
        self.console.print(panel)

    def _format_generic_warning(
        self,
        temporal_version: str,
        postgres_version: str,
        min_required: str,
        max_supported: str,
        issue_type: str,
    ) -> None:
        """Format generic compatibility warning."""
        content = Text()
        content.append("\nCompatibility Issue Detected:\n", style="bold yellow")
        content.append(f"  Temporal:   {temporal_version}\n", style="cyan")
        content.append(f"  PostgreSQL: {postgres_version}\n", style="magenta")
        content.append(f"  Issue Type: {issue_type}\n", style="yellow")

        content.append("\nRequirements:\n", style="bold")
        content.append(f"  Minimum PostgreSQL: {min_required}\n", style="yellow")
        content.append(f"  Maximum PostgreSQL: {max_supported}\n", style="green")

        panel = Panel(
            content,
            title="⚠️  Compatibility Warning",
            border_style="yellow",
            padding=(1, 2),
        )
        self.console.print(panel)

    def format_validation_result(self, validation_result: CompatibilityRequirement) -> None:
        """Display formatted validation result with appropriate styling.

        - Green panel for compatible versions
        - Yellow panel for warnings (can proceed with --force)
        - Red panel for errors (cannot proceed)

        Args:
            validation_result: CompatibilityRequirement with validation details
        """
        if validation_result.is_compatible and not validation_result.warning_message:
            self._format_success_result(validation_result)
        elif validation_result.is_compatible and validation_result.warning_message:
            self._format_warning_result(validation_result)
        else:
            self._format_error_result(validation_result)

    def _format_success_result(self, result: CompatibilityRequirement) -> None:
        """Format successful compatibility check result."""
        content = Text()
        content.append("\nTemporal:   ", style="bold")
        content.append(f"{result.temporal_version}\n", style="cyan bold")
        content.append("PostgreSQL: ", style="bold")
        content.append(f"{result.postgres_version}\n", style="green bold")

        content.append("\nStatus: ", style="bold")
        content.append("Compatible ✓\n", style="green bold")

        if result.notes:
            content.append(f"\nNotes: {result.notes}\n", style="dim")

        content.append("\nThis is a tested, recommended combination.\n", style="green")

        panel = Panel(
            content,
            title="✅ PostgreSQL Compatibility Check Passed",
            border_style="green",
            padding=(1, 2),
        )
        self.console.print(panel)

    def _format_warning_result(self, result: CompatibilityRequirement) -> None:
        """Format compatibility check result with warnings."""
        content = Text()
        content.append("\nTemporal:   ", style="bold")
        content.append(f"{result.temporal_version}\n", style="cyan bold")
        content.append("PostgreSQL: ", style="bold")
        content.append(f"{result.postgres_version}\n", style="yellow bold")

        content.append("\nStatus: ", style="bold")
        content.append("Compatible (with warnings)\n", style="yellow bold")

        if result.warning_message:
            content.append(f"\n⚠️  Warning:\n{result.warning_message}\n", style="yellow")

        if result.notes:
            content.append(f"\nNotes: {result.notes}\n", style="dim")

        content.append("\nYou can proceed with --force-version flag.\n", style="yellow")

        panel = Panel(
            content,
            title="⚠️  PostgreSQL Compatibility Check (Warnings)",
            border_style="yellow",
            padding=(1, 2),
        )
        self.console.print(panel)

    def _format_error_result(self, result: CompatibilityRequirement) -> None:
        """Format compatibility check error result."""
        content = Text()
        content.append("\nTemporal:   ", style="bold")
        content.append(f"{result.temporal_version}\n", style="cyan bold")
        content.append("PostgreSQL: ", style="bold")
        content.append(f"{result.postgres_version}\n", style="red bold")

        content.append("\nStatus: ", style="bold")
        content.append("Incompatible ✗\n", style="red bold")

        content.append("\nRequirements:\n", style="bold")
        content.append(f"  Minimum PostgreSQL: {result.min_postgres}\n", style="yellow")
        content.append(f"  Maximum PostgreSQL: {result.max_postgres}\n", style="green")
        content.append(f"  Recommended:        {result.recommended}\n", style="green bold")

        if result.warning_message:
            content.append(f"\n❌ Error:\n{result.warning_message}\n", style="red")

        if result.notes:
            content.append(f"\nNotes: {result.notes}\n", style="dim")

        content.append("\nCannot proceed without fixing version mismatch.\n", style="red bold")
        content.append("Use --force-version to override (not recommended).\n", style="yellow")

        panel = Panel(
            content,
            title="❌ PostgreSQL Compatibility Check Failed",
            border_style="red",
            padding=(1, 2),
        )
        self.console.print(panel)

    def format_upgrade_recommendation(
        self,
        current_postgres: str,
        recommended_postgres: str,
        temporal_version: str,
    ) -> None:
        """Display upgrade recommendation with manual steps.

        CRITICAL: Never suggest auto-upgrade, only manual process.

        Args:
            current_postgres: Current PostgreSQL version
            recommended_postgres: Recommended PostgreSQL version
            temporal_version: Temporal version being deployed
        """
        content = Text()
        content.append("\nCurrent PostgreSQL: ", style="bold")
        content.append(f"{current_postgres}\n", style="yellow bold")
        content.append("Recommended:        ", style="bold")
        content.append(f"{recommended_postgres}\n", style="green bold")
        content.append("Temporal:           ", style="bold")
        content.append(f"{temporal_version}\n", style="cyan")

        content.append("\n[green bold]Upgrade Recommendation[/green bold]\n", style="")
        content.append(
            f"\nFor optimal compatibility with Temporal {temporal_version},\n"
            f"upgrade PostgreSQL to version {recommended_postgres}.\n",
            style="",
        )

        content.append("\n[yellow bold]⚠️  Manual Upgrade Required[/yellow bold]\n", style="")
        content.append("PostgreSQL upgrades must be performed manually.\n", style="yellow")
        content.append("Automatic upgrades are NOT supported for safety.\n\n", style="yellow")

        content.append("Manual Upgrade Steps:\n", style="bold cyan")
        major_version = recommended_postgres.split(".")[0]
        content.append("\n  1. Backup your database:\n", style="bold")
        content.append("     pg_dumpall > backup.sql\n")
        content.append("     # Or use pg_basebackup for physical backup\n", style="dim")

        content.append("\n  2. Install PostgreSQL ", style="bold")
        content.append(f"{recommended_postgres}:\n", style="bold green")
        content.append("     # Debian/Ubuntu:\n", style="dim")
        content.append(f"     apt-get install postgresql-{major_version}\n")
        content.append("     # RHEL/CentOS:\n", style="dim")
        content.append(f"     yum install postgresql{major_version}-server\n")
        content.append("     # macOS:\n", style="dim")
        content.append(f"     brew install postgresql@{major_version}\n")

        content.append("\n  3. Migrate data:\n", style="bold")
        content.append("     # Option A: In-place upgrade (faster, more complex)\n", style="dim")
        content.append("     pg_upgrade --check\n")
        content.append("     pg_upgrade\n")
        content.append("     # Option B: Logical replication (zero downtime)\n", style="dim")
        content.append("     # See: https://www.postgresql.org/docs/current/logical-replication.html\n")

        content.append("\n  4. Test thoroughly:\n", style="bold")
        content.append("     # Verify data integrity\n")
        content.append("     # Run application tests\n")
        content.append("     # Check performance\n")

        content.append("\n  5. Deploy Temporal:\n", style="bold")
        content.append(f"     # Once PostgreSQL {recommended_postgres} is confirmed working\n")

        content.append("\nResources:\n", style="bold green")
        content.append("  • PostgreSQL Upgrade Guide:\n")
        content.append("    https://www.postgresql.org/docs/current/upgrading.html\n", style="blue underline")
        content.append("  • pg_upgrade Documentation:\n")
        content.append("    https://www.postgresql.org/docs/current/pgupgrade.html\n", style="blue underline")

        panel = Panel(
            content,
            title="📋 PostgreSQL Upgrade Recommendation",
            border_style="cyan",
            padding=(1, 2),
        )
        self.console.print(panel)

    def format_version_info_table(
        self,
        temporal_version: str,
        postgres_version: str,
        compatibility_status: str,
        notes: str | None = None,
    ) -> Table:
        """Create a formatted table showing version information.

        Args:
            temporal_version: Temporal version
            postgres_version: PostgreSQL version
            compatibility_status: Status string (e.g., "Compatible", "Incompatible")
            notes: Optional additional notes

        Returns:
            Rich Table object (can be printed with console.print)
        """
        table = Table(title="Version Compatibility Check", show_header=True, header_style="bold")
        table.add_column("Component", style="cyan", width=15)
        table.add_column("Version", style="magenta", width=12)
        table.add_column("Status", style="bold", width=20)

        # Determine status style - check for "incompatible" first
        if "incompatible" in compatibility_status.lower():
            status_style = "red"
            status_icon = "✗"
        elif "warning" in compatibility_status.lower():
            status_style = "yellow"
            status_icon = "⚠️"
        elif "compatible" in compatibility_status.lower():
            status_style = "green"
            status_icon = "✓"
        else:
            status_style = "yellow"
            status_icon = "?"

        table.add_row("Temporal", temporal_version, "Detected", style="")
        table.add_row("PostgreSQL", postgres_version, "Detected", style="")
        table.add_row(
            "Compatibility",
            "",
            f"[{status_style}]{status_icon} {compatibility_status}[/{status_style}]",
            style="",
        )

        if notes:
            # Add notes as a separate row spanning all columns
            table.add_row("Notes", notes, "", style="dim")

        return table

    def print_version_info_table(
        self,
        temporal_version: str,
        postgres_version: str,
        compatibility_status: str,
        notes: str | None = None,
    ) -> None:
        """Print a formatted table showing version information.

        Args:
            temporal_version: Temporal version
            postgres_version: PostgreSQL version
            compatibility_status: Status string (e.g., "Compatible", "Incompatible")
            notes: Optional additional notes
        """
        table = self.format_version_info_table(temporal_version, postgres_version, compatibility_status, notes)
        self.console.print(table)
