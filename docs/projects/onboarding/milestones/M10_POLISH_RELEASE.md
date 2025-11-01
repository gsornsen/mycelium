# M10: Polish & Release

## Overview

**Duration**: 2 days **Dependencies**: M06 (Coordination Testing), M07 (Configuration Management), M08 (Documentation),
M09 (Testing Suite) **Blocks**: Public release **Critical Path**: Yes - final milestone

**Lead Agent**: qa-expert **Support Agents**: devops-engineer, performance-engineer, technical-writer

## Why This Milestone

This final milestone focuses on quality assurance, performance optimization, and release preparation. It ensures the
onboarding system is production-ready with comprehensive validation across all supported platforms, performance
profiling to identify bottlenecks, release candidate testing, and post-release monitoring setup. This milestone
transforms a functional implementation into a polished, reliable product ready for end users.

## Requirements

### Functional Requirements (FR)

- **FR-10.1**: Complete QA validation on all supported platforms (Linux, macOS, Windows/WSL2)
- **FR-10.2**: Performance profiling identifying and resolving bottlenecks
- **FR-10.3**: Release candidate validation with beta testers
- **FR-10.4**: Version tagging and comprehensive release notes
- **FR-10.5**: Post-release monitoring and alerting infrastructure

### Technical Requirements (TR)

- **TR-10.1**: Automated QA checklist covering all features and workflows
- **TR-10.2**: Performance benchmarks for key operations (detection, generation, wizard)
- **TR-10.3**: Release automation with changelog generation
- **TR-10.4**: Monitoring dashboards tracking adoption and errors
- **TR-10.5**: Rollback procedures and emergency response plan

### Integration Requirements (IR)

- **IR-10.1**: QA validates integration of all milestones (M01-M09)
- **IR-10.2**: Performance testing validates coordination patterns from M06
- **IR-10.3**: Release process integrates with GitHub releases and tags

### Compliance Requirements (CR)

- **CR-10.1**: All documentation reviewed for accuracy and completeness
- **CR-10.2**: Security review of generated deployment files
- **CR-10.3**: License compliance verified for all dependencies
- **CR-10.4**: Privacy review for data handling (no PII collection)

______________________________________________________________________

## Tasks

### Task 10.1: Multi-Platform QA Validation

**Effort**: 6 hours **Agent**: qa-expert, devops-engineer

Execute comprehensive QA validation across all supported platforms with automated checklist.

**QA Test Matrix**:

| Platform | Version             | Python     | Docker | Tests      |
| -------- | ------------------- | ---------- | ------ | ---------- |
| Ubuntu   | 22.04 LTS           | 3.11, 3.12 | 24.0+  | Full suite |
| Ubuntu   | 24.04 LTS           | 3.11, 3.12 | 24.0+  | Full suite |
| macOS    | 13 (Ventura)        | 3.11, 3.12 | 24.0+  | Full suite |
| macOS    | 14 (Sonoma)         | 3.11, 3.12 | 24.0+  | Full suite |
| Windows  | WSL2 (Ubuntu 22.04) | 3.11, 3.12 | 24.0+  | Full suite |

**Automated QA Checklist**:

