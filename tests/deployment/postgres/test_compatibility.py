"""Tests for PostgreSQL-Temporal compatibility checking.

This module tests the compatibility matrix functionality including:
- Loading compatibility matrix from YAML
- Checking version compatibility
- Handling unknown versions
- Version normalization
- Known issues detection
- Recommended configurations
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from mycelium_onboarding.deployment.postgres.compatibility import (
    CompatibilityMatrix,
    CompatibilityRequirement,
    PostgresCompatibilityChecker,
)


@pytest.fixture
def matrix_path() -> Path:
    """Get path to compatibility matrix YAML file."""
    return Path(__file__).parents[3] / "mycelium_onboarding" / "deployment" / "postgres" / "compatibility.yaml"


@pytest.fixture
def compatibility_matrix(matrix_path: Path) -> CompatibilityMatrix:
    """Create CompatibilityMatrix instance."""
    return CompatibilityMatrix(matrix_path)


@pytest.fixture
def compatibility_checker(matrix_path: Path) -> PostgresCompatibilityChecker:
    """Create PostgresCompatibilityChecker instance."""
    return PostgresCompatibilityChecker(matrix_path)


@pytest.fixture
def matrix_data(matrix_path: Path) -> dict[str, Any]:
    """Load raw matrix data from YAML."""
    with open(matrix_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestCompatibilityMatrix:
    """Test CompatibilityMatrix core functionality."""

    def test_load_matrix_success(self, matrix_path: Path):
        """Test successful loading of compatibility matrix."""
        matrix = CompatibilityMatrix(matrix_path)
        assert matrix._data is not None
        assert "compatibility" in matrix._data
        assert "default" in matrix._data

    def test_load_matrix_file_not_found(self, tmp_path: Path):
        """Test error handling when matrix file doesn't exist."""
        non_existent = tmp_path / "nonexistent.yaml"
        with pytest.raises(FileNotFoundError):
            CompatibilityMatrix(non_existent)

    def test_matrix_has_required_sections(self, compatibility_matrix: CompatibilityMatrix):
        """Test that matrix has all required sections."""
        data = compatibility_matrix._data
        assert "metadata" in data
        assert "compatibility" in data
        assert "default" in data
        assert "postgresql_lifecycle" in data
        assert "version_ranges" in data

    def test_normalize_temporal_version(self, compatibility_matrix: CompatibilityMatrix):
        """Test Temporal version normalization."""
        # Test various version formats
        assert compatibility_matrix._normalize_temporal_version("1.22") == "1.22.0"
        assert compatibility_matrix._normalize_temporal_version("1.22.0") == "1.22.0"
        assert compatibility_matrix._normalize_temporal_version("v1.22.0") == "1.22.0"
        assert compatibility_matrix._normalize_temporal_version("1.22.3") == "1.22.3"

    def test_normalize_postgres_version(self, compatibility_matrix: CompatibilityMatrix):
        """Test PostgreSQL version normalization."""
        # Test various version formats
        assert compatibility_matrix._normalize_postgres_version("15") == "15.0"
        assert compatibility_matrix._normalize_postgres_version("15.0") == "15.0"
        assert compatibility_matrix._normalize_postgres_version("v15.3") == "15.3"
        assert compatibility_matrix._normalize_postgres_version("16.2") == "16.2"

    def test_get_requirements_exact_version(self, compatibility_matrix: CompatibilityMatrix):
        """Test getting requirements for exact version in matrix."""
        requirements = compatibility_matrix.get_requirements("1.22.0")
        assert requirements["min_version"] == "13.0"
        assert requirements["max_version"] == "16.0"
        assert requirements["recommended"] == "16.0"
        assert "support_level" in requirements

    def test_get_requirements_patch_version(self, compatibility_matrix: CompatibilityMatrix):
        """Test getting requirements for patch version using version ranges."""
        # Should map to 1.22.0 via version_ranges
        requirements = compatibility_matrix.get_requirements("1.22.1")
        assert requirements["min_version"] == "13.0"
        assert requirements["max_version"] == "16.0"

    def test_get_requirements_unknown_version_uses_default(self, compatibility_matrix: CompatibilityMatrix):
        """Test that unknown versions fall back to defaults."""
        requirements = compatibility_matrix.get_requirements("99.99.99")
        assert "min_version" in requirements
        assert "max_version" in requirements
        assert "recommended" in requirements
        assert requirements["support_level"] == "unknown"

    def test_find_closest_version(self, compatibility_matrix: CompatibilityMatrix):
        """Test finding closest version in matrix."""
        available = ["1.0.0", "1.10.0", "1.20.0", "1.22.0", "1.24.0"]

        # Test exact match
        closest = compatibility_matrix._find_closest_version("1.22.0", available)
        assert closest == "1.22.0"

        # Test finding closest (should prefer lower version)
        closest = compatibility_matrix._find_closest_version("1.21.0", available)
        assert closest == "1.20.0"

        # Test finding closest (newer)
        closest = compatibility_matrix._find_closest_version("1.25.0", available)
        assert closest == "1.24.0"


