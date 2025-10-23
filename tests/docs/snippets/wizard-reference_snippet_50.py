# Source: wizard-reference.md
# Line: 1060
# Valid syntax: True
# Has imports: False
# Has assignments: True

persistence = WizardStatePersistence()
path = persistence.get_state_path()
print(f"State file: {path}")
