"""Centralized PostgreSQL configuration for testing.

This module provides PostgreSQL configuration with automatic CI/local detection.
It handles different connection parameters for CI environments and local development.
"""

import os
from dataclasses import dataclass


@dataclass
class PostgresConfig:
    """PostgreSQL connection configuration for tests.

    Attributes:
        host: PostgreSQL server hostname
        port: PostgreSQL server port
        user: Database username
        password: Database password
        database: Database name
    """

    host: str
    port: int
    user: str
    password: str
    database: str

    @property
    def connection_string(self) -> str:
        """Build PostgreSQL connection string.

        Returns:
            Connection string in format: postgresql://user:password@host:port/database
        """
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


def get_postgres_config(database: str = "mycelium_test") -> PostgresConfig:
    """Get PostgreSQL config from environment with CI/local detection.

    This function automatically detects whether tests are running in CI or locally
    and provides appropriate default values for each environment:

    CI Environment (CI=true):
        - host: localhost
        - port: 5432
        - user: mycelium
        - password: mycelium_test

    Local Environment:
        - host: localhost
        - port: 5433 (avoids conflicts with local PostgreSQL installations)
        - user: postgres
        - password: changeme

    All values can be overridden via environment variables:
        - POSTGRES_HOST
        - POSTGRES_PORT
        - POSTGRES_USER
        - POSTGRES_PASSWORD
        - POSTGRES_DB

    Args:
        database: Database name (default: mycelium_test)

    Returns:
        PostgresConfig instance with connection parameters

    Example:
        >>> config = get_postgres_config("mycelium_test")
        >>> conn_str = config.connection_string
        >>> print(conn_str)
        postgresql://mycelium:mycelium_test@localhost:5432/mycelium_test
    """
    is_ci = os.getenv("CI", "false").lower() == "true"

    if is_ci:
        # CI environment - use GitHub Actions service container defaults
        default_host, default_port = "localhost", 5432
        default_user, default_password = "mycelium", "mycelium_test"
    else:
        # Local environment - use non-conflicting port and default credentials
        default_host, default_port = "localhost", 5433
        default_user, default_password = "postgres", "changeme"

    return PostgresConfig(
        host=os.getenv("POSTGRES_HOST", default_host),
        port=int(os.getenv("POSTGRES_PORT", str(default_port))),
        user=os.getenv("POSTGRES_USER", default_user),
        password=os.getenv("POSTGRES_PASSWORD", default_password),
        database=os.getenv("POSTGRES_DB", database),
    )
