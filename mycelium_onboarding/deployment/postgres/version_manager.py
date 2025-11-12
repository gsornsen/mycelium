"""PostgreSQL version management and compatibility matrix.

This module manages PostgreSQL version detection, compatibility checking,
and provides recommendations for version upgrades or downgrades.
"""

from __future__ import annotations

import logging
import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PostgresVersion(str, Enum):
    """Supported PostgreSQL major versions."""

    PG_12 = "12"
    PG_13 = "13"
    PG_14 = "14"
    PG_15 = "15"
    PG_16 = "16"
    PG_17 = "17"


class CompatibilityLevel(str, Enum):
    """Compatibility levels between PostgreSQL versions."""

    FULL = "full"  # Fully compatible, no changes needed
    COMPATIBLE = "compatible"  # Compatible with minor adjustments
    MIGRATION_REQUIRED = "migration_required"  # Requires migration steps
    INCOMPATIBLE = "incompatible"  # Not compatible


@dataclass
class VersionInfo:
    """Detailed PostgreSQL version information."""

    major: int
    minor: int
    patch: int
    full_version: str
    build_info: str | None = None

    @classmethod
    def from_string(cls, version_string: str) -> VersionInfo:
        """Parse version info from PostgreSQL version string.

        Args:
            version_string: Version string like "14.5" or "14.5 (Ubuntu 14.5-1ubuntu1)"

        Returns:
            VersionInfo object
        """
        # Extract numeric version
        match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", version_string)
        if not match:
            raise ValueError(f"Cannot parse version from: {version_string}")

        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3)) if match.group(3) else 0

        # Extract build info if present
        build_info = None
        if "(" in version_string and ")" in version_string:
            build_info = version_string[version_string.index("(") + 1 : version_string.rindex(")")]

        return cls(
            major=major, minor=minor, patch=patch, full_version=f"{major}.{minor}.{patch}", build_info=build_info
        )

    def to_major_version(self) -> PostgresVersion:
        """Convert to PostgresVersion enum."""
        try:
            return PostgresVersion(f"PG_{self.major}")
        except ValueError:
            # Return closest supported version
            if self.major < 12:
                return PostgresVersion.PG_12
            if self.major > 17:
                return PostgresVersion.PG_17
            return PostgresVersion.PG_16


class CompatibilityMatrix(BaseModel):
    """PostgreSQL version compatibility matrix."""

    # Compatibility rules between versions
    # Key: (source_version, target_version), Value: CompatibilityLevel
    matrix: dict[tuple[str, str], CompatibilityLevel] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True

    def __init__(self, **data: Any) -> None:
        """Initialize compatibility matrix with default rules.

        Args:
            **data: Additional data for BaseModel initialization
        """
        super().__init__(**data)
        self._init_default_matrix()

    def _init_default_matrix(self) -> None:
        """Initialize default compatibility matrix."""
        versions = [v.value for v in PostgresVersion]

        for source in versions:
            for target in versions:
                source_major = int(source)
                target_major = int(target)

                if source_major == target_major:
                    # Same version is fully compatible
                    self.matrix[(source, target)] = CompatibilityLevel.FULL
                elif target_major > source_major:
                    # Upgrading
                    diff = target_major - source_major
                    if diff == 1:
                        # One major version upgrade - compatible
                        self.matrix[(source, target)] = CompatibilityLevel.COMPATIBLE
                    elif diff <= 3:
                        # 2-3 major versions - migration required
                        self.matrix[(source, target)] = CompatibilityLevel.MIGRATION_REQUIRED
                    else:
                        # More than 3 versions - likely incompatible
                        self.matrix[(source, target)] = CompatibilityLevel.INCOMPATIBLE
                else:
                    # Downgrading
                    diff = source_major - target_major
                    if diff == 1:
                        # One major version downgrade - migration required
                        self.matrix[(source, target)] = CompatibilityLevel.MIGRATION_REQUIRED
                    else:
                        # More than 1 version downgrade - incompatible
                        self.matrix[(source, target)] = CompatibilityLevel.INCOMPATIBLE

    def get_compatibility(self, source: str, target: str) -> CompatibilityLevel:
        """Get compatibility level between two versions.

        Args:
            source: Source PostgreSQL version
            target: Target PostgreSQL version

        Returns:
            Compatibility level
        """
        return self.matrix.get((source, target), CompatibilityLevel.INCOMPATIBLE)