```python
# scripts/qa_validation.py
"""Automated QA validation script for multi-platform testing."""

import subprocess
import sys
import platform
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import json


@dataclass
class QATestResult:
    """Result of a single QA test."""
    test_name: str
    status: str  # "pass", "fail", "skip"
    duration_sec: float
    error_message: Optional[str] = None


class QAValidator:
    """Orchestrates comprehensive QA validation."""

    def __init__(self):
        self.results: List[QATestResult] = []
        self.platform_info = self._gather_platform_info()

    def _gather_platform_info(self) -> dict:
        """Gather platform information for reporting."""
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "architecture": platform.machine(),
        }

    def run_all_checks(self) -> bool:
        """Run all QA checks and return overall pass/fail."""
        print("=" * 60)
        print("Starting QA Validation")
        print("=" * 60)
        print(f"Platform: {self.platform_info['os']}")
        print(f"Python: {self.platform_info['python_version']}")
        print()

        # Category 1: Installation & Setup
        self._check_dependencies()
        self._check_installation()

        # Category 2: Detection System
        self._check_docker_detection()
        self._check_redis_detection()
        self._check_postgres_detection()

        # Category 3: Onboarding Wizard
        self._check_wizard_flow()
        self._check_configuration_persistence()

        # Category 4: Deployment Generation
        self._check_docker_compose_generation()
        self._check_justfile_generation()
        self._check_secrets_generation()

        # Category 5: Testing Framework
        self._check_coordination_tests()
        self._check_unit_tests()
        self._check_integration_tests()

        # Category 6: CLI Commands
        self._check_slash_commands()

        # Category 7: Documentation
        self._check_documentation_accuracy()

        # Generate report
        self._generate_report()

        # Return overall status
        failed_count = sum(1 for r in self.results if r.status == "fail")
        return failed_count == 0

    def _check_dependencies(self):
        """Verify all required dependencies are installed."""
        print("Checking dependencies...")

        # Check uv
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True
        )
        self._record_result("uv_installed", result.returncode == 0)

        # Check Docker (if available)
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True
        )
        self._record_result("docker_available", result.returncode == 0)

    def _check_installation(self):
        """Verify mycelium package is correctly installed."""
        print("Checking installation...")

        result = subprocess.run(
            ["uv", "run", "python", "-c", "import mycelium; print(mycelium.__version__)"],
            capture_output=True,
            text=True
        )
        self._record_result("mycelium_installed", result.returncode == 0)

    def _check_docker_detection(self):
        """Test Docker detection accuracy."""
        print("Checking Docker detection...")

        result = subprocess.run(
            ["uv", "run", "python", "-c",
             "from mycelium.detection import InfraDetector; "
             "d = InfraDetector(); "
             "r = d.detect_docker(); "
             "print('available' if r.available else 'unavailable')"],
            capture_output=True,
            text=True
        )

        self._record_result("docker_detection", result.returncode == 0)

    def _check_wizard_flow(self):
        """Test onboarding wizard completion."""
        print("Checking wizard flow...")

        # Create test inputs file
        test_inputs = """redis
postgres

docker-compose
y
"""
        inputs_file = Path("/tmp/qa_wizard_inputs.txt")
        inputs_file.write_text(test_inputs)

        result = subprocess.run(
            ["uv", "run", "mycelium-onboarding", "--non-interactive"],
            input=test_inputs,
            capture_output=True,
            text=True
        )

        self._record_result("wizard_flow", result.returncode == 0)

    def _check_docker_compose_generation(self):
        """Test Docker Compose file generation."""
        print("Checking Docker Compose generation...")

        result = subprocess.run(
            ["uv", "run", "python", "-c",
             "from mycelium.generators import DockerComposeGenerator; "
             "from mycelium.config import MyceliumConfig; "
             "config = MyceliumConfig(); "
             "gen = DockerComposeGenerator(); "
             "output = gen.generate(config); "
             "print('valid' if 'services:' in output else 'invalid')"],
            capture_output=True,
            text=True
        )

        self._record_result(
            "docker_compose_generation",
            result.returncode == 0 and "valid" in result.stdout
        )

    def _check_coordination_tests(self):
        """Run coordination tests from M06."""
        print("Running coordination tests...")

        result = subprocess.run(
            ["uv", "run", "pytest", "tests/integration/test_coordination.py", "-v"],
            capture_output=True,
            text=True
        )

        self._record_result("coordination_tests", result.returncode == 0)

    def _check_unit_tests(self):
        """Run unit tests from M09."""
        print("Running unit tests...")

        result = subprocess.run(
            ["uv", "run", "pytest", "tests/unit/", "-v"],
            capture_output=True,
            text=True
        )

        self._record_result("unit_tests", result.returncode == 0)

    def _check_slash_commands(self):
        """Verify all slash commands are accessible."""
        print("Checking slash commands...")

        commands = [
            "mycelium-onboarding",
            "mycelium-generate",
            "mycelium-test",
            "mycelium-configuration",
        ]

        for cmd in commands:
            result = subprocess.run(
                ["uv", "run", cmd, "--help"],
                capture_output=True,
                text=True
            )
            self._record_result(f"slash_command_{cmd}", result.returncode == 0)

    def _check_documentation_accuracy(self):
        """Verify documentation examples are accurate."""
        print("Checking documentation accuracy...")

        # Check installation guide
        install_guide = Path("docs/INSTALLATION.md")
        self._record_result(
            "installation_guide_exists",
            install_guide.exists()
        )

        # Check getting started tutorial
        tutorial = Path("docs/GETTING_STARTED.md")
        self._record_result(
            "getting_started_exists",
            tutorial.exists()
        )

    def _record_result(self, test_name: str, passed: bool, error: Optional[str] = None):
        """Record test result."""
        result = QATestResult(
            test_name=test_name,
            status="pass" if passed else "fail",
            duration_sec=0.0,
            error_message=error
        )
        self.results.append(result)

        status_symbol = "✓" if passed else "✗"
        print(f"  {status_symbol} {test_name}")

    def _generate_report(self):
        """Generate QA validation report."""
        print("\n" + "=" * 60)
        print("QA Validation Report")
        print("=" * 60)

        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "pass")
        failed = sum(1 for r in self.results if r.status == "fail")

        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")

        if failed > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if result.status == "fail":
                    print(f"  ✗ {result.test_name}")
                    if result.error_message:
                        print(f"    Error: {result.error_message}")

        # Save JSON report
        report_path = Path("qa_report.json")
        report_data = {
            "platform": self.platform_info,
            "results": [
                {
                    "test": r.test_name,
                    "status": r.status,
                    "duration": r.duration_sec,
                    "error": r.error_message
                }
                for r in self.results
            ],
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": passed / total if total > 0 else 0
            }
        }
        report_path.write_text(json.dumps(report_data, indent=2))
        print(f"\nDetailed report saved to: {report_path}")


def main():
    """Main entry point."""
    validator = QAValidator()
    success = validator.run_all_checks()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
```

