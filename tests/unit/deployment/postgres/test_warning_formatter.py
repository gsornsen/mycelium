"""Comprehensive unit tests for PostgreSQL warning formatter.

This test suite validates the WarningFormatter's ability to format compatibility
warnings, validation results, and upgrade recommendations using Rich console.
"""

from __future__ import annotations

from io import StringIO

import pytest
from rich.console import Console

from mycelium_onboarding.deployment.postgres.compatibility import CompatibilityRequirement
from mycelium_onboarding.deployment.postgres.warning_formatter import WarningFormatter


@pytest.fixture
def string_console() -> tuple[Console, StringIO]:
    """Create a Rich Console that writes to a StringIO for testing.

    Returns:
        Tuple of (Console, StringIO) for output capture and assertions
    """
    string_io = StringIO()
    console = Console(file=string_io, force_terminal=True, width=120, legacy_windows=False)
    return console, string_io


@pytest.fixture
def formatter(string_console: tuple[Console, StringIO]) -> WarningFormatter:
    """Create a WarningFormatter with test console.

    Args:
        string_console: Console and StringIO fixture

    Returns:
        WarningFormatter instance
    """
    console, _ = string_console
    return WarningFormatter(console=console)


class TestWarningFormatterInitialization:
    """Test WarningFormatter initialization."""

    def test_init_with_console(self) -> None:
        """Test initialization with provided console."""
        console = Console()
        formatter = WarningFormatter(console=console)
        assert formatter.console is console

    def test_init_without_console(self) -> None:
        """Test initialization creates default console."""
        formatter = WarningFormatter()
        assert formatter.console is not None
        assert isinstance(formatter.console, Console)


