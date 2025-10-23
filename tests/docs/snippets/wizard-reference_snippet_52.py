# Source: wizard-reference.md
# Line: 1096
# Valid syntax: True
# Has imports: False
# Has assignments: True

persistence = WizardStatePersistence()
persistence.restore_from_backup(Path("/tmp/backup.json"))