# Source: wizard-reference.md
# Line: 1077
# Valid syntax: True
# Has imports: False
# Has assignments: True

persistence = WizardStatePersistence()
backup_path = persistence.backup()
if backup_path:
    print(f"Backed up to {backup_path}")