**Manual QA Checklist** (for platform-specific issues):

```markdown
# Manual QA Checklist

## Linux (Ubuntu 22.04 / 24.04)
- [ ] Package installation succeeds with uv
- [ ] All slash commands are executable
- [ ] Docker detection works correctly
- [ ] Native service detection works (systemd)
- [ ] File permissions are correct (0644 for config, 0755 for scripts)
- [ ] XDG directories used correctly (~/.config, ~/.local/share)

## macOS (Ventura / Sonoma)
- [ ] Package installation succeeds with uv
- [ ] All slash commands are executable
- [ ] Docker Desktop detection works
- [ ] Homebrew service detection works
- [ ] File permissions are correct
- [ ] XDG directories respected (if configured)

## Windows (WSL2 - Ubuntu 22.04)
- [ ] Package installation succeeds with uv
- [ ] All slash commands are executable
- [ ] Docker Desktop for Windows detected in WSL2
- [ ] Windows paths properly converted
- [ ] File permissions work correctly in WSL2 filesystem
- [ ] Line endings handled correctly (LF not CRLF)
```

______________________________________________________________________

### Task 10.2: Performance Profiling and Optimization

**Effort**: 5 hours **Agent**: performance-engineer, python-pro

Profile key operations and optimize bottlenecks to ensure responsive user experience.

**Performance Benchmarking Script**:

