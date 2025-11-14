"""PostgreSQL test fixtures with automatic availability detection.

This module provides pytest fixtures and decorators for PostgreSQL integration tests.
It includes automatic detection of PostgreSQL availability and graceful skipping
when the database is not available locally.

In CI environments, PostgreSQL is required and tests will fail if it's unavailable.
In local environments, tests will skip gracefully with a clear message.
"""

import os

import pytest

# Global cache for PostgreSQL availability check (per session)
_postgres_available: bool | None = None


def is_postgres_available() -> bool:
    """Check if PostgreSQL is available (cached per session).

    This function performs a quick connection test to PostgreSQL and caches
    the result for the duration of the test session. This avoids repeated
    connection attempts and provides fast skip decisions.

    In CI environments (CI=true), if PostgreSQL is unavailable, the test
    session fails immediately with a clear error message.

    In local environments, returns False when PostgreSQL is unavailable,
    allowing tests to skip gracefully.

    Returns:
        True if PostgreSQL is available, False otherwise

    Raises:
        pytest.fail: In CI environment when PostgreSQL is unavailable

    Example:
        >>> if is_postgres_available():
        ...     # Run PostgreSQL tests
        ...     pass
        ... else:
        ...     # Skip tests gracefully
        ...     pytest.skip("PostgreSQL not available")
    """
    global _postgres_available
    if _postgres_available is not None:
        return _postgres_available

    try:
        from tests.config.postgres_config import get_postgres_config

        # Try importing psycopg2 first
        try:
            import psycopg2
        except ImportError:
            # Fall back to psycopg (v3)
            try:
                import psycopg  # type: ignore
            except ImportError:
                # Neither psycopg2 nor psycopg available
                is_ci = os.getenv("CI", "false").lower() == "true"
                if is_ci:
                    pytest.fail("PostgreSQL driver (psycopg2 or psycopg) required in CI but not installed")
                _postgres_available = False
                return False

        config = get_postgres_config("postgres")

        # Try connecting with psycopg2
        try:
            import psycopg2

            conn = psycopg2.connect(
                host=config.host,
                port=config.port,
                user=config.user,
                password=config.password,
                database=config.database,
                connect_timeout=2,
            )
            conn.close()
        except (ImportError, Exception):
            # Try connecting with psycopg (v3)
            try:
                import psycopg  # type: ignore

                with psycopg.connect(
                    f"host={config.host} port={config.port} user={config.user} "
                    f"password={config.password} dbname={config.database} "
                    f"connect_timeout=2"
                ):
                    pass
            except Exception:
                # Connection failed with both drivers
                raise

        _postgres_available = True
        return True

    except Exception:
        is_ci = os.getenv("CI", "false").lower() == "true"
        if is_ci:
            pytest.fail("PostgreSQL required in CI but unavailable")
        _postgres_available = False
        return False


# Pytest marker for PostgreSQL tests
postgres_available = pytest.mark.skipif(not is_postgres_available(), reason="PostgreSQL not available")
"""Pytest marker to skip tests when PostgreSQL is unavailable.

Usage:
    @postgres_available
    @pytest.mark.integration
    def test_postgres_integration():
        # Test code here
        pass

This marker will:
- Skip the test locally if PostgreSQL is not available
- Fail the test in CI if PostgreSQL is not available
- Run the test if PostgreSQL is available in any environment
"""
