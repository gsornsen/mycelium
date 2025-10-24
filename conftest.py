"""Root conftest.py for pytest configuration.

This file is loaded before any test collection happens,
allowing us to modify sys.path before test modules are imported.
"""

import sys
from pathlib import Path

# Add plugins/mycelium-core to Python path so tests can import modules directly
project_root = Path(__file__).parent
mycelium_core_dir = project_root / "plugins" / "mycelium-core"

print(f"[conftest.py] Adding {mycelium_core_dir} to sys.path")

if str(mycelium_core_dir) not in sys.path:
    sys.path.insert(0, str(mycelium_core_dir))
    print(f"[conftest.py] Added {mycelium_core_dir} to sys.path")
else:
    print(f"[conftest.py] {mycelium_core_dir} already in sys.path")

# Debug: verify imports work
try:
    from coordination.protocol import HandoffProtocol
    print("[conftest.py] Successfully imported HandoffProtocol")
except ImportError as e:
    print(f"[conftest.py] Failed to import: {e}")