```python
# scripts/performance_benchmark.py
"""Performance benchmarking for key operations."""

import time
import statistics
from typing import List, Callable
from dataclasses import dataclass
import cProfile
import pstats
from io import StringIO


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""
    operation_name: str
    mean_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    iterations: int


class PerformanceBenchmark:
    """Performance benchmarking suite."""

    def __init__(self, iterations: int = 100):
        self.iterations = iterations
        self.results: List[BenchmarkResult] = []

    def benchmark_operation(
        self,
        name: str,
        operation: Callable,
        warmup: int = 10
    ) -> BenchmarkResult:
        """Benchmark a single operation."""
        print(f"Benchmarking: {name}")

        # Warmup
        for _ in range(warmup):
            operation()

        # Measure
        timings: List[float] = []
        for _ in range(self.iterations):
            start = time.perf_counter()
            operation()
            end = time.perf_counter()
            timings.append((end - start) * 1000)  # Convert to ms

        # Calculate statistics
        result = BenchmarkResult(
            operation_name=name,
            mean_ms=statistics.mean(timings),
            median_ms=statistics.median(timings),
            p95_ms=self._percentile(timings, 95),
            p99_ms=self._percentile(timings, 99),
            min_ms=min(timings),
            max_ms=max(timings),
            iterations=self.iterations
        )

        self.results.append(result)
        self._print_result(result)

        return result

    def profile_operation(
        self,
        name: str,
        operation: Callable
    ):
        """Profile operation with cProfile to identify hotspots."""
        print(f"\nProfiling: {name}")

        profiler = cProfile.Profile()
        profiler.enable()

        operation()

        profiler.disable()

        # Print stats
        stream = StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.strip_dirs()
        stats.sort_stats('cumulative')
        stats.print_stats(20)  # Top 20 functions

        print(stream.getvalue())

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[index]

    def _print_result(self, result: BenchmarkResult):
        """Print benchmark result."""
        print(f"  Mean: {result.mean_ms:.2f}ms")
        print(f"  Median: {result.median_ms:.2f}ms")
        print(f"  P95: {result.p95_ms:.2f}ms")
        print(f"  P99: {result.p99_ms:.2f}ms")
        print(f"  Range: [{result.min_ms:.2f}ms - {result.max_ms:.2f}ms]")
        print()

    def generate_report(self):
        """Generate performance benchmark report."""
        print("=" * 60)
        print("Performance Benchmark Report")
        print("=" * 60)

        for result in self.results:
            status = "✓ PASS" if result.mean_ms < 100 else "⚠ SLOW"
            print(f"{status} {result.operation_name}: {result.mean_ms:.2f}ms (mean)")


def main():
    """Run performance benchmarks."""
    from mycelium.detection import InfraDetector
    from mycelium.config import ConfigManager, MyceliumConfig
    from mycelium.generators import DockerComposeGenerator, JustfileGenerator

    benchmark = PerformanceBenchmark(iterations=100)

    # Benchmark detection operations
    detector = InfraDetector()
    benchmark.benchmark_operation(
        "Docker Detection",
        lambda: detector.detect_docker()
    )
    benchmark.benchmark_operation(
        "Redis Detection",
        lambda: detector.detect_redis()
    )
    benchmark.benchmark_operation(
        "Full Infrastructure Scan",
        lambda: detector.scan_all()
    )

    # Benchmark configuration operations
    sample_config = MyceliumConfig()
    benchmark.benchmark_operation(
        "Configuration Validation",
        lambda: MyceliumConfig.model_validate(sample_config.model_dump())
    )

    # Benchmark generation operations
    docker_gen = DockerComposeGenerator()
    benchmark.benchmark_operation(
        "Docker Compose Generation",
        lambda: docker_gen.generate(sample_config)
    )

    justfile_gen = JustfileGenerator()
    benchmark.benchmark_operation(
        "Justfile Generation",
        lambda: justfile_gen.generate(sample_config)
    )

    # Generate report
    benchmark.generate_report()

    # Profile slowest operation
    print("\n" + "=" * 60)
    print("Detailed Profiling")
    print("=" * 60)
    benchmark.profile_operation(
        "Full Infrastructure Scan (detailed)",
        lambda: detector.scan_all()
    )


if __name__ == "__main__":
    main()
```

**Performance Targets**:

| Operation                 | Target  | Acceptable | Threshold |
| ------------------------- | ------- | ---------- | --------- |
| Docker detection          | \<50ms  | \<100ms    | \<200ms   |
| Redis detection           | \<30ms  | \<50ms     | \<100ms   |
| Full infrastructure scan  | \<200ms | \<500ms    | \<1000ms  |
| Configuration validation  | \<10ms  | \<20ms     | \<50ms    |
| Docker Compose generation | \<20ms  | \<50ms     | \<100ms   |
| Justfile generation       | \<20ms  | \<50ms     | \<100ms   |
| Wizard complete flow      | \<5s    | \<10s      | \<20s     |

**Optimization Strategies**:

1. **Caching**: Cache detection results during wizard session
1. **Parallel Detection**: Run Docker/Redis/Postgres detection concurrently
1. **Template Caching**: Pre-compile Jinja2 templates
1. **Lazy Loading**: Defer imports until needed
1. **Async Operations**: Use async/await for I/O-bound operations

______________________________________________________________________

### Task 10.3: Release Candidate Validation

**Effort**: 4 hours **Agent**: qa-expert, devops-engineer

Create release candidate, conduct beta testing, and validate release artifacts.

**Release Candidate Checklist**:

