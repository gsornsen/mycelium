"""Tests for PostgreSQL version manager enhancements.

This test suite validates PostgreSQL version detection and normalization
across various deployment environments.
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from mycelium_onboarding.deployment.postgres.version_manager import (
    PostgresVersionManager,
    VersionInfo,
    normalize_postgres_version,
)


class TestNormalizePostgresVersion:
    """Test PostgreSQL version normalization function."""

    def test_normalize_full_version_string(self):
        """Test normalization from full PostgreSQL output."""
        version_string = "PostgreSQL 15.3 on x86_64-pc-linux-gnu, compiled by gcc"
        normalized = normalize_postgres_version(version_string)
        assert normalized == "15.3"

    def test_normalize_psql_version_output(self):
        """Test normalization from psql --version output."""
        version_string = "psql (PostgreSQL) 16.0"
        normalized = normalize_postgres_version(version_string)
        assert normalized == "16.0"

    def test_normalize_major_only(self):
        """Test normalization when only major version provided."""
        normalized = normalize_postgres_version("15")
        assert normalized == "15.0"

    def test_normalize_major_minor_patch(self):
        """Test normalization with major.minor.patch format."""
        normalized = normalize_postgres_version("15.3.1")
        assert normalized == "15.3"

    def test_normalize_with_v_prefix(self):
        """Test normalization with 'v' prefix."""
        normalized = normalize_postgres_version("v16.2")
        assert normalized == "16.2"

    def test_normalize_case_insensitive(self):
        """Test normalization is case-insensitive."""
        version_string = "postgresql 15.3 on x86_64"
        normalized = normalize_postgres_version(version_string)
        assert normalized == "15.3"

    def test_normalize_with_extra_whitespace(self):
        """Test normalization handles extra whitespace."""
        normalized = normalize_postgres_version("  15.3  ")
        assert normalized == "15.3"

    def test_normalize_invalid_version_raises_error(self):
        """Test normalization raises ValueError for invalid input."""
        with pytest.raises(ValueError, match="Cannot parse PostgreSQL version"):
            normalize_postgres_version("invalid")

    def test_normalize_empty_string_raises_error(self):
        """Test normalization raises ValueError for empty string."""
        with pytest.raises(ValueError, match="Version string cannot be empty"):
            normalize_postgres_version("")


class TestPostgresVersionManager:
    """Test PostgresVersionManager class."""

    @pytest.fixture
    def version_manager(self) -> PostgresVersionManager:
        """Create PostgresVersionManager instance for testing.

        Returns:
            PostgresVersionManager instance
        """
        return PostgresVersionManager()

    def test_initialization(self, version_manager: PostgresVersionManager):
        """Test version manager initialization."""
        assert version_manager.compatibility_matrix is not None
        assert isinstance(version_manager._version_cache, dict)

    def test_get_supported_versions(self, version_manager: PostgresVersionManager):
        """Test getting list of supported PostgreSQL versions."""
        versions = version_manager.get_supported_versions()
        assert isinstance(versions, list)
        assert len(versions) > 0
        assert "13" in versions
        assert "15" in versions
        assert "16" in versions


class TestDockerVersionDetection:
    """Test PostgreSQL version detection from Docker containers."""

    @pytest.fixture
    def version_manager(self) -> PostgresVersionManager:
        """Create version manager instance."""
        return PostgresVersionManager()

    @patch("subprocess.run")
    def test_detect_version_from_docker_success(self, mock_run: MagicMock, version_manager: PostgresVersionManager):
        """Test successful version detection from Docker container."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "psql (PostgreSQL) 15.3"
        mock_run.return_value = mock_result

        version = version_manager.detect_version_from_docker("postgres-container")

        assert version == "15.3"
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "docker"
        assert cmd[1] == "exec"
        assert "postgres-container" in cmd

    @patch("subprocess.run")
    def test_detect_version_from_docker_failure(self, mock_run: MagicMock, version_manager: PostgresVersionManager):
        """Test version detection failure from Docker container."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        version = version_manager.detect_version_from_docker("nonexistent-container")

        assert version is None

    @patch("subprocess.run")
    def test_detect_version_from_docker_timeout(self, mock_run: MagicMock, version_manager: PostgresVersionManager):
        """Test version detection timeout from Docker container."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="docker", timeout=5)

        version = version_manager.detect_version_from_docker("slow-container")

        assert version is None

    @patch("subprocess.run")
    def test_detect_version_from_docker_exception(self, mock_run: MagicMock, version_manager: PostgresVersionManager):
        """Test version detection handles exceptions from Docker."""
        mock_run.side_effect = Exception("Docker error")

        version = version_manager.detect_version_from_docker("error-container")

        assert version is None


