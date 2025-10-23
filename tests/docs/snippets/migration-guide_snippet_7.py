# Source: migration-guide.md
# Line: 465
# Valid syntax: True
# Has imports: True
# Has assignments: True

import logging

logger = logging.getLogger(__name__)

def migrate(self, config_dict: dict[str, Any]) -> dict[str, Any]:
    logger.info("Adding monitoring configuration")

    config_dict["monitoring"] = {
        "enabled": False,
        "metrics_port": 9090,
    }

    logger.debug("Monitoring config: %s", config_dict["monitoring"])

    return config_dict
