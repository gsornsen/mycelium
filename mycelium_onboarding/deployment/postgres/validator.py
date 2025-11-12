"""PostgreSQL version validation engine.

This module provides comprehensive validation of PostgreSQL versions against
Temporal requirements, generating clear actionable warnings and recommendations
for deployment compatibility issues.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, NamedTuple

from mycelium_onboarding.deployment.postgres.compatibility import (
    PostgresCompatibilityChecker,
)
from mycelium_onboarding.deployment.postgres.temporal_detector import (
    detect_temporal_version,
)

logger = logging.getLogger(__name__)


class ValidationResult(NamedTuple):
    """Result of PostgreSQL-Temporal compatibility validation.

    Attributes:
        is_compatible: Whether versions are compatible
        temporal_version: Detected or specified Temporal version
        postgres_version: PostgreSQL version being validated
        warning_message: Warning message if compatibility issues exist
        error_message: Error message for critical failures
        recommended_action: Actionable recommendation for user
        can_proceed: True if user can continue with --force flag
        support_level: Support level (active, maintenance, deprecated, unknown)
        requires_postgres_upgrade: True if PostgreSQL needs upgrading
        requires_temporal_downgrade: True if Temporal should be downgraded
    """

    is_compatible: bool
    temporal_version: str
    postgres_version: str
    warning_message: str | None
    error_message: str | None
    recommended_action: str
    can_proceed: bool
    support_level: str = "unknown"
    requires_postgres_upgrade: bool = False
    requires_temporal_downgrade: bool = False

    def format_message(self) -> str:
        """Format validation result as user-friendly message.

        Returns:
            Formatted multi-line message for display
        """
        lines = []

        if self.is_compatible:
            lines.append("✓ PostgreSQL Compatibility Check: PASSED")
            lines.append(f"  Temporal Version: {self.temporal_version}")
            lines.append(f"  PostgreSQL Version: {self.postgres_version}")
            lines.append(f"  Support Level: {self.support_level}")

            if self.warning_message:
                lines.append("")
                lines.append(f"⚠️  Warning: {self.warning_message}")
        else:
            lines.append("✗ PostgreSQL Compatibility Check: FAILED")
            lines.append("")
            lines.append(f"  Current PostgreSQL: {self.postgres_version}")
            lines.append(f"  Temporal Version: {self.temporal_version}")

            if self.error_message:
                lines.append("")
                lines.append(f"Error: {self.error_message}")

            if self.warning_message:
                lines.append("")
                lines.append(self.warning_message)

        lines.append("")
        lines.append(f"Recommended Action: {self.recommended_action}")

        if not self.is_compatible and self.can_proceed:
            lines.append("")
            lines.append("You can override this check with --force-version (not recommended)")

        return "\n".join(lines)


class PostgresValidator:
    """PostgreSQL-Temporal compatibility validator.

    This class validates PostgreSQL versions against Temporal version requirements,
    providing clear, actionable feedback for deployment planning.
    """

    def __init__(self, project_dir: Path | None = None):
        """Initialize PostgreSQL validator.

        Args:
            project_dir: Path to project directory for Temporal detection.
                        If None, uses current working directory.
        """
        self.project_dir = project_dir or Path.cwd()
        self.compatibility_checker = PostgresCompatibilityChecker()

    def validate_deployment(
        self,
        postgres_version: str,
        temporal_version: str | None = None,
    ) -> ValidationResult:
        """Validate PostgreSQL version against Temporal requirements.

        This is the main entry point for deployment validation.

        Args:
            postgres_version: PostgreSQL version to validate (e.g., "15.3")
            temporal_version: Optional explicit Temporal version.
                            If None, attempts to detect from project.

        Returns:
            ValidationResult with compatibility status and recommendations
        """
        # 1. Determine Temporal version (detect or use provided)
        if temporal_version:
            # Use explicitly provided version
            temporal_ver = temporal_version
            temporal_source = "explicit"
            logger.info(f"Using explicit Temporal version: {temporal_version}")
        else:
            # Detect from project
            temporal_info = detect_temporal_version(self.project_dir)

            if not temporal_info:
                return self._build_no_temporal_result(postgres_version)

            temporal_ver = temporal_info.version
            temporal_source = temporal_info.source_file.name
            logger.info(f"Detected Temporal version {temporal_ver} from {temporal_source}")

        # 2. Check compatibility
        compatibility_report = self.compatibility_checker.get_compatibility_report(temporal_ver, postgres_version)

        # 3. Build validation result
        return self._build_validation_result(temporal_ver, postgres_version, compatibility_report)

    def validate_upgrade_path(
        self,
        current_postgres: str,
        target_postgres: str,
        temporal_version: str | None = None,
    ) -> ValidationResult:
        """Validate PostgreSQL upgrade path for Temporal compatibility.

        Args:
            current_postgres: Current PostgreSQL version
            target_postgres: Target PostgreSQL version to upgrade to
            temporal_version: Optional Temporal version, auto-detected if None

        Returns:
            ValidationResult for the upgrade path
        """
        # Detect Temporal version if not provided
        if not temporal_version:
            temporal_info = detect_temporal_version(self.project_dir)
            if not temporal_info:
                return self._build_no_temporal_result(target_postgres)
            temporal_version = temporal_info.version

        # Validate target version compatibility
        target_result = self.validate_deployment(target_postgres, temporal_version)

        if not target_result.is_compatible:
            return ValidationResult(
                is_compatible=False,
                temporal_version=temporal_version,
                postgres_version=f"{current_postgres} → {target_postgres}",
                warning_message=(
                    f"Upgrade to PostgreSQL {target_postgres} would be incompatible with Temporal {temporal_version}"
                ),
                error_message=target_result.error_message,
                recommended_action=(
                    f"Choose a PostgreSQL version compatible with Temporal {temporal_version}, "
                    f"or upgrade Temporal to a version supporting PostgreSQL {target_postgres}"
                ),
                can_proceed=False,
                support_level=target_result.support_level,
            )

        # Upgrade path is valid
        return ValidationResult(
            is_compatible=True,
            temporal_version=temporal_version,
            postgres_version=f"{current_postgres} → {target_postgres}",
            warning_message=target_result.warning_message,
            error_message=None,
            recommended_action=(
                f"PostgreSQL upgrade from {current_postgres} to {target_postgres} is compatible. "
                "Proceed with standard PostgreSQL upgrade procedures: backup, test, and verify."
            ),
            can_proceed=True,
            support_level=target_result.support_level,
        )

    def _build_validation_result(
        self,
        temporal_version: str,
        postgres_version: str,
        compatibility_report: dict[str, Any],
    ) -> ValidationResult:
        """Build ValidationResult from compatibility report.

        Args:
            temporal_version: Temporal version being validated
            postgres_version: PostgreSQL version being validated
            compatibility_report: Report from PostgresCompatibilityChecker

        Returns:
            Complete ValidationResult
        """
        is_compatible = compatibility_report["compatible"]
        support_level = compatibility_report["support_level"]
        warning = compatibility_report.get("warning")
        requirements = compatibility_report["requirements"]

        # Determine if PostgreSQL upgrade or Temporal downgrade is needed
        requires_pg_upgrade = False
        requires_temporal_downgrade = False

        if not is_compatible:
            # Parse versions to determine what action is needed
            try:
                from packaging.version import parse

                pg_ver = parse(postgres_version)
                min_pg = parse(requirements["min_postgres"])
                max_pg = parse(requirements["max_postgres"])

                if pg_ver < min_pg:
                    requires_pg_upgrade = True
                elif pg_ver > max_pg:
                    requires_temporal_downgrade = True
            except Exception as e:
                logger.debug(f"Error parsing versions for action determination: {e}")

        # Build warning message
        warning_message = self._build_warning_message(
            is_compatible,
            temporal_version,
            postgres_version,
            requirements,
            support_level,
            warning,
            requires_pg_upgrade,
            requires_temporal_downgrade,
        )

        # Build recommended action
        recommended_action = self._build_recommended_action(
            is_compatible,
            temporal_version,
            postgres_version,
            requirements,
            support_level,
            requires_pg_upgrade,
            requires_temporal_downgrade,
        )

        # Determine if user can proceed with --force
        can_proceed = self._can_force_proceed(
            is_compatible, support_level, requires_pg_upgrade, requires_temporal_downgrade
        )

        # Build error message for critical failures
        error_message = None
        if not is_compatible and not can_proceed:
            error_message = (
                f"PostgreSQL {postgres_version} is fundamentally incompatible with "
                f"Temporal {temporal_version}. Deployment cannot proceed."
            )

        return ValidationResult(
            is_compatible=is_compatible,
            temporal_version=temporal_version,
            postgres_version=postgres_version,
            warning_message=warning_message,
            error_message=error_message,
            recommended_action=recommended_action,
            can_proceed=can_proceed,
            support_level=support_level,
            requires_postgres_upgrade=requires_pg_upgrade,
            requires_temporal_downgrade=requires_temporal_downgrade,
        )

    def _build_no_temporal_result(self, postgres_version: str) -> ValidationResult:
        """Build result when Temporal version cannot be detected.

        Args:
            postgres_version: PostgreSQL version being validated

        Returns:
            ValidationResult indicating detection failure
        """
        return ValidationResult(
            is_compatible=False,
            temporal_version="unknown",
            postgres_version=postgres_version,
            warning_message=None,
            error_message="Cannot detect Temporal version from project dependencies",
            recommended_action=(
                "Ensure Temporal SDK is listed in project dependencies "
                "(pyproject.toml, requirements.txt, or poetry.lock), "
                "or manually specify Temporal version with --temporal-version flag"
            ),
            can_proceed=False,
        )

    def _build_warning_message(
        self,
        is_compatible: bool,
        temporal_version: str,
        postgres_version: str,
        requirements: dict[str, Any],
        support_level: str,  # noqa: ARG002
        existing_warning: str | None,
        requires_pg_upgrade: bool,
        requires_temporal_downgrade: bool,
    ) -> str | None:
        """Build detailed warning message.

        Args:
            is_compatible: Whether versions are compatible
            temporal_version: Temporal version
            postgres_version: PostgreSQL version
            requirements: PostgreSQL requirements from compatibility matrix
            support_level: Support level (active, deprecated, etc.)
            existing_warning: Warning from compatibility checker
            requires_pg_upgrade: Whether PostgreSQL upgrade is needed
            requires_temporal_downgrade: Whether Temporal downgrade is needed

        Returns:
            Warning message or None
        """
        if not is_compatible:
            # Build incompatibility warning
            lines = ["⚠️  PostgreSQL Compatibility Warning", ""]

            if requires_pg_upgrade:
                lines.append(f"PostgreSQL {postgres_version} is too old for Temporal {temporal_version}")
                lines.append(
                    f"Required: PostgreSQL {requirements['min_postgres']}+ (recommended: {requirements['recommended']})"
                )
            elif requires_temporal_downgrade:
                lines.append(f"PostgreSQL {postgres_version} is too new for Temporal {temporal_version}")
                lines.append(
                    f"Maximum supported: PostgreSQL {requirements['max_postgres']} "
                    f"(recommended: {requirements['recommended']})"
                )
            else:
                lines.append(f"PostgreSQL {postgres_version} is incompatible with Temporal {temporal_version}")

            return "\n".join(lines)

        # Compatible but has warnings (EOL, deprecated, etc.)
        if existing_warning:
            return existing_warning

        return None

    def _build_recommended_action(
        self,
        is_compatible: bool,
        temporal_version: str,
        postgres_version: str,
        requirements: dict[str, Any],
        support_level: str,
        requires_pg_upgrade: bool,
        requires_temporal_downgrade: bool,
    ) -> str:
        """Build recommended action message.

        Args:
            is_compatible: Whether versions are compatible
            temporal_version: Temporal version
            postgres_version: PostgreSQL version
            requirements: PostgreSQL requirements
            support_level: Support level
            requires_pg_upgrade: Whether PostgreSQL upgrade needed
            requires_temporal_downgrade: Whether Temporal downgrade needed

        Returns:
            Recommended action message
        """
        if is_compatible:
            if support_level == "deprecated":
                return (
                    f"Consider upgrading Temporal {temporal_version} to a newer, supported version. "
                    "Current deployment can proceed but may have limited support."
                )
            if support_level == "unknown":
                return (
                    "Temporal version not in compatibility matrix. "
                    "Manually verify compatibility with PostgreSQL documentation before proceeding."
                )
            return "Deployment can proceed. Versions are compatible."

        # Incompatible - provide specific actions
        actions = []

        if requires_pg_upgrade:
            actions.append(f"Option 1: Upgrade PostgreSQL to {requirements['recommended']} or higher")
            actions.append("  - Backup your database completely")
            actions.append(
                "  - Follow PostgreSQL upgrade guide: https://www.postgresql.org/docs/current/upgrading.html"
            )
            actions.append("  - Test thoroughly before deploying Temporal")
            actions.append("")
            actions.append(f"Option 2: Downgrade Temporal to a version supporting PostgreSQL {postgres_version}")
            actions.append("  - Check compatibility matrix for compatible Temporal versions")
            actions.append("  - Update project dependencies accordingly")
        elif requires_temporal_downgrade:
            actions.append(f"Option 1: Use PostgreSQL {requirements['recommended']} (recommended)")
            actions.append("  - Deploy PostgreSQL within the supported version range")
            actions.append("")
            actions.append(f"Option 2: Upgrade Temporal to a version supporting PostgreSQL {postgres_version}")
            actions.append("  - Update Temporal SDK in project dependencies")
            actions.append("  - Review Temporal release notes for breaking changes")
        else:
            actions.append(
                f"Use PostgreSQL {requirements['recommended']} (recommended version for Temporal {temporal_version})"
            )

        return "\n".join(actions)

    def _can_force_proceed(
        self,
        is_compatible: bool,
        support_level: str,  # noqa: ARG002
        requires_pg_upgrade: bool,
        requires_temporal_downgrade: bool,
    ) -> bool:
        """Determine if deployment can proceed with --force flag.

        Args:
            is_compatible: Whether versions are compatible
            support_level: Support level
            requires_pg_upgrade: Whether PostgreSQL upgrade needed
            requires_temporal_downgrade: Whether Temporal downgrade needed

        Returns:
            True if --force can override validation failure
        """
        # Always allow force for compatible versions
        if is_compatible:
            return True

        # Allow force for minor incompatibilities (e.g., slightly too new/old)
        # but not for critical incompatibilities
        return requires_pg_upgrade or requires_temporal_downgrade


def validate_postgres_for_temporal(
    postgres_version: str,
    project_dir: Path | None = None,
    temporal_version: str | None = None,
) -> ValidationResult:
    """Convenience function to validate PostgreSQL version for Temporal deployment.

    Args:
        postgres_version: PostgreSQL version to validate
        project_dir: Optional project directory for Temporal detection
        temporal_version: Optional explicit Temporal version

    Returns:
        ValidationResult with compatibility status

    Example:
        >>> result = validate_postgres_for_temporal("15.3", Path("/my/project"))
        >>> if not result.is_compatible:
        ...     print(result.format_message())
    """
    validator = PostgresValidator(project_dir)
    return validator.validate_deployment(postgres_version, temporal_version)