class TestLocalVersionDetection:
    """Test PostgreSQL version detection from local installation."""

    @pytest.fixture
    def version_manager(self) -> PostgresVersionManager:
        """Create version manager instance."""
        return PostgresVersionManager()

    @patch("subprocess.run")
    def test_detect_version_from_local_success(self, mock_run: MagicMock, version_manager: PostgresVersionManager):
        """Test successful version detection from local installation."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "psql (PostgreSQL) 16.0"
        mock_run.return_value = mock_result

        version = version_manager.detect_version_from_local()

        assert version == "16.0"
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd == ["psql", "--version"]

    @patch("subprocess.run")
    def test_detect_version_from_local_not_installed(
        self, mock_run: MagicMock, version_manager: PostgresVersionManager
    ):
        """Test version detection when psql not installed."""
        mock_run.side_effect = FileNotFoundError("psql not found")

        version = version_manager.detect_version_from_local()

        assert version is None

    @patch("subprocess.run")
    def test_detect_version_from_local_failed_execution(
        self, mock_run: MagicMock, version_manager: PostgresVersionManager
    ):
        """Test version detection when psql fails to execute."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        version = version_manager.detect_version_from_local()

        assert version is None


class TestRemoteConnectionDetection:
    """Test PostgreSQL version detection from remote connections."""

    @pytest.fixture
    def version_manager(self) -> PostgresVersionManager:
        """Create version manager instance."""
        return PostgresVersionManager()

    @patch("subprocess.run")
    def test_detect_version_from_connection_success(self, mock_run: MagicMock, version_manager: PostgresVersionManager):
        """Test successful version detection from remote connection."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "PostgreSQL 15.3 on x86_64-pc-linux-gnu, compiled by gcc 11.3.0"
        mock_run.return_value = mock_result

        connection_string = "postgresql://user:pass@localhost:5432/db"
        version = version_manager.detect_version_from_connection(connection_string)

        assert version == "15.3"
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "psql" in cmd
        assert connection_string in cmd
        assert "SELECT version" in " ".join(cmd)

    @patch("subprocess.run")
    def test_detect_version_from_connection_failure(self, mock_run: MagicMock, version_manager: PostgresVersionManager):
        """Test version detection failure from connection."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "FATAL: password authentication failed"
        mock_run.return_value = mock_result

        connection_string = "postgresql://baduser:badpass@localhost:5432/db"
        version = version_manager.detect_version_from_connection(connection_string)

        assert version is None

    @patch("subprocess.run")
    def test_detect_version_from_connection_timeout(self, mock_run: MagicMock, version_manager: PostgresVersionManager):
        """Test version detection timeout from connection."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="psql", timeout=10)

        connection_string = "postgresql://user:pass@slow-host:5432/db"
        version = version_manager.detect_version_from_connection(connection_string)

        assert version is None


class TestKubernetesVersionDetection:
    """Test PostgreSQL version detection from Kubernetes pods."""

    @pytest.fixture
    def version_manager(self) -> PostgresVersionManager:
        """Create version manager instance."""
        return PostgresVersionManager()

    @patch("subprocess.run")
    def test_detect_version_from_kubernetes_success(self, mock_run: MagicMock, version_manager: PostgresVersionManager):
        """Test successful version detection from Kubernetes pod."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "psql (PostgreSQL) 16.2"
        mock_run.return_value = mock_result

        version = version_manager.detect_version_from_kubernetes("postgres-pod")

        assert version == "16.2"
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "kubectl"
        assert cmd[1] == "exec"
        assert "-n" in cmd
        assert "default" in cmd
        assert "postgres-pod" in cmd

    @patch("subprocess.run")
    def test_detect_version_from_kubernetes_custom_namespace(
        self, mock_run: MagicMock, version_manager: PostgresVersionManager
    ):
        """Test version detection from custom Kubernetes namespace."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "psql (PostgreSQL) 15.5"
        mock_run.return_value = mock_result

        version = version_manager.detect_version_from_kubernetes("postgres-pod", namespace="production")

        assert version == "15.5"
        cmd = mock_run.call_args[0][0]
        assert "production" in cmd

    @patch("subprocess.run")
    def test_detect_version_from_kubernetes_failure(self, mock_run: MagicMock, version_manager: PostgresVersionManager):
        """Test version detection failure from Kubernetes pod."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        version = version_manager.detect_version_from_kubernetes("nonexistent-pod")

        assert version is None

    @patch("subprocess.run")
    def test_detect_version_from_kubernetes_timeout(self, mock_run: MagicMock, version_manager: PostgresVersionManager):
        """Test version detection timeout from Kubernetes pod."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="kubectl", timeout=10)

        version = version_manager.detect_version_from_kubernetes("slow-pod")

        assert version is None


class TestVersionInfo:
    """Test VersionInfo dataclass."""

    def test_version_info_from_string_full(self):
        """Test creating VersionInfo from full version string."""
        version_info = VersionInfo.from_string("15.3.1")

        assert version_info.major == 15
        assert version_info.minor == 3
        assert version_info.patch == 1
        assert version_info.full_version == "15.3.1"

    def test_version_info_from_string_major_minor(self):
        """Test creating VersionInfo from major.minor version."""
        version_info = VersionInfo.from_string("16.0")

        assert version_info.major == 16
        assert version_info.minor == 0
        assert version_info.patch == 0
        assert version_info.full_version == "16.0.0"

    def test_version_info_with_build_info(self):
        """Test creating VersionInfo with build information."""
        version_string = "15.3 (Ubuntu 15.3-1ubuntu1)"
        version_info = VersionInfo.from_string(version_string)

        assert version_info.major == 15
        assert version_info.minor == 3
        assert version_info.build_info == "Ubuntu 15.3-1ubuntu1"

    def test_version_info_invalid_string(self):
        """Test VersionInfo raises error for invalid version string."""
        with pytest.raises(ValueError, match="Cannot parse version"):
            VersionInfo.from_string("invalid-version")

    def test_to_major_version(self):
        """Test converting VersionInfo to major version enum."""
        version_info = VersionInfo.from_string("15.3")
        # Note: This test verifies the enum conversion exists
        # The actual enum value depends on implementation
        major_version = version_info.to_major_version()
        assert major_version is not None


class TestVersionDetectionIntegration:
    """Test version detection method integration."""

    @pytest.fixture
    def version_manager(self) -> PostgresVersionManager:
        """Create version manager instance."""
        return PostgresVersionManager()

    @patch("subprocess.run")
    def test_detect_version_with_connection_string(self, mock_run: MagicMock, version_manager: PostgresVersionManager):
        """Test detect_version method with connection string."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "PostgreSQL 15.3 on x86_64-pc-linux-gnu, compiled by gcc"
        mock_run.return_value = mock_result

        version_info = version_manager.detect_version("postgresql://localhost/db")

        assert version_info is not None
        assert version_info.major == 15
        assert version_info.minor == 3

    @patch("subprocess.run")
    def test_detect_version_local(self, mock_run: MagicMock, version_manager: PostgresVersionManager):
        """Test detect_version method for local installation."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "psql (PostgreSQL) 16.0"
        mock_run.return_value = mock_result

        version_info = version_manager.detect_version()

        assert version_info is not None
        assert version_info.major == 16
        assert version_info.minor == 0

    @patch("subprocess.run")
    def test_detect_version_failure_returns_none(self, mock_run: MagicMock, version_manager: PostgresVersionManager):
        """Test detect_version returns None on failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        version_info = version_manager.detect_version()

        assert version_info is None


