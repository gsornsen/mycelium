#!/usr/bin/env python3
"""CI Status Analyzer for PR #15.

Multi-Agent Coordinator: Structured CI analysis and failure categorization.
"""

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


class CheckStatus(Enum):
    """Enumeration of CI check statuses."""

    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SKIPPED = "skipped"


class FailureCategory(Enum):
    """Enumeration of failure categories for CI checks."""

    LINTING = "linting"
    TYPE_CHECK = "type_check"
    UNIT_TEST = "unit_test"
    INTEGRATION_TEST = "integration_test"
    MIGRATION = "migration"
    BUILD = "build"
    DEPENDENCY = "dependency"
    INFRASTRUCTURE = "infrastructure"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class CheckResult:
    """Result of a CI check execution."""

    name: str
    status: CheckStatus
    conclusion: str | None
    started_at: str | None
    completed_at: str | None
    details_url: str | None


@dataclass
class FailureAnalysis:
    """Analysis of a failed CI check with recommendations."""

    check_name: str
    category: FailureCategory
    error_message: str
    log_excerpt: str
    recommendation: str
    agent_to_coordinate: str


@dataclass
class CIStatusReport:
    """Comprehensive CI status report for a pull request."""

    pr_number: int
    branch: str
    timestamp: str
    overall_status: str
    checks: list[CheckResult]
    failures: list[FailureAnalysis]
    merge_ready: bool
    recommendations: list[str]


