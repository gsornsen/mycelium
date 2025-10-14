# M09: Testing Suite

## Overview

**Duration**: 2 days
**Dependencies**: M06 (Coordination Testing)
**Parallel Work**: Runs concurrently with M07 (Configuration Management) and M08 (Documentation)
**Blocks**: M10 (Polish & Release)

**Lead Agent**: test-automator
**Support Agents**: python-pro, devops-engineer, qa-expert

## Why This Milestone

While M06 established functional coordination testing, this milestone creates a comprehensive test infrastructure covering all components of the onboarding system. This includes unit tests for individual modules, integration tests for component interactions, CI/CD pipeline setup, and automated coverage reporting. A robust test suite ensures code quality, catches regressions early, and provides confidence for future development.

## Requirements

### Functional Requirements (FR)

- **FR-9.1**: Unit test suite achieving ≥80% code coverage across all modules
- **FR-9.2**: Integration tests validating component interactions (detection → config → generation)
- **FR-9.3**: CI/CD pipeline automating test execution on pull requests and main branch
- **FR-9.4**: Code coverage reporting with HTML reports and PR comments
- **FR-9.5**: Test data management with fixtures and factories for reproducible tests

### Technical Requirements (TR)

- **TR-9.1**: pytest framework with plugins (pytest-asyncio, pytest-cov, pytest-mock)
- **TR-9.2**: GitHub Actions workflow for automated testing
- **TR-9.3**: Test organization following pytest conventions (tests/ directory structure)
- **TR-9.4**: Mock strategies for external dependencies (MCP servers, Docker, system calls)
- **TR-9.5**: Parameterized tests for comprehensive edge case coverage

### Integration Requirements (IR)

- **IR-9.1**: Tests validate integration with M02 (ConfigManager), M03 (detection), M04 (wizard), M05 (generators)
- **IR-9.2**: CI/CD integrates with GitHub repository (actions, pull request checks)
- **IR-9.3**: Coverage reports integrate with GitHub PR comments via bot

### Compliance Requirements (CR)

- **CR-9.1**: All public APIs must have corresponding unit tests
- **CR-9.2**: All integration points must have integration tests
- **CR-9.3**: Test code follows same quality standards as production code (type hints, docstrings)

---

## Tasks

### Task 9.1: Unit Test Suite for Core Modules

**Effort**: 8 hours
**Agent**: test-automator, python-pro

Create comprehensive unit tests for all core modules with ≥80% coverage target.

**Test Organization**:

```
tests/
├── unit/
│   ├── __init__.py
│   ├── test_config_manager.py      # M02 tests
│   ├── test_detection.py           # M03 tests
│   ├── test_wizard.py              # M04 tests
│   ├── test_generators.py          # M05 tests
│   └── test_orchestrator.py        # M06 tests
├── integration/
│   ├── __init__.py
│   ├── test_full_flow.py
│   └── test_component_integration.py
├── fixtures/
│   ├── __init__.py
│   ├── config_fixtures.py
│   ├── detection_fixtures.py
│   └── mcp_fixtures.py
└── conftest.py                      # Shared fixtures
```

**Example: ConfigManager Unit Tests**

