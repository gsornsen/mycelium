# Source: projects/onboarding/ORIGINAL_PLAN.md
# Line: 93
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: invalid syntax. Perhaps you forgot a comma? (<unknown>, line 10)

# ~/.claude/plugins/mycelium-core/lib/onboarding/cli.py
import click
from InquirerPy import inquirer

@click.command()
def onboard():
    services = detect_services()
    selected = inquirer.checkbox(
        message="Select services to enable:",
        choices=[...detected_services]
    ).execute()

    deployment = inquirer.select(
        message="Choose deployment method:",
        choices=["Docker Compose", "Baremetal (Justfile)", "Baremetal (Procfile)"]
    ).execute()

    # Continue configuration...