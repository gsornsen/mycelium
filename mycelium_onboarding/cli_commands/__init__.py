"""CLI module initialization.

This module re-exports the main CLI entry point for backward compatibility.
The actual CLI implementation is in cli.py at the package root level.
"""

# Import main from the parent package's cli.py module
# This maintains backward compatibility while allowing the commands subpackage
import sys
from pathlib import Path

# Add parent directory to path to import from sibling cli.py module
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Now we can import from the cli module (cli.py file)
# Note: This creates a circular situation, so we'll handle it differently
# The __main__.py should import directly from mycelium_onboarding.cli (the .py file)
# not from this package

__all__ = ["commands"]
