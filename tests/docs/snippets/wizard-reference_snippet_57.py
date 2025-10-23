# Source: wizard-reference.md
# Line: 1222
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.wizard.flow import WizardState

# Serialize to dict
state = WizardState()
state_dict = state.to_dict()

# Save to JSON
import json

with open("state.json", "w") as f:
    json.dump(state_dict, f)

# Load from dict
with open("state.json") as f:
    loaded_dict = json.load(f)
loaded_state = WizardState.from_dict(loaded_dict)
