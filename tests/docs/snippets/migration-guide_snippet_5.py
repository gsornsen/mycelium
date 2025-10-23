# Source: migration-guide.md
# Line: 431
# Valid syntax: True
# Has imports: False
# Has assignments: True

def migrate(self, config_dict: dict[str, Any]) -> dict[str, Any]:
    # Rename field while preserving value
    if "deployment" in config_dict:
        if "log_level" in config_dict["deployment"]:
            # Get old value
            old_value = config_dict["deployment"].pop("log_level")
            # Set new field with old value
            config_dict["deployment"]["logging_level"] = old_value

    return config_dict