```python
# tests/unit/test_config_manager.py
"""Unit tests for ConfigManager."""

import pytest
from pathlib import Path
from pydantic import ValidationError

from mycelium.config import ConfigManager, MyceliumConfig, ServicesConfig, RedisConfig


class TestConfigManagerLoad:
    """Tests for ConfigManager.load()."""

    def test_load_from_project_local(self, tmp_path, sample_config):
        """Test loading configuration from project-local path."""
        # Arrange
        project_config = tmp_path / ".mycelium" / "config.yaml"
        project_config.parent.mkdir(parents=True)
        ConfigManager.save(sample_config, project_local=True, config_dir=tmp_path)

        # Act
        loaded = ConfigManager.load(prefer_project=True, project_dir=tmp_path)

        # Assert
        assert loaded.services.redis.enabled == sample_config.services.redis.enabled
        assert loaded.services.redis.port == sample_config.services.redis.port

    def test_load_from_user_global(self, tmp_path, sample_config):
        """Test loading configuration from user global path (~/.config/mycelium)."""
        # Arrange
        user_config = tmp_path / "config.yaml"
        ConfigManager.save(sample_config, project_local=False, config_dir=tmp_path)

        # Act
        loaded = ConfigManager.load(prefer_project=False, user_config_dir=tmp_path)

        # Assert
        assert loaded.services.redis.enabled == sample_config.services.redis.enabled

    def test_load_creates_default_if_missing(self, tmp_path):
        """Test that load creates default config if no config exists."""
        # Act
        loaded = ConfigManager.load(
            prefer_project=False,
            user_config_dir=tmp_path / "nonexistent",
            create_default=True
        )

        # Assert
        assert isinstance(loaded, MyceliumConfig)
        assert loaded.services.redis.enabled  # Default has Redis enabled

    def test_load_raises_if_missing_and_no_default(self, tmp_path):
        """Test that load raises error if config missing and no default creation."""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            ConfigManager.load(
                prefer_project=False,
                user_config_dir=tmp_path / "nonexistent",
                create_default=False
            )


class TestConfigManagerSave:
    """Tests for ConfigManager.save()."""

    def test_save_to_project_local(self, tmp_path, sample_config):
        """Test saving configuration to project-local directory."""
        # Act
        config_path = ConfigManager.save(
            sample_config,
            project_local=True,
            config_dir=tmp_path
        )

        # Assert
        assert config_path.exists()
        assert config_path.parent.name == ".mycelium"
        assert config_path.name == "config.yaml"

    def test_save_creates_directory_if_missing(self, tmp_path, sample_config):
        """Test that save creates config directory if it doesn't exist."""
        # Arrange
        config_dir = tmp_path / "new_dir"
        assert not config_dir.exists()

        # Act
        config_path = ConfigManager.save(
            sample_config,
            project_local=True,
            config_dir=config_dir
        )

        # Assert
        assert config_path.exists()
        assert config_path.parent.exists()

    def test_save_overwrites_existing_config(self, tmp_path, sample_config):
        """Test that save overwrites existing configuration."""
        # Arrange
        config_path = ConfigManager.save(sample_config, project_local=True, config_dir=tmp_path)
        original_content = config_path.read_text()

        # Modify config
        sample_config.services.redis.port = 9999

        # Act
        ConfigManager.save(sample_config, project_local=True, config_dir=tmp_path)

        # Assert
        new_content = config_path.read_text()
        assert new_content != original_content
        assert "9999" in new_content


class TestConfigManagerValidation:
    """Tests for configuration validation."""

    def test_validate_rejects_invalid_port(self):
        """Test that validation rejects ports outside valid range."""
        # Act & Assert
        with pytest.raises(ValidationError):
            MyceliumConfig(
                services=ServicesConfig(
                    redis=RedisConfig(enabled=True, port=70000)  # Invalid port
                )
            )

    def test_validate_rejects_negative_memory(self):
        """Test that validation rejects negative memory values."""
        # Act & Assert
        with pytest.raises(ValidationError):
            MyceliumConfig(
                services=ServicesConfig(
                    redis=RedisConfig(enabled=True, max_memory=-100)  # Invalid
                )
            )

    def test_validate_accepts_valid_config(self, sample_config):
        """Test that validation accepts valid configuration."""
        # Act & Assert (no exception raised)
        assert sample_config.services.redis.enabled
        assert 1024 <= sample_config.services.redis.port <= 65535


@pytest.fixture
def sample_config() -> MyceliumConfig:
    """Provide sample valid configuration for testing."""
    return MyceliumConfig(
        services=ServicesConfig(
            redis=RedisConfig(
                enabled=True,
                port=6379,
                max_memory=512,
                persistence=True
            )
        )
    )
```

**Example: Detection Module Tests**