class TestVersionCaching:
    """Test version detection caching behavior."""

    @pytest.fixture
    def version_manager(self) -> PostgresVersionManager:
        """Create version manager instance."""
        return PostgresVersionManager()

    def test_version_cache_initialization(self, version_manager: PostgresVersionManager):
        """Test version cache is initialized empty."""
        assert isinstance(version_manager._version_cache, dict)
        assert len(version_manager._version_cache) == 0


class TestRecommendVersion:
    """Test PostgreSQL version recommendation logic."""

    @pytest.fixture
    def version_manager(self) -> PostgresVersionManager:
        """Create version manager instance."""
        return PostgresVersionManager()

    def test_recommend_version_no_current(self, version_manager: PostgresVersionManager):
        """Test version recommendation with no current version."""
        recommended = version_manager.recommend_version()
        assert recommended in ["15", "16"]

    def test_recommend_version_already_recent(self, version_manager: PostgresVersionManager):
        """Test version recommendation when already on recent version."""
        current = VersionInfo.from_string("16.0")
        recommended = version_manager.recommend_version(current)
        assert recommended == "16"

    def test_recommend_version_upgrade_from_old(self, version_manager: PostgresVersionManager):
        """Test version recommendation for upgrade from old version."""
        current = VersionInfo.from_string("13.0")
        recommended = version_manager.recommend_version(current)
        assert recommended in ["14", "15"]
