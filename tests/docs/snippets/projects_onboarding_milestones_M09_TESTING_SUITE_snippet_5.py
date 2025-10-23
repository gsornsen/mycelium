# Source: projects/onboarding/milestones/M09_TESTING_SUITE.md
# Line: 865
# Valid syntax: True
# Has imports: True
# Has assignments: True

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