class FeatureCompatibility(BaseModel):
    """Feature compatibility information between PostgreSQL versions."""

    feature_name: str = Field(description="Name of the feature")
    introduced_in: str = Field(description="Version where feature was introduced")
    deprecated_in: str | None = Field(default=None, description="Version where feature was deprecated")
    removed_in: str | None = Field(default=None, description="Version where feature was removed")
    migration_path: str | None = Field(default=None, description="Migration path if feature is deprecated/removed")


def normalize_postgres_version(version_string: str) -> str:
    """Normalize PostgreSQL version string to X.Y format.

    Handles various input formats:
    - "PostgreSQL 15.3 on x86_64..." -> "15.3"
    - "psql (PostgreSQL) 16.0" -> "16.0"
    - "15" -> "15.0"
    - "15.3.1" -> "15.3"

    Args:
        version_string: Raw version string from various sources

    Returns:
        Normalized version in X.Y format (e.g., "15.3")

    Raises:
        ValueError: If version cannot be parsed
    """
    if not version_string:
        raise ValueError("Version string cannot be empty")

    version_string = version_string.strip()

    # Extract version from "PostgreSQL X.Y..." format
    if "PostgreSQL" in version_string or "postgresql" in version_string.lower():
        match = re.search(r"PostgreSQL\s+([\d.]+)", version_string, re.IGNORECASE)
        if match:
            version_string = match.group(1)

    # Extract version from "psql (PostgreSQL) X.Y" format
    if "psql" in version_string.lower():
        match = re.search(r"(\d+\.\d+(?:\.\d+)?)", version_string)
        if match:
            version_string = match.group(1)

    # Clean version string - remove 'v' prefix
    version_string = version_string.lstrip("vV")

    # Parse version components
    match = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", version_string)
    if not match:
        raise ValueError(f"Cannot parse PostgreSQL version from: {version_string}")

    major = match.group(1)
    minor = match.group(2) if match.group(2) else "0"

    # Return major.minor format (PostgreSQL standard)
    return f"{major}.{minor}"