```markdown
# Release Candidate Validation Checklist

## Pre-Release Validation

### Code Quality
- [ ] All unit tests passing (≥80% coverage)
- [ ] All integration tests passing
- [ ] No critical or high-severity linting warnings
- [ ] Type checking passes with no errors (mypy)
- [ ] Security scan passes (bandit)
- [ ] No known security vulnerabilities in dependencies

### Documentation
- [ ] README.md is accurate and complete
- [ ] CHANGELOG.md includes all changes since last release
- [ ] Installation guide tested on all platforms
- [ ] Getting started tutorial verified
- [ ] API documentation is up-to-date
- [ ] Troubleshooting guide covers common issues

### Functionality
- [ ] All slash commands work correctly
- [ ] Onboarding wizard completes successfully
- [ ] Configuration persistence works
- [ ] Deployment file generation produces valid output
- [ ] Coordination tests pass
- [ ] All features from M01-M09 are functional

### Platform Compatibility
- [ ] Tested on Ubuntu 22.04 (Python 3.11, 3.12)
- [ ] Tested on Ubuntu 24.04 (Python 3.11, 3.12)
- [ ] Tested on macOS Ventura (Python 3.11, 3.12)
- [ ] Tested on macOS Sonoma (Python 3.11, 3.12)
- [ ] Tested on Windows WSL2 (Python 3.11, 3.12)

### Performance
- [ ] All operations meet performance targets
- [ ] No memory leaks detected
- [ ] Resource usage is acceptable

## Beta Testing

### Beta Tester Recruitment
- [ ] Identify 5-10 beta testers (internal team + external volunteers)
- [ ] Provide beta access to release candidate
- [ ] Distribute beta testing guide

### Beta Testing Activities
- [ ] Fresh installation on clean system
- [ ] Onboarding wizard workflow
- [ ] Docker deployment method
- [ ] Justfile deployment method
- [ ] Configuration management
- [ ] Error handling and recovery

### Feedback Collection
- [ ] Bug reports collected and tracked
- [ ] Feature requests documented
- [ ] User experience feedback gathered
- [ ] Performance feedback collected

### Issue Resolution
- [ ] Critical bugs fixed in RC
- [ ] High-priority issues addressed
- [ ] Medium-priority issues triaged for future releases
- [ ] Low-priority issues documented for backlog

## Release Artifacts

### Package
- [ ] Version number updated (pyproject.toml)
- [ ] Build succeeds without errors
- [ ] Package includes all necessary files
- [ ] Package size is reasonable (<5MB)

### Distribution
- [ ] GitHub release created with tag
- [ ] Release notes published
- [ ] Binary artifacts uploaded (if applicable)
- [ ] Checksum files generated

### Communication
- [ ] Release announcement drafted
- [ ] Documentation website updated
- [ ] Social media posts prepared (if applicable)
```

**Beta Testing Guide**:

````markdown
# Beta Testing Guide - Mycelium Onboarding v1.0.0-rc1

Thank you for participating in beta testing!

## Setup

1. **Install release candidate**:
   ```bash
   git clone https://github.com/your-org/mycelium.git
   cd mycelium
   git checkout v1.0.0-rc1
   uv venv
   source .venv/bin/activate
   uv sync
````

2. **Verify installation**:
   ```bash
   uv run mycelium-onboarding --version
   ```

## Testing Scenarios

### Scenario 1: Fresh Onboarding (Docker)

1. Run `/mycelium-onboarding`
1. Select services: Redis, Postgres, TaskQueue
1. Choose deployment method: docker-compose
1. Verify configuration saved
1. Generate deployment files: `/mycelium-generate`
1. Start services: `docker-compose up -d`
1. Test coordination: `/mycelium-test --pattern pubsub`

**Expected**: All steps complete successfully, services start, tests pass

### Scenario 2: Configuration Management

1. View configuration: `/mycelium-configuration show`
1. Edit configuration: `/mycelium-configuration edit`
1. Validate: `/mycelium-configuration validate`

**Expected**: Configuration displays correctly, edits persist, validation succeeds

### Scenario 3: Error Recovery

1. Introduce error: Edit config.yaml with invalid port (e.g., port: 70000)
1. Run validation: `/mycelium-configuration validate --strict`
1. Observe error message and guidance

**Expected**: Clear error message, helpful guidance for fix

## Feedback Template

Please provide feedback using this template:

**Bug Report**:

- Title: \[Brief description\]
- Steps to reproduce:
- Expected behavior:
- Actual behavior:
- Platform: \[OS, Python version\]
- Severity: \[Critical / High / Medium / Low\]

**Feature Request**:

- Title: \[Brief description\]
- Use case:
- Proposed solution:
- Priority: \[High / Medium / Low\]

**General Feedback**:

- What worked well:
- What was confusing:
- Suggestions for improvement:

Submit feedback to: \[feedback@your-org.com\]

````

---

### Task 10.4: Version Tagging and Release Notes

**Effort**: 3 hours
**Agent**: devops-engineer, technical-writer

Create version tag, generate comprehensive release notes, and publish release.

**Release Automation Script**:

```bash
# scripts/create_release.sh
#!/usr/bin/env bash
set -euo pipefail

# Release automation script
VERSION="${1:-}"

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.0.0"
    exit 1
fi

echo "Creating release for version: $VERSION"

# Validate version format (semver)
if ! echo "$VERSION" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$'; then
    echo "Error: Invalid version format. Use semantic versioning (e.g., 1.0.0 or 1.0.0-rc1)"
    exit 1
fi

# Update version in pyproject.toml
echo "Updating version in pyproject.toml..."
sed -i "s/^version = .*/version = \"$VERSION\"/" pyproject.toml

