# Source: wizard-integration.md
# Line: 744
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Handle old state format gracefully
def _deserialize_state(self, data: dict) -> WizardState:
    # Provide defaults for new fields
    auto_start = data.get("auto_start", True)  # Default if missing
    enable_persistence = data.get("enable_persistence", True)