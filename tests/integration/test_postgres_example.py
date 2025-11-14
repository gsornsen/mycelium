"""Example integration test demonstrating PostgreSQL test infrastructure.

This test demonstrates how to use the new PostgreSQL test configuration
and fixtures for integration testing. It shows:

1. How to use the postgres_available marker to skip tests when PostgreSQL is unavailable
2. How to get PostgreSQL configuration using get_postgres_config()
3. How integration tests behave differently in CI vs local environments

Usage:
    # Run integration tests (will skip if PostgreSQL unavailable locally)
    pytest tests/integration/test_postgres_example.py -v

    # Run in CI mode (will fail if PostgreSQL unavailable)
    CI=true pytest tests/integration/test_postgres_example.py -v

Author: @python-pro
Date: 2025-11-13
"""

import os

import pytest

from tests.config.postgres_config import get_postgres_config
from tests.fixtures.postgres_fixtures import is_postgres_available, postgres_available


class TestPostgreSQLAvailability:
    """Test PostgreSQL availability detection."""

    def test_postgres_config_defaults_local(self) -> None:
        """Test that postgres config uses correct defaults for local environment."""
        # Clear CI env var to simulate local environment
        original_ci = os.environ.get("CI")
        try:
            if "CI" in os.environ:
                del os.environ["CI"]

            config = get_postgres_config("test_db")

            # Local defaults
            assert config.host == "localhost"
            assert config.port == 5433  # Non-conflicting port for local
            assert config.user == "postgres"
            assert config.password == "changeme"
            assert config.database == "test_db"

        finally:
            if original_ci is not None:
                os.environ["CI"] = original_ci
            elif "CI" in os.environ:
                del os.environ["CI"]

    def test_postgres_config_defaults_ci(self) -> None:
        """Test that postgres config uses correct defaults for CI environment."""
        # Set CI env var to simulate CI environment
        original_ci = os.environ.get("CI")
        try:
            os.environ["CI"] = "true"

            config = get_postgres_config("test_db")

            # CI defaults
            assert config.host == "localhost"
            assert config.port == 5432  # Standard port in CI
            assert config.user == "mycelium"
            assert config.password == "mycelium_test"
            assert config.database == "test_db"

        finally:
            if original_ci is not None:
                os.environ["CI"] = original_ci
            elif "CI" in os.environ:
                del os.environ["CI"]

    def test_postgres_config_env_override(self) -> None:
        """Test that postgres config can be overridden via environment variables."""
        original_values = {
            "POSTGRES_HOST": os.environ.get("POSTGRES_HOST"),
            "POSTGRES_PORT": os.environ.get("POSTGRES_PORT"),
            "POSTGRES_USER": os.environ.get("POSTGRES_USER"),
            "POSTGRES_PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
            "POSTGRES_DB": os.environ.get("POSTGRES_DB"),
        }

        try:
            # Override with custom values
            os.environ["POSTGRES_HOST"] = "custom-host"
            os.environ["POSTGRES_PORT"] = "9999"
            os.environ["POSTGRES_USER"] = "custom-user"
            os.environ["POSTGRES_PASSWORD"] = "custom-pass"
            os.environ["POSTGRES_DB"] = "custom-db"

            config = get_postgres_config()

            assert config.host == "custom-host"
            assert config.port == 9999
            assert config.user == "custom-user"
            assert config.password == "custom-pass"
            assert config.database == "custom-db"

        finally:
            # Restore original values
            for key, value in original_values.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_connection_string_format(self) -> None:
        """Test that connection string is properly formatted."""
        config = get_postgres_config("mycelium_test")
        conn_str = config.connection_string

        assert conn_str.startswith("postgresql://")
        assert config.user in conn_str
        assert config.password in conn_str
        assert config.host in conn_str
        assert str(config.port) in conn_str
        assert config.database in conn_str


@postgres_available
@pytest.mark.integration
@pytest.mark.postgres
class TestPostgreSQLIntegration:
    """Example integration tests that require PostgreSQL.

    These tests will:
    - Skip locally if PostgreSQL is not available
    - Fail in CI if PostgreSQL is not available
    - Run normally when PostgreSQL is available
    """

    def test_postgres_connection(self) -> None:
        """Test that we can connect to PostgreSQL.

        This is a basic smoke test that verifies PostgreSQL is accessible.
        """
        config = get_postgres_config("postgres")

        # Try importing psycopg2 first
        try:
            import psycopg2

            conn = psycopg2.connect(
                host=config.host,
                port=config.port,
                user=config.user,
                password=config.password,
                database=config.database,
                connect_timeout=5,
            )
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            assert version is not None
            assert "PostgreSQL" in version[0]
            cursor.close()
            conn.close()

        except ImportError:
            # Fall back to psycopg (v3)
            try:
                import psycopg  # type: ignore

                with (
                    psycopg.connect(
                        f"host={config.host} port={config.port} user={config.user} "
                        f"password={config.password} dbname={config.database} "
                        f"connect_timeout=5"
                    ) as conn,
                    conn.cursor() as cursor,
                ):
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()
                    assert version is not None
                    assert "PostgreSQL" in version[0]

            except ImportError:
                pytest.skip("Neither psycopg2 nor psycopg available")

    def test_postgres_availability_check(self) -> None:
        """Test that is_postgres_available correctly detects PostgreSQL."""
        # If we got here, the @postgres_available decorator passed
        # which means PostgreSQL should be available
        assert is_postgres_available() is True


class TestSkipBehavior:
    """Test that demonstrates skip behavior without PostgreSQL requirement."""

    def test_always_runs(self) -> None:
        """This test always runs regardless of PostgreSQL availability."""
        assert True

    def test_can_check_availability_without_requiring_it(self) -> None:
        """Test that we can check PostgreSQL availability without requiring it."""
        # This test runs even if PostgreSQL is not available
        available = is_postgres_available()
        # Just checking the availability doesn't require PostgreSQL to be present
        assert isinstance(available, bool)
