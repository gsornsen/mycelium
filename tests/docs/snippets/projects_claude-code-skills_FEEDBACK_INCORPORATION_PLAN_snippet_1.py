# Source: projects/claude-code-skills/FEEDBACK_INCORPORATION_PLAN.md
# Line: 138
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Text command example
@click.command()
@click.argument('skill_name')
def install(skill_name: str):
    """Install a skill from the repository."""
    loader = SkillLoader()
    loader.install(skill_name)