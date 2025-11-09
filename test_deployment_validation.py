"""Test script for deployment validation.

This script validates the Temporal + PostgreSQL deployment for Sprint 4 Phase 2.
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from mycelium_onboarding.deployment.validation import validate_deployment


async def main():
    """Run deployment validation."""
    print("=" * 80)
    print("Sprint 4 Phase 2: Temporal + PostgreSQL Deployment Validation")
    print("=" * 80)
    print()

    # Run validation with correct port (5433 from docker ps output)
    report = await validate_deployment(
        postgres_host="localhost",
        postgres_port=5433,  # Port from docker ps
        postgres_database="temporal",
        postgres_user="postgres",
        postgres_password="changeme",  # From .env file
        temporal_host="localhost",
        temporal_port=7233,
        temporal_ui_port=8080,
        temporal_namespace="default",
    )

    # Print formatted report
    print(report.format_summary())
    print()

    # Return exit code based on health
    if report.is_healthy():
        print("✓ Deployment validation PASSED - All systems healthy!")
        return 0
    elif report.can_proceed():
        print("⚠ Deployment validation PASSED with warnings - Can proceed")
        return 0
    else:
        print("✗ Deployment validation FAILED - Critical issues detected")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