```python
# tests/unit/test_detection.py
"""Unit tests for infrastructure detection."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from mycelium.detection import (
    InfraDetector,
    DetectionResults,
    ServiceStatus,
    RedisDetection,
)


class TestRedisDetection:
    """Tests for Redis service detection."""

    @patch('subprocess.run')
    def test_detect_docker_redis(self, mock_run):
        """Test detection of Redis running in Docker."""
        # Arrange
        mock_run.return_value = Mock(
            returncode=0,
            stdout="mycelium-redis\n6379/tcp\nrunning"
        )

        detector = InfraDetector()

        # Act
        result = detector.detect_redis()

        # Assert
        assert result.available
        assert result.method == "docker"
        assert result.port == 6379
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_detect_native_redis(self, mock_run):
        """Test detection of Redis running natively (systemd)."""
        # Arrange
        mock_run.side_effect = [
            Mock(returncode=1, stdout=""),  # Docker check fails
            Mock(returncode=0, stdout="active")  # Systemd check succeeds
        ]

        detector = InfraDetector()

        # Act
        result = detector.detect_redis()

        # Assert
        assert result.available
        assert result.method == "systemd"
        assert mock_run.call_count == 2

    @patch('subprocess.run')
    def test_detect_redis_not_found(self, mock_run):
        """Test detection when Redis is not running."""
        # Arrange
        mock_run.return_value = Mock(returncode=1, stdout="")

        detector = InfraDetector()

        # Act
        result = detector.detect_redis()

        # Assert
        assert not result.available
        assert result.method is None

    @patch('socket.socket')
    def test_detect_redis_port_in_use(self, mock_socket):
        """Test detection of Redis by checking if port 6379 is in use."""
        # Arrange
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.connect_ex.return_value = 0  # Port is open

        detector = InfraDetector()

        # Act
        result = detector._check_redis_port()

        # Assert
        assert result
        mock_sock.connect_ex.assert_called_with(('localhost', 6379))


class TestInfraDetectorFullScan:
    """Tests for complete infrastructure scanning."""

    @patch.object(InfraDetector, 'detect_redis')
    @patch.object(InfraDetector, 'detect_postgres')
    @patch.object(InfraDetector, 'detect_docker')
    def test_scan_all_services(self, mock_docker, mock_postgres, mock_redis):
        """Test scanning all services returns complete results."""
        # Arrange
        mock_redis.return_value = RedisDetection(available=True, method="docker")
        mock_postgres.return_value = Mock(available=False)
        mock_docker.return_value = Mock(available=True, version="24.0.0")

        detector = InfraDetector()

        # Act
        results = detector.scan_all()

        # Assert
        assert isinstance(results, DetectionResults)
        assert results.redis.available
        assert not results.postgres.available
        assert results.docker.available
        mock_redis.assert_called_once()
        mock_postgres.assert_called_once()
        mock_docker.assert_called_once()
```

**Coverage Target**: ≥80% for all modules in `mycelium/` directory.

---

### Task 9.2: Integration Tests for Component Workflows

**Effort**: 6 hours
**Agent**: test-automator, python-pro

Create integration tests validating end-to-end workflows across multiple components.

**Example: Full Onboarding Flow Integration Test**

