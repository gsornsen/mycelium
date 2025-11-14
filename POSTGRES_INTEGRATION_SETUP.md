# PostgreSQL Integration Test Setup

This document describes the PostgreSQL integration test infrastructure implemented to support development and CI
workflows.

## Overview

The PostgreSQL integration test system provides:

1. **Automatic CI/local environment detection** - Different defaults for CI and local development
1. **Graceful skip behavior** - Tests skip locally when PostgreSQL unavailable
1. **CI enforcement** - Tests fail in CI if PostgreSQL is unavailable
1. **Centralized configuration** - Single source of truth for PostgreSQL connection settings
1. **Environment variable overrides** - Full control via environment variables

## Files Created

### Core Configuration

**`tests/config/postgres_config.py`**

- `PostgresConfig` dataclass with connection parameters
- `get_postgres_config()` function with CI/local detection
- Environment variable support for all settings

**`tests/fixtures/postgres_fixtures.py`**

- `is_postgres_available()` function with session-level caching
- `@postgres_available` pytest marker for automatic skipping
- CI/local behavior differences

### Example Test

**`tests/integration/test_postgres_example.py`**

- Demonstrates how to use the PostgreSQL test infrastructure
- Shows configuration defaults for CI and local environments
- Example integration tests with `@postgres_available` marker

## Configuration Defaults

### Local Environment (CI=false)

```python
host: "localhost"
port: 5433  # Non-conflicting port
user: "postgres"
password: "changeme"
```

### CI Environment (CI=true)

```python
host: "localhost"
port: 5432  # Standard port in GitHub Actions
user: "mycelium"
password: "mycelium_test"
```

## Environment Variables

All configuration values can be overridden:

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=mycelium
POSTGRES_PASSWORD=mycelium_test
POSTGRES_DB=mycelium_test
CI=true  # Forces CI mode
```

## Usage in Tests

### Basic Usage

```python
from tests.config.postgres_config import get_postgres_config
from tests.fixtures.postgres_fixtures import postgres_available
import pytest

@postgres_available
@pytest.mark.integration
@pytest.mark.postgres
class TestMyPostgreSQLFeature:
    """Integration tests requiring PostgreSQL."""

    def test_database_operation(self):
        config = get_postgres_config("mycelium_test")
        # Use config.connection_string or individual fields
        # Test will skip locally if PostgreSQL unavailable
        # Test will fail in CI if PostgreSQL unavailable
        pass
```

### Checking Availability Without Requirements

```python
from tests.fixtures.postgres_fixtures import is_postgres_available

def test_conditional_behavior():
    """Test that adapts based on PostgreSQL availability."""
    if is_postgres_available():
        # Run PostgreSQL-dependent code
        pass
    else:
        # Run alternative/mock code
        pass
```

## Running Tests

### Run All Integration Tests (Skip if PostgreSQL Unavailable)

```bash
pytest tests/integration/ -v
```

### Run Only PostgreSQL Tests

```bash
pytest tests/integration/ -v -m postgres
```

### Run in CI Mode (Fail if PostgreSQL Unavailable)

```bash
CI=true pytest tests/integration/ -v -m postgres
```

### Run Unit Tests Only (No PostgreSQL Required)

```bash
pytest tests/unit/ -v
```

## Pre-commit Hook

The pre-commit hook has been updated to ONLY run unit tests:

```yaml
- id: pytest-unit
  name: Unit tests only (fast, no external services)
  entry: bash -c
  language: system
  pass_filenames: false
  stages: [pre-push]
  args:
    - |
      uv run pytest tests/unit/ -v \
        -m "not integration and not benchmark and not slow" \
        --tb=short \
        --cov=plugins \
        --cov=mycelium_onboarding \
        --cov-report=term \
        --cov-fail-under=80
```

This ensures pre-push hooks complete quickly (\<30 seconds) without requiring PostgreSQL.

## CI Workflow

The CI workflow sets `CI=true` for integration tests:

```yaml
- name: Run integration tests
  env:
    CI: "true"
    POSTGRES_HOST: localhost
    POSTGRES_PORT: "5432"
    POSTGRES_USER: mycelium
    POSTGRES_PASSWORD: mycelium_test
    POSTGRES_DB: mycelium_test
```

## Pytest Markers

Added to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests (no external dependencies)",
    "integration: Integration tests (may require external services)",
    "postgres: Tests requiring PostgreSQL",
    "temporal: Tests requiring Temporal",
    "benchmark: marks tests as benchmarks",
    "slow: marks tests as slow",
    "asyncio: marks tests as async tests",
]
```

## Local Development Setup

### Option 1: Docker Compose (Recommended)

```bash
# Start PostgreSQL in docker-compose
docker-compose up -d postgres

# PostgreSQL will be available on port 5433
# Tests will automatically connect
pytest tests/integration/ -v
```

### Option 2: Custom PostgreSQL Instance

```bash
# Set custom connection parameters
export POSTGRES_HOST=my-postgres-host
export POSTGRES_PORT=5432
export POSTGRES_USER=myuser
export POSTGRES_PASSWORD=mypassword

# Run tests
pytest tests/integration/ -v
```

### Option 3: No PostgreSQL (Tests Skip)

```bash
# Simply run tests - they will skip gracefully
pytest tests/integration/ -v

# Output:
# tests/integration/test_postgres_example.py::TestPostgreSQLIntegration::test_postgres_connection SKIPPED
# Reason: PostgreSQL not available
```

## Benefits

1. **Faster Development** - Pre-push hooks complete in \<30 seconds
1. **No Setup Required** - Integration tests skip when PostgreSQL unavailable locally
1. **CI Safety** - Integration tests enforce PostgreSQL availability in CI
1. **Clear Feedback** - Skip messages explain why tests didn't run
1. **Easy Configuration** - Environment variables control all settings
1. **Consistent Behavior** - Same code works in CI and locally with appropriate defaults

## Troubleshooting

### Tests Skip Locally

This is expected behavior. To run integration tests locally:

1. Start PostgreSQL (e.g., via docker-compose)
1. Ensure it's accessible on port 5433 (or override with environment variables)
1. Re-run tests

### Tests Fail in CI

If integration tests fail in CI:

1. Check PostgreSQL service is configured in `.github/workflows/ci.yml`
1. Verify `CI=true` environment variable is set
1. Check connection parameters match service configuration

### Connection Refused

If tests report connection refused:

1. Verify PostgreSQL is running: `pg_isready -h localhost -p 5433`
1. Check port number matches configuration
1. Verify credentials are correct

## References

- [postgres-pro recommendations](/docs/agents/postgres-pro-recommendations.md)
- [Integration test guide](/docs/testing/integration-tests.md)
- [CI/CD documentation](/docs/ci-cd.md)
