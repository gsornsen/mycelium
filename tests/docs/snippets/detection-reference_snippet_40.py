# Source: detection-reference.md
# Line: 810
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection import detect_all, update_config_from_detection
from mycelium_onboarding.config.manager import ConfigManager

# Detect and update config
summary = detect_all()
config = update_config_from_detection(summary)

# Save config
manager = ConfigManager()
manager.save(config)