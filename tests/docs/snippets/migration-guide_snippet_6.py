# Source: migration-guide.md
# Line: 448
# Valid syntax: True
# Has imports: False
# Has assignments: True

def migrate(self, config_dict: dict[str, Any]) -> dict[str, Any]:
    # Add new feature disabled by default (safe)
    config_dict["monitoring"] = {
        "enabled": False,  # Disabled by default
        "metrics_port": 9090,
        "interval": 30,
    }

    # User can enable explicitly
    return config_dict