```python
# tests/integration/test_full_flow.py
"""Integration tests for complete onboarding workflow."""

import pytest
from pathlib import Path
from unittest.mock import patch, Mock

from mycelium.detection import InfraDetector
from mycelium.config import ConfigManager, MyceliumConfig
from mycelium.wizard import OnboardingWizard
from mycelium.generators import DockerComposeGenerator, JustfileGenerator


@pytest.mark.integration
class TestFullOnboardingFlow:
    """Tests for complete onboarding workflow: detect → wizard → config → generate."""

    @pytest.mark.asyncio
    async def test_docker_deployment_flow(self, tmp_path, monkeypatch):
        """Test complete flow for Docker deployment method."""
        # Arrange: Mock detection results
        detection_results = Mock(
            redis=Mock(available=True, method="docker"),
            postgres=Mock(available=True, method="docker"),
            docker=Mock(available=True, version="24.0.0"),
        )

        with patch.object(InfraDetector, 'scan_all', return_value=detection_results):
            # Arrange: Mock wizard user selections
            mock_selections = {
                'services': {'redis', 'postgres', 'taskqueue'},
                'deployment_method': 'docker-compose',
                'project_local': True,
            }

            with patch('inquirer.checkbox', side_effect=[
                mock_selections['services'],  # Service selection
            ]):
                with patch('inquirer.select', return_value=mock_selections['deployment_method']):
                    with patch('inquirer.confirm', return_value=mock_selections['project_local']):
                        # Act: Run wizard
                        wizard = OnboardingWizard()
                        config = await wizard.run(config_dir=tmp_path)

        # Assert: Configuration created correctly
        assert isinstance(config, MyceliumConfig)
        assert config.services.redis.enabled
        assert config.services.postgres.enabled
        assert config.services.taskqueue.enabled
        assert config.deployment.method == "docker-compose"

        # Act: Save configuration
        config_path = ConfigManager.save(config, project_local=True, config_dir=tmp_path)

        # Assert: Configuration file exists
        assert config_path.exists()
        assert config_path.name == "config.yaml"

        # Act: Generate deployment files
        docker_gen = DockerComposeGenerator()
        docker_compose = docker_gen.generate(config)

        justfile_gen = JustfileGenerator()
        justfile = justfile_gen.generate(config)

        # Assert: Deployment files generated
        assert "services:" in docker_compose
        assert "redis:" in docker_compose
        assert "postgres:" in docker_compose
        assert "up:" in justfile
        assert "down:" in justfile

    @pytest.mark.asyncio
    async def test_native_deployment_flow(self, tmp_path, monkeypatch):
        """Test complete flow for native (Justfile) deployment method."""
        # Arrange: Mock detection results (native services)
        detection_results = Mock(
            redis=Mock(available=True, method="systemd"),
            postgres=Mock(available=True, method="systemd"),
            docker=Mock(available=False),
        )

        with patch.object(InfraDetector, 'scan_all', return_value=detection_results):
            # Arrange: Mock wizard selections
            mock_selections = {
                'services': {'redis', 'taskqueue'},
                'deployment_method': 'justfile',
                'project_local': False,
            }

            with patch('inquirer.checkbox', return_value=mock_selections['services']):
                with patch('inquirer.select', return_value=mock_selections['deployment_method']):
                    with patch('inquirer.confirm', return_value=mock_selections['project_local']):
                        # Act: Run wizard
                        wizard = OnboardingWizard()
                        config = await wizard.run(config_dir=tmp_path)

        # Assert: Configuration created for native deployment
        assert config.deployment.method == "justfile"
        assert config.services.redis.enabled
        assert config.services.taskqueue.enabled

        # Act: Generate Justfile
        justfile_gen = JustfileGenerator()
        justfile = justfile_gen.generate(config)

        # Assert: Justfile contains native service management
        assert "systemctl" in justfile
        assert "redis-cli" in justfile


@pytest.mark.integration
class TestComponentIntegration:
    """Tests for integration between specific component pairs."""

    def test_detection_to_config_mapping(self):
        """Test that detection results correctly map to configuration."""
        # Arrange
        detection_results = Mock(
            redis=Mock(available=True, method="docker", port=6379),
            postgres=Mock(available=True, method="docker", port=5432),
        )

        # Act
        config = MyceliumConfig.from_detection(detection_results)

        # Assert
        assert config.services.redis.enabled
        assert config.services.redis.port == 6379
        assert config.services.postgres.enabled
        assert config.services.postgres.port == 5432

    def test_config_to_generator_input(self, sample_config):
        """Test that configuration provides valid input for generators."""
        # Act
        docker_gen = DockerComposeGenerator()
        output = docker_gen.generate(sample_config)

        # Assert: Valid YAML structure
        import yaml
        parsed = yaml.safe_load(output)
        assert 'services' in parsed
        assert 'redis' in parsed['services']
        assert parsed['services']['redis']['image'].startswith('redis:')
```