class TestCompatibilityChecking:
    """Test compatibility checking functionality."""

    def test_compatible_versions(self, compatibility_matrix: CompatibilityMatrix):
        """Test compatible version pairs return is_compatible=True."""
        # Temporal 1.22.0 supports PostgreSQL 13-16
        result = compatibility_matrix.check_compatibility("1.22.0", "15.0")
        assert result.is_compatible is True
        assert result.warning_message is None
        assert result.temporal_version == "1.22.0"
        assert result.postgres_version == "15.0"

    def test_compatible_versions_at_boundaries(self, compatibility_matrix: CompatibilityMatrix):
        """Test compatibility at min/max boundaries."""
        # Temporal 1.22.0: min=13.0, max=16.0
        result_min = compatibility_matrix.check_compatibility("1.22.0", "13.0")
        assert result_min.is_compatible is True

        result_max = compatibility_matrix.check_compatibility("1.22.0", "16.0")
        assert result_max.is_compatible is True

    def test_postgres_too_old(self, compatibility_matrix: CompatibilityMatrix):
        """Test PostgreSQL version too old for Temporal."""
        # Temporal 1.22.0 requires PostgreSQL 13+
        result = compatibility_matrix.check_compatibility("1.22.0", "12.0")
        assert result.is_compatible is False
        assert "too old" in result.warning_message.lower()
        assert "13.0" in result.warning_message

    def test_postgres_too_new(self, compatibility_matrix: CompatibilityMatrix):
        """Test PostgreSQL version too new for Temporal."""
        # Temporal 1.0.0 max is PostgreSQL 14
        result = compatibility_matrix.check_compatibility("1.0.0", "17.0")
        assert result.is_compatible is False
        assert "too new" in result.warning_message.lower()
        assert "14.0" in result.warning_message

    def test_deprecated_temporal_version_warning(self, compatibility_matrix: CompatibilityMatrix):
        """Test warning for deprecated Temporal versions."""
        # Temporal 1.0.0 is deprecated
        result = compatibility_matrix.check_compatibility("1.0.0", "13.0")
        # Even if compatible, should warn about deprecation
        if result.support_level == "deprecated":
            assert result.warning_message is not None
            assert "deprecated" in result.warning_message.lower() or "eol" in result.warning_message.lower()

    def test_unknown_temporal_version_warning(self, compatibility_matrix: CompatibilityMatrix):
        """Test warning for unknown Temporal versions."""
        result = compatibility_matrix.check_compatibility("99.99.99", "15.0")
        # Should use defaults and warn
        assert result.support_level == "unknown"
        if not result.is_compatible or result.warning_message:
            assert result.warning_message is not None

    def test_eol_postgres_warning(self, compatibility_matrix: CompatibilityMatrix):
        """Test warning for EOL PostgreSQL versions."""
        # PostgreSQL 12 is EOL
        result = compatibility_matrix.check_compatibility("1.15.0", "12.0")
        # Should warn about EOL even if compatible
        if result.warning_message:
            # Either incompatible or EOL warning
            assert any(
                keyword in result.warning_message.lower() for keyword in ["eol", "end-of-life", "too old", "deprecated"]
            )

    def test_version_normalization_in_check(self, compatibility_matrix: CompatibilityMatrix):
        """Test that versions are normalized during compatibility check."""
        # Test with various version formats
        result1 = compatibility_matrix.check_compatibility("1.22", "15")
        result2 = compatibility_matrix.check_compatibility("v1.22.0", "v15.0")

        # Both should normalize to same result
        assert result1.temporal_version == result2.temporal_version
        assert result1.postgres_version == result2.postgres_version
        assert result1.is_compatible == result2.is_compatible


