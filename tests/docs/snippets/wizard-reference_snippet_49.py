# Source: wizard-reference.md
# Line: 1046
# Valid syntax: True
# Has imports: False
# Has assignments: True

persistence = WizardStatePersistence()
if persistence.exists():
    print("Saved state found")