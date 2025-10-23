# Source: wizard-reference.md
# Line: 778
# Valid syntax: True
# Has imports: False
# Has assignments: True

validator = WizardValidator(state)
if not validator.validate_postgres_database("my_db"):
    print("Invalid database name")