def run_gh_command(args: list[str]) -> tuple[int, str, str]:
    """Run a gh CLI command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)


def get_pr_checks(pr_number: int) -> list[CheckResult]:
    """Get all checks for a PR."""
    returncode, stdout, stderr = run_gh_command([
        "pr", "view", str(pr_number),
        "--json", "statusCheckRollup"
    ])

    if returncode != 0:
        print(f"Error getting PR checks: {stderr}", file=sys.stderr)
        return []

    try:
        data = json.loads(stdout)
        checks = []

        for check in data.get("statusCheckRollup", []):
            status_str = check.get("status", "").lower()
            conclusion = check.get("conclusion", "").lower()

            # Map GitHub status to our enum
            if conclusion == "success":
                status = CheckStatus.SUCCESS
            elif conclusion in ["failure", "timed_out", "cancelled"]:
                status = CheckStatus.FAILURE
            elif status_str == "in_progress":
                status = CheckStatus.IN_PROGRESS
            elif status_str == "pending" or status_str == "queued":
                status = CheckStatus.PENDING
            elif conclusion == "skipped":
                status = CheckStatus.SKIPPED
            else:
                status = CheckStatus.PENDING

            checks.append(CheckResult(
                name=check.get("name", "Unknown"),
                status=status,
                conclusion=conclusion if conclusion else None,
                started_at=check.get("startedAt"),
                completed_at=check.get("completedAt"),
                details_url=check.get("detailsUrl")
            ))

        return checks
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        return []


def get_workflow_logs(branch: str) -> str | None:
    """Get logs from the latest workflow run."""
    # Get latest run ID
    returncode, stdout, stderr = run_gh_command([
        "run", "list",
        "--branch", branch,
        "--limit", "1",
        "--json", "databaseId"
    ])

    if returncode != 0:
        return None

    try:
        runs = json.loads(stdout)
        if not runs:
            return None

        run_id = runs[0]["databaseId"]

        # Get failed logs
        returncode, stdout, stderr = run_gh_command([
            "run", "view", str(run_id),
            "--log-failed"
        ])

        return stdout if returncode == 0 else None
    except (json.JSONDecodeError, KeyError, IndexError):
        return None


def categorize_failure(check_name: str, logs: str | None = None) -> FailureCategory:
    """Categorize a failure based on check name and logs."""
    name_lower = check_name.lower()

    if "lint" in name_lower or "ruff" in name_lower:
        return FailureCategory.LINTING
    if "type" in name_lower or "mypy" in name_lower:
        return FailureCategory.TYPE_CHECK
    if "unit test" in name_lower:
        return FailureCategory.UNIT_TEST
    if "integration test" in name_lower:
        return FailureCategory.INTEGRATION_TEST
    if "migration" in name_lower:
        return FailureCategory.MIGRATION
    if "build" in name_lower or "install" in name_lower:
        return FailureCategory.BUILD

    # Check logs for more context
    if logs:
        logs_lower = logs.lower()
        if "timeout" in logs_lower or "timed out" in logs_lower:
            return FailureCategory.TIMEOUT
        if "connection" in logs_lower or "network" in logs_lower:
            return FailureCategory.INFRASTRUCTURE
        if "import" in logs_lower or "module" in logs_lower:
            return FailureCategory.DEPENDENCY

    return FailureCategory.UNKNOWN


def analyze_failure(check: CheckResult, logs: str | None = None) -> FailureAnalysis:
    """Analyze a failed check and provide recommendations."""
    category = categorize_failure(check.name, logs)

    # Extract relevant log excerpt
    log_excerpt = ""
    if logs:
        lines = logs.split("\n")
        # Get last 20 lines or lines with "error" in them
        error_lines = [line for line in lines if "error" in line.lower()]
        log_excerpt = "\n".join(error_lines[-10:] if error_lines else lines[-20:])

    # Generate recommendation based on category
    recommendations = {
        FailureCategory.LINTING: (
            "Run 'uv run ruff check --fix plugins/ mycelium_onboarding/ tests/' locally",
            "python-pro"
        ),
        FailureCategory.TYPE_CHECK: (
            "Review mypy errors and add type hints. Known 29 errors may need addressing",
            "python-pro"
        ),
        FailureCategory.UNIT_TEST: (
            "Run 'uv run pytest tests/unit/ -v' locally to reproduce and fix",
            "qa-expert"
        ),
        FailureCategory.INTEGRATION_TEST: (
            "Check PostgreSQL connection and verify test database setup",
            "qa-expert"
        ),
        FailureCategory.MIGRATION: (
            "Verify alembic migrations: 'uv run alembic upgrade head'",
            "devops-incident-responder"
        ),
        FailureCategory.BUILD: (
            "Check dependency installation: 'uv sync --frozen --all-extras --group dev'",
            "devops-incident-responder"
        ),
        FailureCategory.INFRASTRUCTURE: (
            "CI infrastructure issue - may need to re-run workflow",
            "devops-incident-responder"
        ),
        FailureCategory.TIMEOUT: (
            "Test or build timeout - optimize or increase timeout limits",
            "devops-incident-responder"
        ),
        FailureCategory.DEPENDENCY: (
            "Dependency resolution issue - verify uv.lock and pyproject.toml",
            "python-pro"
        ),
    }

    recommendation, agent = recommendations.get(
        category,
        ("Investigate logs for root cause", "devops-incident-responder")
    )

    return FailureAnalysis(
        check_name=check.name,
        category=category,
        error_message=check.conclusion or "Unknown error",
        log_excerpt=log_excerpt[:500],  # Limit excerpt size
        recommendation=recommendation,
        agent_to_coordinate=agent
    )


def generate_report(pr_number: int, branch: str) -> CIStatusReport:
    """Generate comprehensive CI status report."""
    checks = get_pr_checks(pr_number)
    logs = get_workflow_logs(branch)

    # Analyze failures
    failures = []
    for check in checks:
        if check.status == CheckStatus.FAILURE:
            failures.append(analyze_failure(check, logs))

    # Determine overall status
    if not checks:
        overall_status = "UNKNOWN"
    elif any(c.status == CheckStatus.FAILURE for c in checks):
        overall_status = "FAILING"
    elif any(c.status in [CheckStatus.PENDING, CheckStatus.IN_PROGRESS] for c in checks):
        overall_status = "IN_PROGRESS"
    else:
        overall_status = "PASSING"

    # Check if merge ready
    merge_ready = (
        overall_status == "PASSING" and
        all(c.status == CheckStatus.SUCCESS for c in checks)
    )

    # Generate recommendations
    recommendations = []
    if failures:
        # Group by agent
        agent_groups: dict[str, list[str]] = {}
        for failure in failures:
            agent = failure.agent_to_coordinate
            if agent not in agent_groups:
                agent_groups[agent] = []
            agent_groups[agent].append(f"{failure.check_name}: {failure.recommendation}")

        for agent, recs in agent_groups.items():
            recommendations.append(f"Coordinate with {agent}:")
            recommendations.extend([f"  - {rec}" for rec in recs])
    elif overall_status == "IN_PROGRESS":
        recommendations.append("CI checks are still running. Monitor progress.")
    elif merge_ready:
        recommendations.append("All checks passed! PR is ready to merge.")

    return CIStatusReport(
        pr_number=pr_number,
        branch=branch,
        timestamp=datetime.utcnow().isoformat(),
        overall_status=overall_status,
        checks=checks,
        failures=failures,
        merge_ready=merge_ready,
        recommendations=recommendations
    )


def print_report(report: CIStatusReport):
    """Print formatted CI status report."""
    print("=" * 80)
    print(f"CI STATUS REPORT - PR #{report.pr_number}")
    print("=" * 80)
    print(f"Branch: {report.branch}")
    print(f"Timestamp: {report.timestamp}")
    print(f"Overall Status: {report.overall_status}")
    print(f"Merge Ready: {'YES' if report.merge_ready else 'NO'}")
    print()

    print("CHECK STATUS:")
    print("-" * 80)
    for check in report.checks:
        status_icon = {
            CheckStatus.SUCCESS: "✓",
            CheckStatus.FAILURE: "✗",
            CheckStatus.PENDING: "○",
            CheckStatus.IN_PROGRESS: "⟳",
            CheckStatus.SKIPPED: "-"
        }.get(check.status, "?")

        print(f"{status_icon} {check.name}: {check.status.value}")
        if check.details_url:
            print(f"  URL: {check.details_url}")
    print()

    if report.failures:
        print("FAILURE ANALYSIS:")
        print("-" * 80)
        for i, failure in enumerate(report.failures, 1):
            print(f"\n{i}. {failure.check_name}")
            print(f"   Category: {failure.category.value}")
            print(f"   Error: {failure.error_message}")
            print(f"   Agent: {failure.agent_to_coordinate}")
            print(f"   Recommendation: {failure.recommendation}")
            if failure.log_excerpt:
                print("   Log excerpt:")
                for line in failure.log_excerpt.split("\n")[:5]:
                    print(f"     {line}")
        print()

    print("RECOMMENDATIONS:")
    print("-" * 80)
    for rec in report.recommendations:
        print(f"• {rec}")
    print()

    print("=" * 80)


def save_report_json(report: CIStatusReport, output_file: str):
    """Save report as JSON for programmatic access."""
    # Convert dataclasses to dict
    report_dict = asdict(report)

    # Convert enums to strings
    for check in report_dict["checks"]:
        check["status"] = check["status"]

    for failure in report_dict["failures"]:
        failure["category"] = failure["category"]

    with Path(output_file).open("w") as f:
        json.dump(report_dict, f, indent=2)

    print(f"JSON report saved to: {output_file}")


def main():
    """Analyze CI status for PR #15 and generate structured report."""
    pr_number = 15
    branch = "feat/phase2-smart-onboarding-unified"

    print("Analyzing CI status for PR #15...")
    print()

    report = generate_report(pr_number, branch)
    print_report(report)

    # Save JSON report
    output_file = "/tmp/ci_status_report.json"
    save_report_json(report, output_file)

    # Exit with appropriate code
    if report.overall_status == "FAILING":
        sys.exit(1)
    elif report.overall_status == "IN_PROGRESS":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