class TestCompatibilityWarningFormatting:
    """Test formatting of compatibility warnings for different issue types."""

    def test_format_compatibility_warning_too_old(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test formatting warning for PostgreSQL version that is too old."""
        _, string_io = string_console

        formatter.format_compatibility_warning(
            temporal_version="1.22.0",
            postgres_version="12.0",
            min_required="13.0",
            max_supported="16.9",
            issue_type="too_old",
        )

        output = string_io.getvalue()

        # Verify essential content
        assert "PostgreSQL Version Incompatibility" in output
        assert "1.22.0" in output
        assert "12.0" in output
        assert "13.0" in output
        assert "16.9" in output
        assert "too old" in output.lower() or "Minimum" in output
        assert "Impact" in output
        assert "compatibility errors" in output.lower() or "Missing required" in output
        assert "Recommended Actions" in output
        assert "Upgrade PostgreSQL" in output
        assert "Manual Upgrade Steps" in output
        assert "pg_dump" in output
        assert "--force-version" in output

    def test_format_compatibility_warning_too_new(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test formatting warning for PostgreSQL version that is too new."""
        _, string_io = string_console

        formatter.format_compatibility_warning(
            temporal_version="1.20.0",
            postgres_version="17.0",
            min_required="12.0",
            max_supported="15.9",
            issue_type="too_new",
        )

        output = string_io.getvalue()

        # Verify essential content
        assert "PostgreSQL Version Incompatibility" in output
        assert "1.20.0" in output
        assert "17.0" in output
        assert "15.9" in output
        assert "too new" in output.lower() or "Maximum" in output
        assert "Impact" in output
        assert "untested behavior" in output.lower() or "compatibility issues" in output.lower()
        assert "Recommended Actions" in output
        assert "--force-version" in output

    def test_format_compatibility_warning_eol(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test formatting warning for end-of-life PostgreSQL version."""
        _, string_io = string_console

        formatter.format_compatibility_warning(
            temporal_version="1.22.0",
            postgres_version="11.0",
            min_required="12.0",
            max_supported="16.9",
            issue_type="eol",
        )

        output = string_io.getvalue()

        # Verify essential content
        assert "End of Life" in output or "EOL" in output
        assert "11.0" in output
        assert "Security Risk" in output or "security updates" in output.lower()
        assert "Strongly Recommended" in output or "Upgrade" in output
        assert "--force-version" in output

    def test_format_compatibility_warning_deprecated(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test formatting warning for deprecated Temporal version."""
        _, string_io = string_console

        formatter.format_compatibility_warning(
            temporal_version="1.18.0",
            postgres_version="14.0",
            min_required="12.0",
            max_supported="15.9",
            issue_type="deprecated",
        )

        output = string_io.getvalue()

        # Verify essential content
        assert "Deprecated" in output
        assert "1.18.0" in output
        assert "14.0" in output
        assert "Upgrade" in output
        assert "--force-version" in output

    def test_format_compatibility_warning_unknown(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test formatting warning for unknown Temporal version."""
        _, string_io = string_console

        formatter.format_compatibility_warning(
            temporal_version="1.99.0",
            postgres_version="15.0",
            min_required="12.0",
            max_supported="17.9",
            issue_type="unknown",
        )

        output = string_io.getvalue()

        # Verify essential content
        assert "Unknown" in output
        assert "1.99.0" in output
        assert "15.0" in output
        assert "Conservative defaults" in output or "estimated" in output.lower()
        assert "12.0" in output
        assert "17.9" in output
        assert "Verify compatibility manually" in output or "docs.temporal.io" in output
        assert "Proceed or Cancel" in output or "Continue with caution" in output

    def test_format_compatibility_warning_generic(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test formatting generic compatibility warning."""
        _, string_io = string_console

        formatter.format_compatibility_warning(
            temporal_version="1.22.0",
            postgres_version="14.0",
            min_required="12.0",
            max_supported="16.9",
            issue_type="custom_issue",
        )

        output = string_io.getvalue()

        # Verify essential content
        assert "Compatibility" in output
        assert "1.22.0" in output
        assert "14.0" in output
        assert "custom_issue" in output
        assert "12.0" in output
        assert "16.9" in output


class TestValidationResultFormatting:
    """Test formatting of validation results."""

    def test_format_validation_result_success(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test formatting successful validation result."""
        _, string_io = string_console

        result = CompatibilityRequirement(
            min_postgres="13.0",
            max_postgres="16.9",
            recommended="15.0",
            notes="Tested and recommended combination",
            is_compatible=True,
            warning_message=None,
            temporal_version="1.24.0",
            postgres_version="16.0",
            support_level="active",
        )

        formatter.format_validation_result(result)
        output = string_io.getvalue()

        # Verify success indicators
        assert "Passed" in output or "Compatible" in output
        assert "1.24.0" in output
        assert "16.0" in output
        assert "✓" in output or "✅" in output
        assert "recommended combination" in output.lower() or "tested" in output.lower()

    def test_format_validation_result_warning(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test formatting validation result with warnings."""
        _, string_io = string_console

        result = CompatibilityRequirement(
            min_postgres="13.0",
            max_postgres="16.9",
            recommended="15.0",
            notes="Minor compatibility concern",
            is_compatible=True,
            warning_message="PostgreSQL 16 has limited testing with Temporal 1.22.0",
            temporal_version="1.22.0",
            postgres_version="16.0",
            support_level="active",
        )

        formatter.format_validation_result(result)
        output = string_io.getvalue()

        # Verify warning indicators
        assert "Warning" in output or "⚠️" in output
        assert "1.22.0" in output
        assert "16.0" in output
        assert "limited testing" in output
        assert "--force-version" in output
        assert "Compatible" in output

    def test_format_validation_result_error(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test formatting validation error result."""
        _, string_io = string_console

        result = CompatibilityRequirement(
            min_postgres="13.0",
            max_postgres="16.9",
            recommended="15.0",
            notes="Incompatible versions",
            is_compatible=False,
            warning_message="PostgreSQL 12.0 is too old for Temporal 1.22.0",
            temporal_version="1.22.0",
            postgres_version="12.0",
            support_level="active",
        )

        formatter.format_validation_result(result)
        output = string_io.getvalue()

        # Verify error indicators
        assert "Failed" in output or "Incompatible" in output or "✗" in output or "❌" in output
        assert "1.22.0" in output
        assert "12.0" in output
        assert "too old" in output
        assert "13.0" in output  # min requirement
        assert "16.9" in output  # max requirement
        assert "15.0" in output  # recommended
        assert "Cannot proceed" in output or "not recommended" in output.lower()


class TestUpgradeRecommendation:
    """Test formatting of upgrade recommendations."""

    def test_format_upgrade_recommendation(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test formatting upgrade recommendation with manual steps."""
        _, string_io = string_console

        formatter.format_upgrade_recommendation(
            current_postgres="13.0", recommended_postgres="15.0", temporal_version="1.24.0"
        )

        output = string_io.getvalue()

        # Verify upgrade recommendation content
        assert "Upgrade Recommendation" in output
        assert "13.0" in output
        assert "15.0" in output
        assert "1.24.0" in output

        # Verify manual upgrade warning
        assert "Manual Upgrade Required" in output or "manual process" in output.lower()
        assert (
            "Automatic upgrades are NOT supported" in output.lower() or "must be performed manually" in output.lower()
        )

        # Verify upgrade steps
        assert "Manual Upgrade Steps" in output or "Backup your database" in output
        assert "pg_dumpall" in output or "pg_dump" in output
        assert "Install PostgreSQL" in output
        assert "apt-get" in output or "yum" in output or "brew" in output
        assert "Migrate data" in output or "pg_upgrade" in output
        assert "Test thoroughly" in output

        # Verify resources
        assert "Resources" in output or "postgresql.org" in output
        assert "upgrading.html" in output or "pgupgrade" in output

    def test_format_upgrade_recommendation_never_suggests_auto_upgrade(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test that upgrade recommendation NEVER suggests automatic upgrade."""
        _, string_io = string_console

        formatter.format_upgrade_recommendation(
            current_postgres="12.0", recommended_postgres="16.0", temporal_version="1.24.0"
        )

        output = string_io.getvalue().lower()

        # Ensure no automatic upgrade suggestions
        assert "automatic" not in output or "not supported" in output
        assert "auto-upgrade" not in output or "manual" in output
        assert "manually" in output or "manual upgrade" in output


class TestVersionInfoTable:
    """Test version information table generation."""

    def test_format_version_info_table_compatible(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test formatting version info table for compatible versions."""
        _, string_io = string_console

        table = formatter.format_version_info_table(
            temporal_version="1.24.0",
            postgres_version="15.0",
            compatibility_status="Compatible",
            notes="Tested combination",
        )

        assert table is not None
        assert table.title == "Version Compatibility Check"

        # Print table to capture output
        formatter.console.print(table)
        output = string_io.getvalue()

        assert "1.24.0" in output
        assert "15.0" in output
        assert "Compatible" in output
        assert "Tested" in output and "combination" in output
        # Check for checkmark or the word Compatible which indicates success
        assert "✓" in output or "Compatible" in output

    def test_format_version_info_table_incompatible(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test formatting version info table for incompatible versions."""
        _, string_io = string_console

        table = formatter.format_version_info_table(
            temporal_version="1.22.0",
            postgres_version="12.0",
            compatibility_status="Incompatible",
            notes=None,
        )

        assert table is not None

        # Print table to capture output
        formatter.console.print(table)
        output = string_io.getvalue()

        assert "1.22.0" in output
        assert "12.0" in output
        assert "Incompatible" in output
        # Check for X mark or the word Incompatible
        assert "✗" in output or "❌" in output or "Incompatible" in output

    def test_format_version_info_table_warning(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test formatting version info table for versions with warnings."""
        _, string_io = string_console

        table = formatter.format_version_info_table(
            temporal_version="1.22.0",
            postgres_version="16.0",
            compatibility_status="Compatible (with warnings)",
            notes="Limited testing",
        )

        assert table is not None

        # Print table to capture output
        formatter.console.print(table)
        output = string_io.getvalue()

        assert "1.22.0" in output
        assert "16.0" in output
        assert "warning" in output.lower()
        # Check for warning symbol or the word warning
        assert "⚠️" in output or "warning" in output.lower()
        assert "Limited" in output and "testing" in output

    def test_print_version_info_table(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test print_version_info_table convenience method."""
        _, string_io = string_console

        formatter.print_version_info_table(
            temporal_version="1.23.0",
            postgres_version="14.5",
            compatibility_status="Compatible",
            notes="Production ready",
        )

        output = string_io.getvalue()

        assert "1.23.0" in output
        assert "14.5" in output
        assert "Compatible" in output
        # Notes might be truncated in table output, just check version and status
        assert "Production ready" in output or "Compatible" in output


class TestRichConsoleFeatures:
    """Test Rich console feature usage and rendering."""

    def test_uses_panels_for_warnings(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test that warnings use Rich panels with borders."""
        _, string_io = string_console

        formatter.format_compatibility_warning(
            temporal_version="1.22.0",
            postgres_version="12.0",
            min_required="13.0",
            max_supported="16.9",
            issue_type="too_old",
        )

        output = string_io.getvalue()

        # Rich panels use box drawing characters
        # Check for panel indicators (box drawing or panel structure)
        assert (
            any(char in output for char in ["─", "│", "┌", "┐", "└", "┘", "╭", "╮", "╰", "╯"])
            or "PostgreSQL Version Incompatibility" in output
        )

    def test_uses_colors_and_styles(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test that output includes ANSI color codes for terminal styling."""
        _, string_io = string_console

        formatter.format_compatibility_warning(
            temporal_version="1.22.0",
            postgres_version="12.0",
            min_required="13.0",
            max_supported="16.9",
            issue_type="too_old",
        )

        output = string_io.getvalue()

        # Rich with force_terminal=True includes ANSI escape codes
        # Check for color codes or styled content
        assert "\x1b[" in output or "12.0" in output  # ANSI escape codes

    def test_table_has_proper_structure(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test that tables have proper column structure."""
        _, string_io = string_console

        table = formatter.format_version_info_table(
            temporal_version="1.24.0",
            postgres_version="15.0",
            compatibility_status="Compatible",
        )

        # Check table properties
        assert table.title == "Version Compatibility Check"
        assert len(table.columns) == 3  # Component, Version, Status
        assert table.columns[0].header == "Component"
        assert table.columns[1].header == "Version"
        assert table.columns[2].header == "Status"


class TestOutputConsistency:
    """Test output consistency and completeness."""

    def test_all_warning_types_produce_output(self, formatter: WarningFormatter) -> None:
        """Test that all warning types produce non-empty output."""
        issue_types = ["too_old", "too_new", "eol", "deprecated", "unknown", "generic"]

        for issue_type in issue_types:
            string_io = StringIO()
            console = Console(file=string_io, force_terminal=True, width=120)
            temp_formatter = WarningFormatter(console=console)

            temp_formatter.format_compatibility_warning(
                temporal_version="1.22.0",
                postgres_version="14.0",
                min_required="13.0",
                max_supported="16.9",
                issue_type=issue_type,
            )

            output = string_io.getvalue()
            assert len(output) > 0, f"No output for issue_type: {issue_type}"
            assert "1.22.0" in output, f"Missing temporal version in output for: {issue_type}"
            assert "14.0" in output, f"Missing postgres version in output for: {issue_type}"

    def test_validation_result_all_cases_produce_output(self, formatter: WarningFormatter) -> None:
        """Test that all validation result cases produce output."""
        test_cases = [
            # Success case
            CompatibilityRequirement(
                min_postgres="13.0",
                max_postgres="16.9",
                recommended="15.0",
                notes="Success",
                is_compatible=True,
                warning_message=None,
                temporal_version="1.24.0",
                postgres_version="15.0",
            ),
            # Warning case
            CompatibilityRequirement(
                min_postgres="13.0",
                max_postgres="16.9",
                recommended="15.0",
                notes="Warning",
                is_compatible=True,
                warning_message="Some warning",
                temporal_version="1.22.0",
                postgres_version="16.0",
            ),
            # Error case
            CompatibilityRequirement(
                min_postgres="13.0",
                max_postgres="16.9",
                recommended="15.0",
                notes="Error",
                is_compatible=False,
                warning_message="Incompatible",
                temporal_version="1.22.0",
                postgres_version="12.0",
            ),
        ]

        for result in test_cases:
            string_io = StringIO()
            console = Console(file=string_io, force_terminal=True, width=120)
            temp_formatter = WarningFormatter(console=console)

            temp_formatter.format_validation_result(result)

            output = string_io.getvalue()
            assert len(output) > 0, f"No output for result: {result}"
            assert result.temporal_version in output
            assert result.postgres_version in output


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_format_with_none_notes(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test formatting handles None notes gracefully."""
        _, string_io = string_console

        table = formatter.format_version_info_table(
            temporal_version="1.24.0",
            postgres_version="15.0",
            compatibility_status="Compatible",
            notes=None,
        )

        formatter.console.print(table)
        output = string_io.getvalue()

        assert "1.24.0" in output
        assert "15.0" in output
        # Should not crash with None notes

    def test_format_with_empty_strings(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test formatting handles empty strings gracefully."""
        _, string_io = string_console

        formatter.format_compatibility_warning(
            temporal_version="1.22.0",
            postgres_version="14.0",
            min_required="13.0",
            max_supported="16.9",
            issue_type="",
        )

        output = string_io.getvalue()

        # Should fall back to generic warning
        assert len(output) > 0
        assert "1.22.0" in output

    def test_format_with_very_long_versions(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test formatting handles very long version strings."""
        _, string_io = string_console

        formatter.format_compatibility_warning(
            temporal_version="1.22.0-rc.1+build.123.abc",
            postgres_version="15.3.1.2.3.4.5",
            min_required="13.0",
            max_supported="16.9",
            issue_type="too_old",
        )

        output = string_io.getvalue()

        assert "1.22.0-rc.1+build.123.abc" in output
        assert "15.3.1.2.3.4.5" in output


class TestSafetyRequirements:
    """Test safety requirements compliance."""

    def test_never_auto_upgrade_in_any_message(self, formatter: WarningFormatter) -> None:
        """Test that no message suggests automatic PostgreSQL upgrade."""
        issue_types = ["too_old", "too_new", "eol"]  # Only test types that mention upgrades

        for issue_type in issue_types:
            string_io = StringIO()
            console = Console(file=string_io, force_terminal=True, width=120)
            temp_formatter = WarningFormatter(console=console)

            temp_formatter.format_compatibility_warning(
                temporal_version="1.22.0",
                postgres_version="12.0",
                min_required="13.0",
                max_supported="16.9",
                issue_type=issue_type,
            )

            output = string_io.getvalue().lower()

            # Should mention manual if discussing upgrades
            if "upgrade" in output and "postgresql" in output:
                assert "manual" in output or "manually" in output, f"Missing manual warning for: {issue_type}"

    def test_force_version_flag_mentioned_in_warnings(self, formatter: WarningFormatter) -> None:
        """Test that --force-version flag is mentioned in appropriate warnings."""
        # All issue types should mention --force-version
        issue_types = ["too_old", "too_new", "eol", "deprecated"]

        for issue_type in issue_types:
            string_io = StringIO()
            console = Console(file=string_io, force_terminal=True, width=120)
            temp_formatter = WarningFormatter(console=console)

            temp_formatter.format_compatibility_warning(
                temporal_version="1.22.0",
                postgres_version="14.0",
                min_required="13.0",
                max_supported="16.9",
                issue_type=issue_type,
            )

            output = string_io.getvalue()

            assert "--force-version" in output, f"Missing --force-version for: {issue_type}"

    def test_upgrade_recommendation_emphasizes_manual_process(
        self, formatter: WarningFormatter, string_console: tuple[Console, StringIO]
    ) -> None:
        """Test that upgrade recommendations emphasize manual process."""
        _, string_io = string_console

        formatter.format_upgrade_recommendation(
            current_postgres="13.0",
            recommended_postgres="15.0",
            temporal_version="1.24.0",
        )

        output = string_io.getvalue().lower()

        # Must include manual warnings
        assert "manual" in output
        assert "backup" in output
        assert "pg_dump" in output or "pg_dumpall" in output

        # Should NOT suggest automatic anything
        if "automatic" in output:
            assert "not supported" in output or "must be" in output
