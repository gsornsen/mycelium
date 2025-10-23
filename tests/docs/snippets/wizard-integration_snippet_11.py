# Source: wizard-integration.md
# Line: 644
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Don't modify state without validation
state.postgres_database = user_input  # Could be invalid!

# DO validate first
validator = WizardValidator(state)
if validator.validate_postgres_database(user_input):
    state.postgres_database = user_input