# Generate changelog
echo "Generating changelog..."
python scripts/generate_changelog.py "$VERSION" > CHANGELOG_LATEST.md

# Commit version bump
echo "Committing version bump..."
git add pyproject.toml CHANGELOG.md CHANGELOG_LATEST.md
git commit -m "chore: bump version to $VERSION"

# Create git tag
echo "Creating git tag..."
git tag -a "v$VERSION" -m "Release $VERSION"

# Push to remote
echo "Pushing to remote..."
git push origin main
git push origin "v$VERSION"

# Create GitHub release
echo "Creating GitHub release..."
gh release create "v$VERSION" \
    --title "Mycelium Onboarding v$VERSION" \
    --notes-file CHANGELOG_LATEST.md \
    --verify-tag

echo "✓ Release v$VERSION created successfully!"
echo ""
echo "Next steps:"
echo "1. Monitor GitHub Actions for release workflow completion"
echo "2. Verify release artifacts are published"
echo "3. Announce release to users"
````

**Changelog Generation Script**:

```python
# scripts/generate_changelog.py
"""Generate changelog from git commits."""

import subprocess
import sys
from datetime import datetime
from typing import List, Dict
import re


def get_commits_since_last_tag() -> List[str]:
    """Get commits since last release tag."""
    # Get last tag
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        last_tag = result.stdout.strip()
        commit_range = f"{last_tag}..HEAD"
    else:
        # No previous tags, get all commits
        commit_range = "HEAD"

    # Get commits
    result = subprocess.run(
        ["git", "log", commit_range, "--pretty=format:%H|%s|%an|%ad"],
        capture_output=True,
        text=True
    )

    return result.stdout.strip().split('\n') if result.stdout else []


def parse_commit(commit_line: str) -> Dict[str, str]:
    """Parse commit line into structured data."""
    parts = commit_line.split('|')
    return {
        'hash': parts[0][:7],
        'subject': parts[1],
        'author': parts[2],
        'date': parts[3],
    }


def categorize_commits(commits: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize commits by type (feat, fix, docs, etc.)."""
    categories = {
        'Features': [],
        'Bug Fixes': [],
        'Documentation': [],
        'Performance': [],
        'Refactoring': [],
        'Testing': [],
        'Chores': [],
        'Other': [],
    }

    for commit in commits:
        subject = commit['subject']

        if re.match(r'^feat(\(.*\))?:', subject):
            categories['Features'].append(commit)
        elif re.match(r'^fix(\(.*\))?:', subject):
            categories['Bug Fixes'].append(commit)
        elif re.match(r'^docs(\(.*\))?:', subject):
            categories['Documentation'].append(commit)
        elif re.match(r'^perf(\(.*\))?:', subject):
            categories['Performance'].append(commit)
        elif re.match(r'^refactor(\(.*\))?:', subject):
            categories['Refactoring'].append(commit)
        elif re.match(r'^test(\(.*\))?:', subject):
            categories['Testing'].append(commit)
        elif re.match(r'^chore(\(.*\))?:', subject):
            categories['Chores'].append(commit)
        else:
            categories['Other'].append(commit)

    return categories


def generate_changelog(version: str) -> str:
    """Generate changelog in markdown format."""
    today = datetime.now(UTC).strftime('%Y-%m-%d')

    changelog = f"# Release {version}\n\n"
    changelog += f"**Release Date**: {today}\n\n"

    # Get and parse commits
    commit_lines = get_commits_since_last_tag()
    commits = [parse_commit(line) for line in commit_lines if line]

    if not commits:
        changelog += "No changes since last release.\n"
        return changelog

    # Categorize
    categories = categorize_commits(commits)

    # Generate sections
    for category, commits_in_category in categories.items():
        if not commits_in_category:
            continue

        changelog += f"## {category}\n\n"

        for commit in commits_in_category:
            # Clean up commit subject (remove conventional commit prefix)
            subject = re.sub(r'^[a-z]+(\(.*\))?:\s*', '', commit['subject'])
            changelog += f"- {subject} ([{commit['hash']}](https://github.com/your-org/mycelium/commit/{commit['hash']}))\n"

        changelog += "\n"

    # Add contributors
    contributors = sorted(set(c['author'] for c in commits))
    changelog += "## Contributors\n\n"
    changelog += "Thank you to all contributors:\n\n"
    for contributor in contributors:
        changelog += f"- @{contributor}\n"

    return changelog


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python generate_changelog.py <version>")
        sys.exit(1)

    version = sys.argv[1]
    changelog = generate_changelog(version)

    print(changelog)


if __name__ == "__main__":
    main()
```

