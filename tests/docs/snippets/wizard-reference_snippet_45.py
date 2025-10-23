# Source: wizard-reference.md
# Line: 975
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Use default XDG location
persistence = WizardStatePersistence()

# Use custom location
persistence = WizardStatePersistence(state_dir=Path("/tmp/state"))
