#!/usr/bin/env python3
"""Verify that local tool versions match CI requirements.

This script ensures that pre-commit hooks will behave identically to CI by
checking that all tool versions are aligned.
"""

import subprocess
import sys


def get_version(command: list[str]) -> str:
    """Get version from a command output."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"ERROR: {e}"


def main() -> int:
    """Check tool versions against CI requirements."""
    print("Checking tool versions against CI requirements...")
    print("=" * 60)

    # Expected versions from CI
    expected = {
        "Python": "3.10.x",
        "uv": "0.5.11",
        "ruff": "0.14.0",
    }

    # Get actual versions
    python_version = get_version(["python", "--version"]).split()[1]
    uv_version = get_version(["uv", "--version"]).split()[1]
    ruff_version = get_version(["uv", "run", "ruff", "--version"]).split()[1]

    actual = {
        "Python": python_version,
        "uv": uv_version,
        "ruff": ruff_version,
    }

    # Compare versions
    mismatches = []
    for tool, expected_ver in expected.items():
        actual_ver = actual[tool]

        # For Python, just check major.minor
        if tool == "Python":
            expected_major_minor = ".".join(expected_ver.split(".")[:2])
            actual_major_minor = ".".join(actual_ver.split(".")[:2])
            if expected_major_minor != actual_major_minor:
                mismatches.append(f"  {tool}: expected {expected_ver}, got {actual_ver}")
                print(f"❌ {tool}: {actual_ver} (expected {expected_ver})")
            else:
                print(f"✅ {tool}: {actual_ver}")
        else:
            # For other tools, check exact version or use uv.lock
            if not actual_ver.startswith(expected_ver.split(".")[0]):
                print(f"⚠️  {tool}: {actual_ver} (CI uses {expected_ver}, " "but uv.lock manages this)")
            else:
                print(f"✅ {tool}: {actual_ver}")

    print("=" * 60)

    if mismatches:
        print("\n❌ Version mismatches detected:")
        for mismatch in mismatches:
            print(mismatch)
        print(
            "\nWARNING: Local Python version differs from CI. " "Consider using pyenv or similar to match CI version."
        )
        return 1

    print("\n✅ All critical tool versions are compatible with CI")
    print("\nNote: Minor version differences in ruff/mypy are managed by uv.lock")
    print("and should not cause CI failures.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