**Release Notes Template**:

````markdown
# Mycelium Onboarding v1.0.0

**Release Date**: 2025-01-XX

## Overview

Mycelium Onboarding v1.0.0 is the first stable release, providing an interactive CLI wizard for agent coordination infrastructure setup. This release includes comprehensive detection, configuration management, deployment generation, and testing capabilities.

## What's New

### Interactive Onboarding Wizard (M04)
- InquirerPy-based wizard for service selection
- Automatic infrastructure detection
- Configuration persistence with validation

### Deployment Generation (M05)
- Docker Compose generation with healthchecks
- Justfile generation for native deployments
- Automatic secrets generation

### Testing Framework (M06, M09)
- Coordination pattern tests (pub/sub, task queues, barriers)
- Unit test suite with ≥80% coverage
- Integration tests for full workflows

### Configuration Management (M07)
- CLI commands for viewing and editing configuration
- Validation with helpful error messages
- Template-based initialization

### Documentation (M08)
- Installation guides for Linux, macOS, Windows/WSL2
- Getting started tutorial
- Comprehensive command reference

## Features

- **Multi-platform support**: Linux, macOS, Windows (WSL2)
- **Multiple deployment methods**: Docker Compose, Justfile (native)
- **MCP integration**: Redis, TaskQueue, Temporal, Postgres
- **Comprehensive testing**: Unit, integration, coordination tests
- **Performance optimized**: All operations <1s response time

## Installation

```bash
git clone https://github.com/your-org/mycelium.git
cd mycelium
uv venv
source .venv/bin/activate
uv sync
````

## Quick Start

```bash
# Run onboarding wizard
/mycelium-onboarding

# Generate deployment files
/mycelium-generate

# Start services
docker-compose up -d

# Test coordination
/mycelium-test --pattern pubsub
```

## System Requirements

- Python 3.11 or 3.12
- uv package manager
- Docker 20.10+ (for containerized deployment)
- 2GB RAM minimum
- 5GB disk space

## Known Issues

- Issue #42: Wizard may hang on slow Docker daemon responses (workaround: increase timeout)
- Issue #51: macOS Homebrew service detection requires manual path configuration

## Contributors

Thank you to all contributors who made this release possible!

## Links

- [Documentation](https://docs.mycelium.dev)
- [GitHub Repository](https://github.com/your-org/mycelium)
- [Issue Tracker](https://github.com/your-org/mycelium/issues)
- [Changelog](https://github.com/your-org/mycelium/blob/main/CHANGELOG.md)

````

---

### Task 10.5: Post-Release Monitoring and Support

**Effort**: 4 hours
**Agent**: devops-engineer, performance-monitor

Set up monitoring, alerting, and support infrastructure for post-release.

**Monitoring Dashboard Configuration**:

```yaml
# monitoring/grafana_dashboard.json
{
  "dashboard": {
    "title": "Mycelium Onboarding - Usage & Errors",
    "panels": [
      {
        "title": "Onboarding Wizard Completions",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mycelium_wizard_completions_total[5m])"
          }
        ]
      },
      {
        "title": "Error Rate by Operation",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mycelium_errors_total[5m])"
          }
        ]
      },
      {
        "title": "Platform Distribution",
        "type": "pie",
        "targets": [
          {
            "expr": "sum by (platform) (mycelium_installations_total)"
          }
        ]
      },
      {
        "title": "Deployment Method Distribution",
        "type": "pie",
        "targets": [
          {
            "expr": "sum by (method) (mycelium_deployments_total)"
          }
        ]
      }
    ]
  }
}
````

**Telemetry Collection (Optional, Opt-in)**:

