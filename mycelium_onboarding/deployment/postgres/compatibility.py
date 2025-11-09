"""PostgreSQL-Temporal compatibility checking.

This module provides functionality to check compatibility between PostgreSQL
and Temporal server versions using the compatibility matrix defined in
compatibility.yaml.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, NamedTuple

import yaml
from packaging.version import InvalidVersion, Version, parse

logger = logging.getLogger(__name__)


class CompatibilityRequirement(NamedTuple):
    """PostgreSQL compatibility requirement for a Temporal version.

    Attributes:
        min_postgres: Minimum PostgreSQL version required
        max_postgres: Maximum PostgreSQL version supported
        recommended: Recommended PostgreSQL version
        notes: Additional compatibility notes
        is_compatible: Whether the versions are compatible
        warning_message: Warning message if not compatible or other issues
        temporal_version: Temporal version this requirement is for
        postgres_version: PostgreSQL version being checked
        support_level: Support level (active, maintenance, deprecated, unknown)
        tested_versions: List of tested PostgreSQL versions
    """

    min_postgres: str
    max_postgres: str
    recommended: str
    notes: str
    is_compatible: bool
    warning_message: str | None = None
    temporal_version: str = ""
    postgres_version: str = ""
    support_level: str = "unknown"
    tested_versions: list[str] = []


class CompatibilityMatrix:
    """PostgreSQL-Temporal compatibility matrix manager.

    This class loads and manages the compatibility matrix from YAML,
    providing methods to check version compatibility and get requirements.
    """

    def __init__(self, matrix_path: Path | None = None):
        """Initialize compatibility matrix.

        Args:
            matrix_path: Path to compatibility.yaml file.
                        If None, uses default path relative to this module.
        """
        if matrix_path is None:
            matrix_path = Path(__file__).parent / "compatibility.yaml"

        self.matrix_path = matrix_path
        self._data: dict[str, Any] = {}
        self._load_matrix()

    def _load_matrix(self) -> None:
        """Load compatibility matrix from YAML file.

        Raises:
            FileNotFoundError: If matrix file doesn't exist
            yaml.YAMLError: If matrix file is invalid YAML
        """
        if not self.matrix_path.exists():
            raise FileNotFoundError(f"Compatibility matrix not found: {self.matrix_path}")

        try:
            with open(self.matrix_path, encoding="utf-8") as f:
                self._data = yaml.safe_load(f)
            logger.info(f"Loaded compatibility matrix from {self.matrix_path}")
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse compatibility matrix: {e}")
            raise

    def check_compatibility(self, temporal_version: str, postgres_version: str) -> CompatibilityRequirement:
        """Check if PostgreSQL version is compatible with Temporal version.

        Args:
            temporal_version: Temporal version string (e.g., "1.22.0")
            postgres_version: PostgreSQL version string (e.g., "15.0")

        Returns:
            CompatibilityRequirement with compatibility status and details
        """
        # Normalize versions
        try:
            temporal_ver = self._normalize_temporal_version(temporal_version)
            postgres_ver = self._normalize_postgres_version(postgres_version)
        except InvalidVersion as e:
            logger.error(f"Invalid version format: {e}")
            return CompatibilityRequirement(
                min_postgres="0.0.0",
                max_postgres="999.0.0",
                recommended="16.0",
                notes=f"Invalid version format: {e}",
                is_compatible=False,
                warning_message=f"Cannot parse version: {e}",
                temporal_version=temporal_version,
                postgres_version=postgres_version,
            )

        # Get requirements for this Temporal version
        requirements = self.get_requirements(temporal_ver)

        # Check if PostgreSQL version is within supported range
        min_pg = parse(requirements["min_version"])
        max_pg = parse(requirements["max_version"])
        current_pg = parse(postgres_ver)

        is_compatible = min_pg <= current_pg <= max_pg
        warning_message = None

        if not is_compatible:
            if current_pg < min_pg:
                warning_message = (
                    f"PostgreSQL {postgres_ver} is too old for Temporal {temporal_ver}. "
                    f"Minimum required: PostgreSQL {requirements['min_version']}. "
                    f"Recommended: PostgreSQL {requirements['recommended']}."
                )
            else:  # current_pg > max_pg
                warning_message = (
                    f"PostgreSQL {postgres_ver} is too new for Temporal {temporal_ver}. "
                    f"Maximum supported: PostgreSQL {requirements['max_version']}. "
                    f"Recommended: PostgreSQL {requirements['recommended']}."
                )
        else:
            # Check for warnings even when compatible
            if requirements.get("support_level") == "deprecated":
                warning_message = (
                    f"Temporal {temporal_ver} is deprecated (EOL: {requirements.get('eol_date', 'unknown')}). "
                    f"Consider upgrading to a newer version."
                )
            elif requirements.get("support_level") == "unknown":
                warning_message = (
                    f"Temporal {temporal_ver} is not in the compatibility matrix. "
                    f"Using conservative defaults. Please verify compatibility manually."
                )
            else:
                # Check PostgreSQL lifecycle status even when compatible
                pg_lifecycle = self._check_postgres_lifecycle(postgres_ver)
                if pg_lifecycle:
                    warning_message = pg_lifecycle

        return CompatibilityRequirement(
            min_postgres=requirements["min_version"],
            max_postgres=requirements["max_version"],
            recommended=requirements["recommended"],
            notes=requirements["notes"],
            is_compatible=is_compatible,
            warning_message=warning_message,
            temporal_version=temporal_ver,
            postgres_version=postgres_ver,
            support_level=requirements.get("support_level", "unknown"),
            tested_versions=requirements.get("tested_versions", []),
        )

    def get_requirements(self, temporal_version: str) -> dict[str, Any]:
        """Get PostgreSQL requirements for a Temporal version.

        Args:
            temporal_version: Temporal version string (e.g., "1.22.0")

        Returns:
            Dictionary with PostgreSQL version requirements
        """
        # Normalize version
        try:
            temporal_ver = self._normalize_temporal_version(temporal_version)
        except InvalidVersion:
            logger.warning(f"Invalid Temporal version: {temporal_version}, using defaults")
            return self._get_default_requirements()

        # Check if exact version exists in compatibility matrix
        compatibility = self._data.get("compatibility", {})
        if temporal_ver in compatibility:
            req = compatibility[temporal_ver]["postgresql"]
            return {
                "min_version": req["min_version"],
                "max_version": req["max_version"],
                "recommended": req["recommended"],
                "notes": req.get("notes", ""),
                "support_level": req.get("support_level", "unknown"),
                "tested_versions": req.get("tested_versions", []),
                "eol_date": req.get("eol_date"),
            }

        # Check version ranges for patch versions
        version_ranges = self._data.get("version_ranges", {})
        for range_key, range_data in version_ranges.items():
            if temporal_ver in range_data.get("applies_to", []):
                use_version = range_data["use_compatibility"]
                if use_version in compatibility:
                    req = compatibility[use_version]["postgresql"]
                    return {
                        "min_version": req["min_version"],
                        "max_version": req["max_version"],
                        "recommended": req["recommended"],
                        "notes": req.get("notes", ""),
                        "support_level": req.get("support_level", "unknown"),
                        "tested_versions": req.get("tested_versions", []),
                        "eol_date": req.get("eol_date"),
                    }

        # Try to find closest version
        closest_version = self._find_closest_version(temporal_ver, list(compatibility.keys()))
        if closest_version:
            logger.warning(f"Temporal {temporal_ver} not found, using closest version {closest_version}")
            req = compatibility[closest_version]["postgresql"]
            return {
                "min_version": req["min_version"],
                "max_version": req["max_version"],
                "recommended": req["recommended"],
                "notes": f"Using compatibility data from {closest_version}. {req.get('notes', '')}",
                "support_level": "unknown",
                "tested_versions": req.get("tested_versions", []),
                "eol_date": None,
            }

        # Fall back to defaults
        logger.warning(f"Temporal {temporal_ver} not found in matrix, using defaults")
        return self._get_default_requirements()

    def _get_default_requirements(self) -> dict[str, Any]:
        """Get default PostgreSQL requirements for unknown Temporal versions.

        Returns:
            Dictionary with default PostgreSQL requirements
        """
        default = self._data.get("default", {})
        if default and "postgresql" in default:
            pg = default["postgresql"]
            return {
                "min_version": pg["min_version"],
                "max_version": pg["max_version"],
                "recommended": pg["recommended"],
                "notes": pg.get("notes", "Unknown Temporal version - using conservative defaults"),
                "support_level": "unknown",
                "tested_versions": pg.get("tested_versions", []),
                "eol_date": None,
            }

        # Hardcoded fallback if YAML is missing defaults
        return {
            "min_version": "13.0",
            "max_version": "17.0",
            "recommended": "16.0",
            "notes": "Unknown Temporal version - using conservative PostgreSQL requirements",
            "support_level": "unknown",
            "tested_versions": [],
            "eol_date": None,
        }

    def _find_closest_version(self, target: str, available: list[str]) -> str | None:
        """Find closest known Temporal version in matrix.

        Args:
            target: Target version to find (e.g., "1.21.5")
            available: List of available versions in matrix

        Returns:
            Closest version string or None if no close match found
        """
        try:
            target_ver = parse(target)
        except InvalidVersion:
            return None

        # Parse all available versions
        version_pairs: list[tuple[Version, str]] = []
        for ver_str in available:
            try:
                version_pairs.append((parse(ver_str), ver_str))
            except InvalidVersion:
                continue

        if not version_pairs:
            return None

        # Sort by version
        version_pairs.sort(key=lambda x: x[0])

        # Find closest version (prefer lower version for compatibility)
        closest = None
        min_distance = float("inf")

        for ver, ver_str in version_pairs:
            # Calculate distance (major.minor.patch)
            distance = abs(
                (target_ver.major - ver.major) * 10000
                + (target_ver.minor - ver.minor) * 100
                + (getattr(target_ver, "micro", 0) - getattr(ver, "micro", 0))
            )

            if distance < min_distance:
                min_distance = distance
                closest = ver_str
            elif distance == min_distance and ver < parse(closest or "0.0.0"):
                # Prefer lower version if distance is same
                closest = ver_str

        return closest

    def _normalize_temporal_version(self, version: str) -> str:
        """Normalize Temporal version string.

        Args:
            version: Version string (e.g., "1.22", "v1.22.0")

        Returns:
            Normalized version (e.g., "1.22.0")

        Raises:
            InvalidVersion: If version cannot be parsed
        """
        # Remove 'v' prefix
        version = version.strip().lstrip("v")

        parsed = parse(version)
        base = parsed.base_version

        # Ensure major.minor.patch format
        parts = base.split(".")
        if len(parts) == 1:
            return f"{parts[0]}.0.0"
        if len(parts) == 2:
            return f"{parts[0]}.{parts[1]}.0"
        return ".".join(parts[:3])

    def _normalize_postgres_version(self, version: str) -> str:
        """Normalize PostgreSQL version string.

        Handles version aliases from the matrix (e.g., "12" -> "12.0").

        Args:
            version: Version string (e.g., "15", "15.0", "v15.3")

        Returns:
            Normalized version (e.g., "15.0")

        Raises:
            InvalidVersion: If version cannot be parsed
        """
        # Remove 'v' prefix
        version = version.strip().lstrip("v")

        # Check for aliases in matrix
        aliases = self._data.get("postgresql_lifecycle", {})
        # If version is just major version (e.g., "15"), add ".0"
        if version.isdigit() and version in aliases:
            return f"{version}.0"

        parsed = parse(version)
        base = parsed.base_version

        # Ensure major.minor format (PostgreSQL uses major.minor)
        parts = base.split(".")
        if len(parts) == 1:
            return f"{parts[0]}.0"
        return ".".join(parts[:2])

    def _check_postgres_lifecycle(self, postgres_version: str) -> str | None:
        """Check PostgreSQL version lifecycle status.

        Args:
            postgres_version: PostgreSQL version (e.g., "15.0")

        Returns:
            Warning message if version is EOL or near EOL, None otherwise
        """
        lifecycle = self._data.get("postgresql_lifecycle", {})

        # Extract major version
        try:
            major = postgres_version.split(".")[0]
        except (IndexError, AttributeError):
            return None

        if major not in lifecycle:
            return None

        version_info = lifecycle[major]
        status = version_info.get("status", "unknown")

        if status == "eol":
            return (
                f"PostgreSQL {major} is end-of-life (EOL: {version_info.get('eol_date', 'unknown')}). "
                f"Upgrade to a supported version is strongly recommended."
            )

        return None

    def get_known_issues(self, temporal_version: str, postgres_version: str) -> list[dict[str, Any]]:
        """Get known compatibility issues for version combination.

        Args:
            temporal_version: Temporal version
            postgres_version: PostgreSQL version

        Returns:
            List of known issues with severity and workarounds
        """
        known_issues = self._data.get("known_issues", [])
        matching_issues = []

        for issue in known_issues:
            # Check if issue matches versions (support wildcards)
            if self._version_matches_pattern(
                temporal_version, issue["temporal_version"]
            ) and self._version_matches_pattern(postgres_version, issue["postgres_version"]):
                matching_issues.append(issue)

        return matching_issues

    def _version_matches_pattern(self, version: str, pattern: str) -> bool:
        """Check if version matches pattern (supports .x wildcard).

        Args:
            version: Version string (e.g., "1.22.0")
            pattern: Pattern (e.g., "1.22.x", "1.20.0")

        Returns:
            True if version matches pattern
        """
        # Handle .x wildcard
        if ".x" in pattern:
            pattern_prefix = pattern.replace(".x", "")
            return version.startswith(pattern_prefix)

        # Exact match
        return version == pattern

    def get_recommended_configurations(self, temporal_version: str, postgres_version: str) -> dict[str, Any] | None:
        """Get recommended PostgreSQL configuration for version combination.

        Args:
            temporal_version: Temporal version
            postgres_version: PostgreSQL version

        Returns:
            Recommended configuration dict or None if not found
        """
        configs = self._data.get("recommended_configurations", {})

        # Try exact match first
        key = f"{temporal_version}-{postgres_version}"
        if key in configs:
            return configs[key]

        # Try major version combinations
        try:
            temporal_major_minor = ".".join(temporal_version.split(".")[:2]) + ".0"
            postgres_major = postgres_version.split(".")[0] + ".0"
            key = f"{temporal_major_minor}-{postgres_major}"
            if key in configs:
                return configs[key]
        except (IndexError, AttributeError):
            pass

        return None


class PostgresCompatibilityChecker:
    """High-level PostgreSQL compatibility checker.

    Provides convenient methods for checking compatibility and getting
    detailed compatibility reports.
    """

    def __init__(self, matrix_path: Path | None = None):
        """Initialize compatibility checker.

        Args:
            matrix_path: Path to compatibility.yaml file
        """
        self.matrix = CompatibilityMatrix(matrix_path)

    def is_compatible(self, temporal_version: str, postgres_version: str) -> bool:
        """Check if versions are compatible.

        Args:
            temporal_version: Temporal version
            postgres_version: PostgreSQL version

        Returns:
            True if compatible, False otherwise
        """
        result = self.matrix.check_compatibility(temporal_version, postgres_version)
        return result.is_compatible

    def get_compatibility_report(self, temporal_version: str, postgres_version: str) -> dict[str, Any]:
        """Get detailed compatibility report.

        Args:
            temporal_version: Temporal version
            postgres_version: PostgreSQL version

        Returns:
            Detailed compatibility report
        """
        result = self.matrix.check_compatibility(temporal_version, postgres_version)
        issues = self.matrix.get_known_issues(temporal_version, postgres_version)
        config = self.matrix.get_recommended_configurations(temporal_version, postgres_version)

        return {
            "compatible": result.is_compatible,
            "temporal_version": result.temporal_version,
            "postgres_version": result.postgres_version,
            "requirements": {
                "min_postgres": result.min_postgres,
                "max_postgres": result.max_postgres,
                "recommended": result.recommended,
            },
            "support_level": result.support_level,
            "tested_versions": result.tested_versions,
            "warning": result.warning_message,
            "notes": result.notes,
            "known_issues": issues,
            "recommended_configuration": config,
        }

    def get_upgrade_path(self, current_temporal: str, target_temporal: str, postgres_version: str) -> dict[str, Any]:
        """Get upgrade path information.

        Args:
            current_temporal: Current Temporal version
            target_temporal: Target Temporal version
            postgres_version: PostgreSQL version

        Returns:
            Upgrade path information with compatibility checks
        """
        current_compat = self.matrix.check_compatibility(current_temporal, postgres_version)
        target_compat = self.matrix.check_compatibility(target_temporal, postgres_version)

        return {
            "current_temporal": current_temporal,
            "target_temporal": target_temporal,
            "postgres_version": postgres_version,
            "current_compatible": current_compat.is_compatible,
            "target_compatible": target_compat.is_compatible,
            "postgres_upgrade_needed": not target_compat.is_compatible,
            "recommended_postgres": target_compat.recommended,
            "warnings": [w for w in [current_compat.warning_message, target_compat.warning_message] if w is not None],
        }
