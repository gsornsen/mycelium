# Source: migration-guide.md
# Line: 410
# Valid syntax: True
# Has imports: False
# Has assignments: True

def migrate(self, config_dict: dict[str, Any]) -> dict[str, Any]:
    # Check if section exists
    if "deployment" in config_dict:
        # Safe to access
        if "auto_start" not in config_dict["deployment"]:
            config_dict["deployment"]["auto_start"] = True
    else:
        # Create section with defaults
        config_dict["deployment"] = {
            "method": "docker-compose",
            "auto_start": True,
        }

    return config_dict