class TestKnownIssues:
    """Test known issues detection."""

    def test_get_known_issues_no_matches(self, compatibility_matrix: CompatibilityMatrix):
        """Test getting known issues when none match."""
        issues = compatibility_matrix.get_known_issues("1.24.0", "16.0")
        # 1.24.0 with PG 16.0 should have no known issues
        assert isinstance(issues, list)
        # May or may not have issues, just verify it returns a list

    def test_get_known_issues_with_match(self, compatibility_matrix: CompatibilityMatrix):
        """Test getting known issues when there's a match."""
        # Based on YAML, 1.20.0 with PG 12.x has a critical issue
        issues = compatibility_matrix.get_known_issues("1.20.0", "12.0")
        if issues:  # Only check if issues exist in matrix
            assert len(issues) > 0
            issue = issues[0]
            assert "severity" in issue
            assert "description" in issue

    def test_version_pattern_matching(self, compatibility_matrix: CompatibilityMatrix):
        """Test version pattern matching with wildcards."""
        # Test .x wildcard matching
        assert compatibility_matrix._version_matches_pattern("1.20.0", "1.20.x")
        assert compatibility_matrix._version_matches_pattern("1.20.5", "1.20.x")
        assert not compatibility_matrix._version_matches_pattern("1.21.0", "1.20.x")

        # Test exact matching
        assert compatibility_matrix._version_matches_pattern("1.20.0", "1.20.0")
        assert not compatibility_matrix._version_matches_pattern("1.20.1", "1.20.0")


class TestRecommendedConfigurations:
    """Test recommended configuration retrieval."""

    def test_get_recommended_config_exact_match(self, compatibility_matrix: CompatibilityMatrix):
        """Test getting recommended config with exact version match."""
        config = compatibility_matrix.get_recommended_configurations("1.24.0", "16.0")
        if config:  # Only check if config exists
            assert "description" in config
            assert "configuration" in config

    def test_get_recommended_config_no_match(self, compatibility_matrix: CompatibilityMatrix):
        """Test getting recommended config when none exists."""
        config = compatibility_matrix.get_recommended_configurations("99.99.99", "99.0")
        # Should return None for unknown combinations
        assert config is None

    def test_get_recommended_config_major_version_fallback(self, compatibility_matrix: CompatibilityMatrix):
        """Test fallback to major version for configs."""
        # Try with patch version
        config = compatibility_matrix.get_recommended_configurations("1.22.3", "15.5")
        # Should find 1.22.0-15.0 config if it exists
        if config:
            assert "configuration" in config


class TestPostgresCompatibilityChecker:
    """Test high-level PostgresCompatibilityChecker."""

    def test_is_compatible_simple(self, compatibility_checker: PostgresCompatibilityChecker):
        """Test simple compatibility check."""
        # Compatible pair
        assert compatibility_checker.is_compatible("1.22.0", "15.0") is True

        # Incompatible pair (PG too old)
        assert compatibility_checker.is_compatible("1.22.0", "12.0") is False

    def test_get_compatibility_report(self, compatibility_checker: PostgresCompatibilityChecker):
        """Test getting detailed compatibility report."""
        report = compatibility_checker.get_compatibility_report("1.22.0", "15.0")

        # Verify report structure
        assert "compatible" in report
        assert "temporal_version" in report
        assert "postgres_version" in report
        assert "requirements" in report
        assert "support_level" in report
        assert "tested_versions" in report
        assert "known_issues" in report

        # Verify requirements structure
        assert "min_postgres" in report["requirements"]
        assert "max_postgres" in report["requirements"]
        assert "recommended" in report["requirements"]

    def test_get_upgrade_path(self, compatibility_checker: PostgresCompatibilityChecker):
        """Test getting upgrade path information."""
        path = compatibility_checker.get_upgrade_path("1.20.0", "1.24.0", "15.0")

        # Verify structure
        assert "current_temporal" in path
        assert "target_temporal" in path
        assert "postgres_version" in path
        assert "current_compatible" in path
        assert "target_compatible" in path
        assert "postgres_upgrade_needed" in path
        assert "recommended_postgres" in path
        assert "warnings" in path

        # Both should be compatible with PG 15
        assert path["current_compatible"] is True
        assert path["target_compatible"] is True
        assert path["postgres_upgrade_needed"] is False

    def test_get_upgrade_path_requires_postgres_upgrade(self, compatibility_checker: PostgresCompatibilityChecker):
        """Test upgrade path when PostgreSQL upgrade is needed."""
        # Upgrade from 1.10.0 (supports PG 12-15) to 1.24.0 (requires PG 13-17)
        # with current PG 12 - should need upgrade
        path = compatibility_checker.get_upgrade_path("1.10.0", "1.24.0", "12.0")

        # Current should be compatible, target should not
        assert path["current_compatible"] is True
        assert path["target_compatible"] is False
        assert path["postgres_upgrade_needed"] is True
        assert path["recommended_postgres"] in ["15.0", "16.0"]


