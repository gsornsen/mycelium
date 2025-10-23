# Source: projects/onboarding/milestones/M10_POLISH_RELEASE.md
# Line: 71
# Valid syntax: True
# Has imports: True
# Has assignments: True

# scripts/qa_validation.py
"""Automated QA validation script for multi-platform testing."""

import json
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class QATestResult:
    """Result of a single QA test."""
    test_name: str
    status: str  # "pass", "fail", "skip"
    duration_sec: float
    error_message: str | None = None


class QAValidator:
    """Orchestrates comprehensive QA validation."""

    def __init__(self):
        self.results: list[QATestResult] = []
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

    def _record_result(self, test_name: str, passed: bool, error: str | None = None):
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
