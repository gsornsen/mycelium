# Source: wizard-integration.md
# Line: 679
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Provide defaults based on context
default_db = state.project_name.lower().replace("-", "_")
db_name = inquirer.text(
    message="Database name:",
    default=default_db,
).execute()