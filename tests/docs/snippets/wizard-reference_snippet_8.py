# Source: wizard-reference.md
# Line: 250
# Valid syntax: True
# Has imports: False
# Has assignments: True

state = WizardState()
state.project_name = "my-project"
state.services_enabled = {"redis": True, "postgres": True, "temporal": False}
state.postgres_database = "my_db"

config = state.to_config()
# Returns MyceliumConfig instance
