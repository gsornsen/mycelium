# Source: wizard-reference.md
# Line: 1018
# Valid syntax: True
# Has imports: False
# Has assignments: True

persistence = WizardStatePersistence()
state = persistence.load()
if state:
    print(f"Resuming from {state.current_step}")