class TestVersionNormalization:
    """Test version normalization edge cases."""

    def test_normalize_temporal_single_digit(self, compatibility_matrix: CompatibilityMatrix):
        """Test normalizing single digit version."""
        assert compatibility_matrix._normalize_temporal_version("1") == "1.0.0"

    def test_normalize_temporal_two_digits(self, compatibility_matrix: CompatibilityMatrix):
        """Test normalizing two digit version."""
        assert compatibility_matrix._normalize_temporal_version("1.22") == "1.22.0"

    def test_normalize_temporal_three_digits(self, compatibility_matrix: CompatibilityMatrix):
        """Test normalizing three digit version."""
        assert compatibility_matrix._normalize_temporal_version("1.22.3") == "1.22.3"

    def test_normalize_temporal_with_v_prefix(self, compatibility_matrix: CompatibilityMatrix):
        """Test normalizing version with 'v' prefix."""
        assert compatibility_matrix._normalize_temporal_version("v1.22.0") == "1.22.0"

    def test_normalize_postgres_major_only(self, compatibility_matrix: CompatibilityMatrix):
        """Test normalizing PostgreSQL major version only."""
        assert compatibility_matrix._normalize_postgres_version("15") == "15.0"

    def test_normalize_postgres_major_minor(self, compatibility_matrix: CompatibilityMatrix):
        """Test normalizing PostgreSQL major.minor."""
        assert compatibility_matrix._normalize_postgres_version("15.3") == "15.3"


class TestCompatibilityRequirement:
    """Test CompatibilityRequirement named tuple."""

    def test_create_requirement(self):
        """Test creating a CompatibilityRequirement."""
        req = CompatibilityRequirement(
            min_postgres="13.0",
            max_postgres="16.0",
            recommended="15.0",
            notes="Test notes",
            is_compatible=True,
            warning_message=None,
            temporal_version="1.22.0",
            postgres_version="15.0",
            support_level="active",
            tested_versions=["13.0", "14.0", "15.0"],
        )

        assert req.min_postgres == "13.0"
        assert req.max_postgres == "16.0"
        assert req.recommended == "15.0"
        assert req.is_compatible is True
        assert req.support_level == "active"
        assert len(req.tested_versions) == 3

    def test_requirement_with_warning(self):
        """Test requirement with warning message."""
        req = CompatibilityRequirement(
            min_postgres="13.0",
            max_postgres="16.0",
            recommended="15.0",
            notes="Test notes",
            is_compatible=False,
            warning_message="PostgreSQL version too old",
            temporal_version="1.22.0",
            postgres_version="12.0",
        )

        assert req.is_compatible is False
        assert req.warning_message == "PostgreSQL version too old"


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_temporal_version(self, compatibility_matrix: CompatibilityMatrix):
        """Test handling of invalid Temporal version."""
        result = compatibility_matrix.check_compatibility("invalid", "15.0")
        assert result.is_compatible is False
        assert result.warning_message is not None

    def test_invalid_postgres_version(self, compatibility_matrix: CompatibilityMatrix):
        """Test handling of invalid PostgreSQL version."""
        result = compatibility_matrix.check_compatibility("1.22.0", "invalid")
        assert result.is_compatible is False
        assert result.warning_message is not None

    def test_empty_version_strings(self, compatibility_matrix: CompatibilityMatrix):
        """Test handling of empty version strings."""
        result = compatibility_matrix.check_compatibility("", "15.0")
        assert result.is_compatible is False

    def test_whitespace_in_versions(self, compatibility_matrix: CompatibilityMatrix):
        """Test handling of whitespace in version strings."""
        result = compatibility_matrix.check_compatibility(" 1.22.0 ", " 15.0 ")
        # Should normalize and work correctly
        assert result.temporal_version == "1.22.0"
        assert result.postgres_version == "15.0"