class PostgresVersionManager:
    """Manages PostgreSQL version detection and compatibility."""

    # Feature compatibility database
    FEATURE_CHANGES = [
        FeatureCompatibility(
            feature_name="Parallel VACUUM", introduced_in="13", deprecated_in=None, removed_in=None, migration_path=None
        ),
        FeatureCompatibility(
            feature_name="Incremental Sorting",
            introduced_in="13",
            deprecated_in=None,
            removed_in=None,
            migration_path=None,
        ),
        FeatureCompatibility(
            feature_name="MERGE statement", introduced_in="15", deprecated_in=None, removed_in=None, migration_path=None
        ),
        FeatureCompatibility(
            feature_name="SQL/JSON path expressions",
            introduced_in="12",
            deprecated_in=None,
            removed_in=None,
            migration_path=None,
        ),
        FeatureCompatibility(
            feature_name="Generated Columns",
            introduced_in="12",
            deprecated_in=None,
            removed_in=None,
            migration_path=None,
        ),
        FeatureCompatibility(
            feature_name="recovery.conf",
            introduced_in="9.0",
            deprecated_in="12",
            removed_in="12",
            migration_path="Use postgresql.conf and standby.signal/recovery.signal files",
        ),
    ]

    def __init__(self) -> None:
        """Initialize version manager."""
        self.compatibility_matrix = CompatibilityMatrix()
        self._version_cache: dict[str, VersionInfo] = {}

    def detect_version_from_docker(self, container_name: str) -> str | None:
        """Detect PostgreSQL version from Docker container.

        Args:
            container_name: Name or ID of Docker container

        Returns:
            Normalized version string (e.g., "15.3") or None if detection fails
        """
        try:
            cmd = ["docker", "exec", container_name, "psql", "--version"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=5)

            if result.returncode != 0:
                logger.debug(f"Failed to detect PostgreSQL version from container {container_name}")
                return None

            version_output = result.stdout.strip()
            logger.debug(f"Docker container {container_name} version output: {version_output}")

            return normalize_postgres_version(version_output)

        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout detecting PostgreSQL version from container {container_name}")
            return None
        except Exception as e:
            logger.debug(f"Error detecting PostgreSQL version from Docker container: {e}")
            return None

    def detect_version_from_local(self) -> str | None:
        """Detect PostgreSQL version from local installation.

        Returns:
            Normalized version string (e.g., "15.3") or None if detection fails
        """
        try:
            cmd = ["psql", "--version"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=5)

            if result.returncode != 0:
                logger.debug("psql not found in PATH or failed to execute")
                return None

            version_output = result.stdout.strip()
            logger.debug(f"Local psql version output: {version_output}")

            return normalize_postgres_version(version_output)

        except FileNotFoundError:
            logger.debug("psql command not found")
            return None
        except subprocess.TimeoutExpired:
            logger.warning("Timeout detecting local PostgreSQL version")
            return None
        except Exception as e:
            logger.debug(f"Error detecting local PostgreSQL version: {e}")
            return None

    def detect_version_from_connection(self, connection_string: str) -> str | None:
        """Detect PostgreSQL version from remote connection.

        Executes SQL query: SELECT version()

        Args:
            connection_string: PostgreSQL connection string (e.g., "postgresql://user:pass@host:port/db")

        Returns:
            Normalized version string (e.g., "15.3") or None if detection fails
        """
        try:
            cmd = ["psql", connection_string, "-t", "-c", "SELECT version();"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=10)

            if result.returncode != 0:
                logger.debug(f"Failed to connect to PostgreSQL: {result.stderr}")
                return None

            version_output = result.stdout.strip()
            logger.debug(f"Remote connection version output: {version_output}")

            # Extract version from "PostgreSQL X.Y.Z on ..." format
            return normalize_postgres_version(version_output)

        except subprocess.TimeoutExpired:
            logger.warning("Timeout connecting to remote PostgreSQL")
            return None
        except Exception as e:
            logger.debug(f"Error detecting PostgreSQL version from connection: {e}")
            return None

    def detect_version_from_kubernetes(self, pod_name: str, namespace: str = "default") -> str | None:
        """Detect PostgreSQL version from Kubernetes pod.

        Args:
            pod_name: Name of Kubernetes pod
            namespace: Kubernetes namespace (default: "default")

        Returns:
            Normalized version string (e.g., "15.3") or None if detection fails
        """
        try:
            cmd = ["kubectl", "exec", "-n", namespace, pod_name, "--", "psql", "--version"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=10)

            if result.returncode != 0:
                logger.debug(f"Failed to detect PostgreSQL version from pod {pod_name}")
                return None

            version_output = result.stdout.strip()
            logger.debug(f"Kubernetes pod {pod_name} version output: {version_output}")

            return normalize_postgres_version(version_output)

        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout detecting PostgreSQL version from pod {pod_name}")
            return None
        except Exception as e:
            logger.debug(f"Error detecting PostgreSQL version from Kubernetes pod: {e}")
            return None

    def detect_version(self, connection_string: str | None = None) -> VersionInfo | None:
        """Detect PostgreSQL version.

        Args:
            connection_string: Optional connection string to use

        Returns:
            Version information or None if detection fails
        """
        try:
            if connection_string:
                # Use psql with connection string
                cmd = ["psql", connection_string, "-t", "-c", "SELECT version();"]
            else:
                # Use local psql
                cmd = ["psql", "--version"]

            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode != 0:
                return None

            version_str = result.stdout.strip()

            # Parse version
            if "SELECT version()" in " ".join(cmd):
                # Parse from SELECT version() output
                # Example: "PostgreSQL 14.5 on x86_64-pc-linux-gnu, compiled by..."
                match = re.search(r"PostgreSQL\s+([\d.]+)", version_str)
                if match:
                    version_str = match.group(1)
            else:
                # Parse from psql --version output
                # Example: "psql (PostgreSQL) 14.5"
                match = re.search(r"(\d+\.\d+(?:\.\d+)?)", version_str)
                if match:
                    version_str = match.group(1)

            return VersionInfo.from_string(version_str)

        except Exception as e:
            logger.debug(f"Error detecting PostgreSQL version: {e}")
            return None

    def check_compatibility(self, source_version: VersionInfo, target_version: VersionInfo) -> dict[str, Any]:
        """Check compatibility between two PostgreSQL versions.

        Args:
            source_version: Source version
            target_version: Target version

        Returns:
            Compatibility report
        """
        source_major = str(source_version.major)
        target_major = str(target_version.major)

        compatibility_level = self.compatibility_matrix.get_compatibility(source_major, target_major)

        # Check feature compatibility
        feature_issues = []
        feature_improvements = []

        for feature in self.FEATURE_CHANGES:
            # Check if feature is affected
            if feature.introduced_in:
                intro_version = int(feature.introduced_in)
                if source_version.major < intro_version <= target_version.major:
                    feature_improvements.append(
                        {
                            "feature": feature.feature_name,
                            "status": "newly_available",
                            "introduced_in": feature.introduced_in,
                        }
                    )

            if feature.removed_in:
                removed_version = int(feature.removed_in)
                if source_version.major < removed_version <= target_version.major:
                    feature_issues.append(
                        {
                            "feature": feature.feature_name,
                            "status": "removed",
                            "removed_in": feature.removed_in,
                            "migration_path": feature.migration_path,
                        }
                    )

            if feature.deprecated_in:
                deprecated_version = int(feature.deprecated_in)
                if source_version.major < deprecated_version <= target_version.major:
                    feature_issues.append(
                        {
                            "feature": feature.feature_name,
                            "status": "deprecated",
                            "deprecated_in": feature.deprecated_in,
                            "migration_path": feature.migration_path,
                        }
                    )

        return {
            "source_version": source_version.full_version,
            "target_version": target_version.full_version,
            "compatibility_level": compatibility_level.value,
            "is_upgrade": target_version.major > source_version.major,
            "major_version_diff": abs(target_version.major - source_version.major),
            "feature_issues": feature_issues,
            "feature_improvements": feature_improvements,
            "recommendations": self._generate_recommendations(
                source_version, target_version, compatibility_level, feature_issues
            ),
        }

    def _generate_recommendations(
        self,
        source_version: VersionInfo,
        target_version: VersionInfo,
        compatibility_level: CompatibilityLevel,
        feature_issues: list[dict[str, Any]],
    ) -> list[str]:
        """Generate migration recommendations.

        Args:
            source_version: Source version
            target_version: Target version
            compatibility_level: Compatibility level
            feature_issues: List of feature compatibility issues

        Returns:
            List of recommendations
        """
        recommendations = []

        if compatibility_level == CompatibilityLevel.FULL:
            recommendations.append("Versions are fully compatible. Direct migration is possible.")

        elif compatibility_level == CompatibilityLevel.COMPATIBLE:
            recommendations.append("Versions are compatible with minor adjustments.")
            recommendations.append("Review release notes for behavioral changes.")
            recommendations.append("Test application thoroughly after migration.")

        elif compatibility_level == CompatibilityLevel.MIGRATION_REQUIRED:
            recommendations.append("Migration steps are required for this version change.")
            recommendations.append("Create a full backup before proceeding.")
            recommendations.append("Use pg_upgrade for in-place upgrade if possible.")
            recommendations.append("Consider using logical replication for zero-downtime migration.")

            if feature_issues:
                recommendations.append("Address the following feature compatibility issues:")
                for issue in feature_issues:
                    if issue.get("migration_path"):
                        recommendations.append(f"  - {issue['feature']}: {issue['migration_path']}")

        elif compatibility_level == CompatibilityLevel.INCOMPATIBLE:
            recommendations.append("Direct migration is not recommended due to incompatibility.")
            recommendations.append("Consider a staged migration through intermediate versions.")
            recommendations.append("Consult PostgreSQL documentation for major version differences.")

        # Add specific recommendations based on version differences
        if source_version.major < 12 and target_version.major >= 12:
            recommendations.append("Note: recovery.conf is replaced by postgresql.conf settings in v12+")

        if source_version.major < 13 and target_version.major >= 13:
            recommendations.append("New feature available: Parallel VACUUM for improved maintenance")

        if source_version.major < 14 and target_version.major >= 14:
            recommendations.append("Performance improvement: Better query parallelization in v14+")

        if source_version.major < 15 and target_version.major >= 15:
            recommendations.append("New SQL feature: MERGE statement available in v15+")

        return recommendations

    def get_supported_versions(self) -> list[str]:
        """Get list of supported PostgreSQL versions.

        Returns:
            List of supported version strings
        """
        return [v.value for v in PostgresVersion]

    def recommend_version(self, current_version: VersionInfo | None = None) -> str:
        """Recommend the best PostgreSQL version to use.

        Args:
            current_version: Current version if upgrading

        Returns:
            Recommended version string
        """
        # Default recommendation is the latest stable LTS-like version
        recommended = PostgresVersion.PG_15  # v15 is a good stable choice

        if current_version:
            current_major = current_version.major

            # If already on a recent version, stay on it
            if current_major >= 15:
                return str(current_major)

            # If on an older version, recommend upgrading to v15
            # unless they're on v14 which is also very stable
            if current_major == 14:
                return "14"

        return recommended.value

    def get_migration_path(self, source_version: VersionInfo, target_version: VersionInfo) -> list[str]:
        """Get recommended migration path between versions.

        Args:
            source_version: Source version
            target_version: Target version

        Returns:
            List of migration steps
        """
        steps = []

        if source_version.major == target_version.major:
            # Same major version - simple upgrade
            steps.append(f"Direct upgrade from {source_version.full_version} to {target_version.full_version}")
            steps.append("1. Backup database")
            steps.append("2. Stop PostgreSQL service")
            steps.append("3. Upgrade PostgreSQL packages")
            steps.append("4. Start PostgreSQL service")
            steps.append("5. Run ANALYZE to update statistics")

        elif target_version.major > source_version.major:
            # Major version upgrade
            diff = target_version.major - source_version.major

            if diff == 1:
                # Single major version upgrade
                steps.append(f"Upgrade from PostgreSQL {source_version.major} to {target_version.major}")
                steps.append("1. Review release notes for breaking changes")
                steps.append("2. Backup database using pg_dumpall")
                steps.append("3. Install new PostgreSQL version")
                steps.append("4. Run pg_upgrade for in-place upgrade")
                steps.append("5. Update configuration files")
                steps.append("6. Test application compatibility")
                steps.append("7. Run VACUUM ANALYZE on all databases")

            else:
                # Multiple major version upgrade
                steps.append(f"Multi-version upgrade from PostgreSQL {source_version.major} to {target_version.major}")
                steps.append("Consider upgrading through intermediate versions:")

                current = source_version.major
                while current < target_version.major:
                    next_version = min(current + 2, target_version.major)
                    steps.append(f"  - Upgrade from {current} to {next_version}")
                    current = next_version

                steps.append("For each intermediate upgrade:")
                steps.append("  1. Backup database")
                steps.append("  2. Run pg_upgrade")
                steps.append("  3. Test functionality")
                steps.append("  4. Update statistics")

        else:
            # Downgrade (not recommended)
            steps.append("WARNING: Downgrading PostgreSQL is not recommended")
            steps.append("If downgrade is necessary:")
            steps.append("1. Export data using pg_dumpall")
            steps.append("2. Install target PostgreSQL version")
            steps.append("3. Create new database cluster")
            steps.append("4. Import data")
            steps.append("5. Verify data integrity")

        return steps
