# Source: wizard-reference.md
# Line: 1155
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.wizard.persistence import WizardStatePersistence

persistence = WizardStatePersistence()

if persistence.exists():
    state = persistence.load()
    if state:
        print(f"Resuming from {state.current_step}")
        # Continue wizard with loaded state
    else:
        print("Saved state corrupted, starting fresh")
        state = WizardState()
else:
    state = WizardState()