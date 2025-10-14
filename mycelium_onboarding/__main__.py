"""Entry point for running mycelium_onboarding as a module.

This allows the package to be run as:
    python -m mycelium_onboarding <command>
"""

from mycelium_onboarding.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
