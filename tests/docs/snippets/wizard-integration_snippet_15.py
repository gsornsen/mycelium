# Source: wizard-integration.md
# Line: 689
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Don't make users type everything
db_name = inquirer.text(
    message="Database name:",
    # No default - forces manual input
).execute()