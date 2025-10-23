# Source: migration-guide.md
# Line: 392
# Valid syntax: True
# Has imports: False
# Has assignments: True

def migrate(self, config_dict: dict[str, Any]) -> dict[str, Any]:
    # BAD: Overwrites user customization
    config_dict["redis"]["port"] = 6379

    # GOOD: Preserves existing value
    if "redis" not in config_dict:
        config_dict["redis"] = {}
    if "port" not in config_dict["redis"]:
        config_dict["redis"]["port"] = 6379

    return config_dict