```python
# mycelium/telemetry.py
"""Optional telemetry for usage analytics (opt-in only)."""

import os
import platform
from typing import Optional
import requests
from pathlib import Path


class TelemetryClient:
    """Client for sending anonymous usage telemetry."""

    TELEMETRY_ENDPOINT = "https://telemetry.mycelium.dev/v1/events"

    def __init__(self):
        self.enabled = self._check_telemetry_enabled()
        self.session_id = self._generate_session_id()

    def _check_telemetry_enabled(self) -> bool:
        """Check if user has opted into telemetry."""
        # Check environment variable
        if os.getenv("MYCELIUM_TELEMETRY", "0") == "1":
            return True

        # Check config file
        config_file = Path.home() / ".config" / "mycelium" / "telemetry"
        return config_file.exists()

    def _generate_session_id(self) -> str:
        """Generate anonymous session ID."""
        import uuid
        return str(uuid.uuid4())

    def track_event(
        self,
        event_name: str,
        properties: Optional[dict] = None
    ):
        """Track usage event (async, non-blocking)."""
        if not self.enabled:
            return

        event_data = {
            "event": event_name,
            "properties": properties or {},
            "session_id": self.session_id,
            "platform": platform.system(),
            "python_version": platform.python_version(),
        }

        # Send asynchronously, don't block on failure
        try:
            requests.post(
                self.TELEMETRY_ENDPOINT,
                json=event_data,
                timeout=1.0
            )
        except Exception:
            # Silently fail, never disrupt user experience
            pass


# Global telemetry client
telemetry = TelemetryClient()


# Example usage in code
def track_wizard_completion(deployment_method: str):
    """Track wizard completion event."""
    telemetry.track_event("wizard_completed", {
        "deployment_method": deployment_method
    })
```

**Support Triage Workflow**:

```markdown
# Support Triage Workflow

## Issue Classification

### P0 - Critical (Response: <2 hours)
- Complete system failure
- Data loss or corruption
- Security vulnerability

### P1 - High (Response: <24 hours)
- Feature broken for all users
- Severe performance degradation
- Installation failure on supported platform

### P2 - Medium (Response: <3 days)
- Feature broken for subset of users
- Minor performance issues
- Documentation errors

### P3 - Low (Response: <1 week)
- Feature requests
- Cosmetic issues
- Enhancement suggestions

## Escalation Path

1. **User reports issue** → GitHub Issues
2. **Triage by qa-expert** → Classify priority
3. **P0/P1 issues** → Immediate assignment to appropriate agent
4. **P2/P3 issues** → Backlog for next sprint
5. **Resolution** → Patch release or next minor version

## Release Hotfix Process

If critical bug (P0) discovered post-release:

1. Create hotfix branch from release tag
2. Implement minimal fix
3. Fast-track testing (automated + manual)
4. Release patch version (e.g., 1.0.1)
5. Backport fix to main branch
```

______________________________________________________________________

## Exit Criteria

- [ ] QA validation passes on all supported platforms (Linux, macOS, Windows/WSL2)
- [ ] Performance benchmarks meet or exceed targets
- [ ] Beta testing completed with feedback incorporated
- [ ] Release candidate validated and approved
- [ ] Version tagged in git with semantic versioning
- [ ] Comprehensive release notes published
- [ ] GitHub release created with artifacts
- [ ] Documentation website updated with v1.0.0 content
- [ ] Monitoring dashboard deployed and operational
- [ ] Support triage workflow documented and communicated
- [ ] Emergency rollback procedure tested and documented

## Deliverables

1. **QA Validation Report** (qa_report.json)

   - Multi-platform test results
   - Manual QA checklist completion
   - Platform-specific issues documented

1. **Performance Benchmark Report** (performance_report.json)

   - Operation timings
   - Profiling results
   - Optimization recommendations

1. **Release Artifacts**

   - Git tag (v1.0.0)
   - GitHub release
   - Release notes (CHANGELOG.md)
   - Binary packages (if applicable)

1. **Monitoring Infrastructure**

   - Grafana dashboard configuration
   - Telemetry client (opt-in)
   - Alert rules

1. **Support Documentation**

   - Triage workflow
   - Escalation paths
   - Hotfix procedures

## Risk Assessment

| Risk                                         | Likelihood | Impact | Mitigation                                                   |
| -------------------------------------------- | ---------- | ------ | ------------------------------------------------------------ |
| Critical bug found post-release              | Medium     | High   | Comprehensive QA, beta testing, hotfix process ready         |
| Performance degradation on specific platform | Low        | Medium | Multi-platform benchmarking, platform-specific optimization  |
| Documentation inaccuracies                   | Medium     | Low    | Technical writer review, beta tester validation              |
| User adoption lower than expected            | Medium     | Low    | Clear documentation, onboarding tutorials, community support |
| Dependency vulnerability discovered          | Low        | High   | Regular security scans, rapid patch release process          |

## Dependencies for Post-Release

This milestone completes the onboarding system development. Post-release activities:

- **Ongoing**: Monitor usage metrics and error rates
- **Weekly**: Triage new issues and user feedback
- **Monthly**: Review roadmap and plan next features
- **Quarterly**: Major version releases with new capabilities

______________________________________________________________________

*This milestone marks the completion of the Mycelium onboarding system development, delivering a polished,
production-ready solution validated across all supported platforms.*
