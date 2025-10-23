# Source: detection-reference.md
# Line: 182
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection import detect_all, update_config_from_detection
from mycelium_onboarding.config.manager import ConfigManager

# Detect services
summary = detect_all()

# Load existing config
manager = ConfigManager()
existing_config = manager.load()

# Update config with detected values
updated_config = update_config_from_detection(summary, existing_config)

# Save updated config
manager.save(updated_config)