**Integration Test Categories**:

1. Full workflow tests (detection → wizard → config → generation)
2. Component pair integration (detection ↔ config, config ↔ generators)
3. MCP coordination integration (using M06 patterns)
4. CLI command integration (slash commands end-to-end)

---

### Task 9.3: CI/CD Pipeline with GitHub Actions

**Effort**: 4 hours
**Agent**: devops-engineer, test-automator

Create GitHub Actions workflow for automated testing on every pull request and main branch push.

**Workflow Configuration**:

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    name: Test on Python ${{ matrix.python-version }}
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install uv
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          echo "$HOME/.cargo/bin" >> $GITHUB_PATH

      - name: Install dependencies
        run: |
          uv venv
          source .venv/bin/activate
          uv sync --all-extras

      - name: Run linter (ruff)
        run: |
          source .venv/bin/activate
          uv run ruff check .

      - name: Run type checker (mypy)
        run: |
          source .venv/bin/activate
          uv run mypy mycelium/

      - name: Run unit tests with coverage
        run: |
          source .venv/bin/activate
          uv run pytest tests/unit/ \
            --cov=mycelium \
            --cov-report=xml \
            --cov-report=html \
            --cov-report=term-missing \
            --junitxml=test-results.xml

      - name: Run integration tests
        run: |
          source .venv/bin/activate
          uv run pytest tests/integration/ \
            --junitxml=integration-results.xml
        env:
          USE_MOCK_MCP: "1"  # Use mocks for MCP in CI

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results-${{ matrix.python-version }}
          path: |
            test-results.xml
            integration-results.xml
            htmlcov/

  lint:
    name: Code Quality Checks
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install uv
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          echo "$HOME/.cargo/bin" >> $GITHUB_PATH

      - name: Install dependencies
        run: |
          uv venv
          source .venv/bin/activate
          uv sync --all-extras

      - name: Check code formatting (ruff format)
        run: |
          source .venv/bin/activate
          uv run ruff format --check .

      - name: Run security checks (bandit)
        run: |
          source .venv/bin/activate
          uv run bandit -r mycelium/ -c pyproject.toml

  coverage-report:
    name: Coverage Report Comment
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'pull_request'

    steps:
      - name: Download coverage artifact
        uses: actions/download-artifact@v4
        with:
          name: test-results-3.11

      - name: Comment coverage on PR
        uses: py-cov-action/python-coverage-comment-action@v3
        with:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          MINIMUM_GREEN: 80
          MINIMUM_ORANGE: 70
```

**Required Secrets/Variables**:

- `CODECOV_TOKEN`: Token for Codecov integration (optional)
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions

**Branch Protection Rules**:

```yaml
# Configure in GitHub repository settings
branch_protection:
  main:
    required_status_checks:
      strict: true
      contexts:
        - "Test on Python 3.11"
        - "Test on Python 3.12"
        - "Code Quality Checks"
    required_pull_request_reviews:
      required_approving_review_count: 1
    enforce_admins: false
```

---

### Task 9.4: Test Configuration and Coverage Reporting

**Effort**: 3 hours
**Agent**: test-automator, python-pro

Configure pytest with plugins and set up comprehensive coverage reporting.

**pytest Configuration**:

```toml
# pyproject.toml (add to existing file)
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-ra",                    # Show summary of all test outcomes
    "--strict-markers",       # Error on undefined markers
    "--strict-config",        # Error on config issues
    "--showlocals",           # Show local variables in tracebacks
    "-v",                     # Verbose output
]

markers = [
    "unit: Unit tests for individual components",
    "integration: Integration tests for component interactions",
    "slow: Tests that take >1 second to run",
    "requires_docker: Tests requiring Docker daemon",
    "requires_redis: Tests requiring Redis connection",
]

asyncio_mode = "auto"

[tool.coverage.run]
source = ["mycelium"]
omit = [
    "*/tests/*",
    "*/__pycache__/*",
    "*/venv/*",
    "*/.venv/*",
]
branch = true

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]

