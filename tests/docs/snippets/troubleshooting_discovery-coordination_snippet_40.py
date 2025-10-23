# Source: troubleshooting/discovery-coordination.md
# Line: 962
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Solution 1: Restart API service
import subprocess
subprocess.run(["systemctl", "restart", "mycelium-discovery-api"])

# Solution 2: Reload registry
from plugins.mycelium_core.agent_discovery import reload_registry

reload_registry(force=True)

# Solution 3: Check database connection
from plugins.mycelium_core.registry import check_database_health

db_health = check_database_health()
if not db_health["connected"]:
    print(f"Database connection failed: {db_health['error']}")
    # Fix database connection

# Solution 4: Rebuild registry
from plugins.mycelium_core.registry import rebuild_registry

rebuild_registry(
    source="plugins/mycelium-core/agents/index.json"
)