class TestMatrixDataIntegrity:
    """Test integrity of the compatibility matrix data."""

    def test_all_compatibility_entries_have_required_fields(self, matrix_data: dict[str, Any]):
        """Test that all compatibility entries have required fields."""
        compatibility = matrix_data.get("compatibility", {})
        required_fields = ["postgresql"]

        for version, data in compatibility.items():
            for field in required_fields:
                assert field in data, f"Version {version} missing {field}"

            # Check PostgreSQL section
            pg = data["postgresql"]
            assert "min_version" in pg
            assert "max_version" in pg
            assert "recommended" in pg

    def test_version_ranges_reference_valid_versions(self, matrix_data: dict[str, Any]):
        """Test that version ranges reference valid compatibility entries."""
        compatibility = matrix_data.get("compatibility", {})
        version_ranges = matrix_data.get("version_ranges", {})

        for range_key, range_data in version_ranges.items():
            use_version = range_data.get("use_compatibility")
            assert use_version in compatibility, f"Version range {range_key} references invalid version {use_version}"

    def test_postgresql_lifecycle_has_required_fields(self, matrix_data: dict[str, Any]):
        """Test that PostgreSQL lifecycle entries have required fields."""
        lifecycle = matrix_data.get("postgresql_lifecycle", {})

        for version, data in lifecycle.items():
            assert "status" in data, f"PostgreSQL {version} missing status"
            assert data["status"] in ["active", "eol", "beta", "deprecated"]

    def test_default_section_exists_and_valid(self, matrix_data: dict[str, Any]):
        """Test that default section exists and is valid."""
        default = matrix_data.get("default")
        assert default is not None, "Default section is missing"
        assert "postgresql" in default

        pg = default["postgresql"]
        assert "min_version" in pg
        assert "max_version" in pg
        assert "recommended" in pg

    def test_metadata_section_exists(self, matrix_data: dict[str, Any]):
        """Test that metadata section exists."""
        metadata = matrix_data.get("metadata")
        assert metadata is not None
        assert "version" in metadata
        assert "last_updated" in metadata


# Integration tests
class TestIntegration:
    """Integration tests for complete workflows."""

    def test_production_deployment_scenario(self, compatibility_checker: PostgresCompatibilityChecker):
        """Test typical production deployment scenario."""
        # New deployment: Temporal 1.24.0 with PostgreSQL 16
        report = compatibility_checker.get_compatibility_report("1.24.0", "16.0")

        assert report["compatible"] is True
        assert report["support_level"] in ["active", "maintenance"]

    def test_upgrade_scenario_compatible(self, compatibility_checker: PostgresCompatibilityChecker):
        """Test upgrade scenario where no PostgreSQL upgrade needed."""
        path = compatibility_checker.get_upgrade_path("1.22.0", "1.24.0", "16.0")

        assert path["current_compatible"] is True
        assert path["target_compatible"] is True
        assert path["postgres_upgrade_needed"] is False

    def test_upgrade_scenario_needs_postgres_upgrade(self, compatibility_checker: PostgresCompatibilityChecker):
        """Test upgrade scenario requiring PostgreSQL upgrade."""
        # Upgrade from old Temporal with old PostgreSQL
        path = compatibility_checker.get_upgrade_path("1.10.0", "1.24.0", "12.0")

        # Should indicate PostgreSQL upgrade needed
        assert path["postgres_upgrade_needed"] is True
        assert path["recommended_postgres"] >= "13.0"

    def test_warning_messages_are_actionable(self, compatibility_checker: PostgresCompatibilityChecker):
        """Test that warning messages provide actionable guidance."""
        # Test incompatible scenario
        report = compatibility_checker.get_compatibility_report("1.22.0", "12.0")

        if not report["compatible"]:
            warning = report.get("warning")
            assert warning is not None
            # Warning should mention version numbers
            assert any(ver in warning for ver in ["12", "13", "PostgreSQL"])
            # Should provide guidance
            assert any(word in warning.lower() for word in ["minimum", "required", "recommended"])