[tool.coverage.html]
directory = "htmlcov"

[tool.coverage.xml]
output = "coverage.xml"
```

**Shared Test Fixtures**:

```python
# tests/conftest.py
"""Shared pytest fixtures for all tests."""

import pytest
from pathlib import Path
from typing import Generator
from unittest.mock import Mock

from mycelium.config import MyceliumConfig, ServicesConfig, RedisConfig, PostgresConfig


@pytest.fixture
def tmp_project_dir(tmp_path: Path) -> Path:
    """Provide temporary project directory with standard structure."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create standard directories
    (project_dir / ".mycelium").mkdir()
    (project_dir / "deployment").mkdir()

    return project_dir


@pytest.fixture
def sample_config() -> MyceliumConfig:
    """Provide sample valid configuration for testing."""
    return MyceliumConfig(
        services=ServicesConfig(
            redis=RedisConfig(
                enabled=True,
                port=6379,
                max_memory=512,
                persistence=True
            ),
            postgres=PostgresConfig(
                enabled=True,
                port=5432,
                database="mycelium",
                max_connections=100
            )
        )
    )


@pytest.fixture
def mock_detection_results() -> Mock:
    """Provide mock detection results."""
    return Mock(
        redis=Mock(available=True, method="docker", port=6379),
        postgres=Mock(available=True, method="docker", port=5432),
        docker=Mock(available=True, version="24.0.0"),
        taskqueue=Mock(available=False),
        temporal=Mock(available=False),
    )


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    # Clear any cached singleton state
    from mycelium.config import ConfigManager
    ConfigManager._instance = None

    yield

    # Cleanup after test
    ConfigManager._instance = None


@pytest.fixture
def mock_docker_client() -> Generator[Mock, None, None]:
    """Provide mocked Docker client."""
    mock_client = Mock()
    mock_client.containers.list.return_value = []
    mock_client.images.list.return_value = []

    yield mock_client

    mock_client.close()


# Mark slow tests
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
```

**Coverage Report Script**:

```python
# scripts/coverage_report.py
"""Generate and display coverage report with color coding."""

import subprocess
import sys
from pathlib import Path


def run_coverage() -> tuple[float, str]:
    """Run pytest with coverage and return coverage percentage."""
    result = subprocess.run(
        [
            "pytest",
            "tests/",
            "--cov=mycelium",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml",
        ],
        capture_output=True,
        text=True
    )

    # Parse coverage percentage from output
    for line in result.stdout.split('\n'):
        if 'TOTAL' in line:
            parts = line.split()
            coverage_pct = float(parts[-1].rstrip('%'))
            return coverage_pct, result.stdout

    return 0.0, result.stdout


def main():
    """Main entry point."""
    print("Running test suite with coverage analysis...\n")

    coverage_pct, output = run_coverage()

    print(output)
    print("\n" + "=" * 60)

    if coverage_pct >= 80:
        print(f"✓ Coverage: {coverage_pct:.2f}% (Target: ≥80%) - PASS")
        sys.exit(0)
    elif coverage_pct >= 70:
        print(f"⚠ Coverage: {coverage_pct:.2f}% (Target: ≥80%) - WARNING")
        sys.exit(0)
    else:
        print(f"✗ Coverage: {coverage_pct:.2f}% (Target: ≥80%) - FAIL")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

### Task 9.5: Mock Strategies and Test Data Management

**Effort**: 3 hours
**Agent**: test-automator, python-pro

Implement comprehensive mock strategies for external dependencies and test data factories.

**Mock Fixtures for MCP Servers**:

```python
# tests/fixtures/mcp_fixtures.py
"""Mock fixtures for MCP server interactions."""

import pytest
from unittest.mock import AsyncMock, Mock
from typing import AsyncGenerator


@pytest.fixture
async def mock_redis_mcp() -> AsyncGenerator[AsyncMock, None]:
    """Provide mocked Redis MCP client."""
    mock_client = AsyncMock()

    # Mock common Redis operations
    mock_client.hset = AsyncMock(return_value=1)
    mock_client.hget = AsyncMock(return_value=b"mocked_value")
    mock_client.hdel = AsyncMock(return_value=1)
    mock_client.hgetall = AsyncMock(return_value={b"key": b"value"})
    mock_client.publish = AsyncMock(return_value=1)
    mock_client.subscribe = AsyncMock()

    yield mock_client

    # Cleanup
    await mock_client.close()


@pytest.fixture
async def mock_taskqueue_mcp() -> AsyncGenerator[AsyncMock, None]:
    """Provide mocked TaskQueue MCP client."""
    mock_client = AsyncMock()

    # Mock task queue operations
    mock_client.create_project = AsyncMock(return_value={"project_id": "proj-1"})
    mock_client.add_tasks_to_project = AsyncMock(return_value={"task_ids": ["task-1"]})
    mock_client.get_next_task = AsyncMock(return_value={
        "task_id": "task-1",
        "title": "Test Task",
        "status": "not started"
    })
    mock_client.update_task = AsyncMock(return_value={"status": "completed"})

    yield mock_client


@pytest.fixture
def mock_subprocess_run(monkeypatch):
    """Provide mocked subprocess.run for system command tests."""
    mock_run = Mock()
    mock_run.return_value = Mock(
        returncode=0,
        stdout="mocked output",
        stderr=""
    )

    monkeypatch.setattr("subprocess.run", mock_run)

    return mock_run
```

**Test Data Factories**:

```python
# tests/fixtures/config_fixtures.py
"""Factory functions for creating test data."""

from dataclasses import dataclass, field
from typing import Optional
import factory
from factory import Factory, SubFactory, Faker

from mycelium.config import (
    MyceliumConfig,
    ServicesConfig,
    RedisConfig,
    PostgresConfig,
    DeploymentConfig,
)


class RedisConfigFactory(Factory):
    """Factory for generating RedisConfig instances."""

    class Meta:
        model = RedisConfig

    enabled = True
    port = 6379
    max_memory = 512
    persistence = True


class PostgresConfigFactory(Factory):
    """Factory for generating PostgresConfig instances."""

    class Meta:
        model = PostgresConfig

    enabled = True
    port = 5432
    database = "mycelium"
    max_connections = 100


class ServicesConfigFactory(Factory):
    """Factory for generating ServicesConfig instances."""

    class Meta:
        model = ServicesConfig

    redis = SubFactory(RedisConfigFactory)
    postgres = SubFactory(PostgresConfigFactory)


class DeploymentConfigFactory(Factory):
    """Factory for generating DeploymentConfig instances."""

    class Meta:
        model = DeploymentConfig

    method = "docker-compose"


class MyceliumConfigFactory(Factory):
    """Factory for generating complete MyceliumConfig instances."""

    class Meta:
        model = MyceliumConfig

    services = SubFactory(ServicesConfigFactory)
    deployment = SubFactory(DeploymentConfigFactory)


# Convenience functions
def create_minimal_config() -> MyceliumConfig:
    """Create minimal valid configuration (Redis only)."""
    return MyceliumConfigFactory.build(
        services__postgres__enabled=False,
        services__taskqueue__enabled=False,
    )


def create_full_config() -> MyceliumConfig:
    """Create configuration with all services enabled."""
    return MyceliumConfigFactory.build()


def create_docker_config() -> MyceliumConfig:
    """Create configuration for Docker deployment."""
    return MyceliumConfigFactory.build(
        deployment__method="docker-compose"
    )


def create_justfile_config() -> MyceliumConfig:
    """Create configuration for Justfile deployment."""
    return MyceliumConfigFactory.build(
        deployment__method="justfile"
    )
```

**Parametrized Tests Example**:

```python
# tests/unit/test_config_validation.py
"""Parametrized tests for configuration validation."""

import pytest
from pydantic import ValidationError

from mycelium.config import RedisConfig


@pytest.mark.parametrize("port,should_pass", [
    (1024, True),      # Valid: lower bound
    (6379, True),      # Valid: standard
    (65535, True),     # Valid: upper bound
    (0, False),        # Invalid: too low
    (70000, False),    # Invalid: too high
    (-1, False),       # Invalid: negative
])
def test_redis_port_validation(port: int, should_pass: bool):
    """Test Redis port validation with various inputs."""
    if should_pass:
        config = RedisConfig(enabled=True, port=port)
        assert config.port == port
    else:
        with pytest.raises(ValidationError):
            RedisConfig(enabled=True, port=port)


@pytest.mark.parametrize("max_memory,should_pass", [
    (128, True),       # Valid: minimum
    (512, True),       # Valid: standard
    (4096, True),      # Valid: large
    (0, False),        # Invalid: zero
    (-100, False),     # Invalid: negative
])
def test_redis_memory_validation(max_memory: int, should_pass: bool):
    """Test Redis max_memory validation with various inputs."""
    if should_pass:
        config = RedisConfig(enabled=True, max_memory=max_memory)
        assert config.max_memory == max_memory
    else:
        with pytest.raises(ValidationError):
            RedisConfig(enabled=True, max_memory=max_memory)
```

---

## Exit Criteria

- [ ] Unit test suite achieves ≥80% code coverage across all modules
- [ ] All unit tests pass without failures or errors
- [ ] Integration tests validate complete workflows (detection → config → generation)
- [ ] CI/CD pipeline executes successfully on pull requests and main branch
- [ ] Coverage reports generated and posted to pull requests
- [ ] Mock strategies implemented for all external dependencies
- [ ] Test data factories created for common test scenarios
- [ ] Test documentation includes examples and best practices
- [ ] All tests follow naming conventions and organization standards
- [ ] pytest runs cleanly with no warnings or deprecations

## Deliverables

1. **Unit Test Suite** (tests/unit/)
   - test_config_manager.py (M02 tests)
   - test_detection.py (M03 tests)
   - test_wizard.py (M04 tests)
   - test_generators.py (M05 tests)
   - test_orchestrator.py (M06 tests)

2. **Integration Test Suite** (tests/integration/)
   - test_full_flow.py (end-to-end workflows)
   - test_component_integration.py (component pairs)

3. **CI/CD Pipeline** (.github/workflows/)
   - test.yml (main test workflow)
   - coverage-comment.yml (PR coverage reporting)

4. **Test Configuration**
   - pytest configuration in pyproject.toml
   - conftest.py with shared fixtures
   - Coverage reporting configuration

5. **Test Utilities** (tests/fixtures/)
   - mcp_fixtures.py (MCP mocks)
   - config_fixtures.py (test data factories)
   - detection_fixtures.py (detection result mocks)

6. **Test Documentation**
   - Testing guide in docs/
   - CI/CD documentation
   - Mock strategy documentation

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Coverage target not met | Medium | High | Iterative testing, focus on critical paths first |
| CI/CD pipeline failures | Low | Medium | Thorough local testing before push, mock external dependencies |
| Flaky tests due to timing | Medium | Medium | Use deterministic fixtures, avoid real I/O where possible |
| Mock drift from real implementations | Medium | High | Periodic integration tests with real MCP servers, contract testing |
| Test maintenance overhead | Medium | Medium | Follow DRY principles, use factories, clear documentation |

## Dependencies for Next Milestones

This milestone provides:

- **For M10**: Validated test suite ensuring quality for release
- **For Future Development**: Regression protection and confidence for refactoring
- **For CI/CD**: Automated quality gates preventing bad merges

Dependencies required from previous milestones:

- **M02**: ConfigManager for configuration testing
- **M03**: InfraDetector for detection testing
- **M04**: OnboardingWizard for wizard testing
- **M05**: Generators for deployment file testing
- **M06**: TestOrchestrator patterns for coordination testing

---

*This milestone ensures comprehensive test coverage and CI/CD automation for the Mycelium onboarding system, providing confidence in code quality and preventing regressions.*
