# Source: migration-guide.md
# Line: 346
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.config.migrations import Migration
from typing import Any

class Migration_1_2_to_1_3(Migration):
    """Migrate from version 1.2 to 1.3.

    Changes:
    - Add security configuration section
    - Add SSL/TLS settings
    """

    @property
    def from_version(self) -> str:
        return "1.2"

    @property
    def to_version(self) -> str:
        return "1.3"

    @property
    def description(self) -> str:
        return "Add security and SSL/TLS configuration"

    def migrate(self, config_dict: dict[str, Any]) -> dict[str, Any]:
        """Perform migration."""
        # Add security section
        config_dict["security"] = {
            "ssl_enabled": False,
            "tls_version": "1.3",
            "cert_path": None,
            "key_path": None,
        }

        # Update version
        config_dict["version"] = self.to_version

        return config_dict