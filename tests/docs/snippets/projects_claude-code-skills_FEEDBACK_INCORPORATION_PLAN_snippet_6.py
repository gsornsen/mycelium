# Source: projects/claude-code-skills/FEEDBACK_INCORPORATION_PLAN.md
# Line: 1282
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Click commands
import click

@click.group()
def cli():
    """Mycelium Skills CLI"""
    pass

@cli.command()
@click.argument('skill_name')
def install(skill_name: str):
    """Install a skill from the repository."""
    loader = SkillLoader()
    loader.install(skill_name)
    click.echo(f"✅ Installed {skill_name}")

@cli.command()
@click.option('--format', type=click.Choice(['table', 'json']), default='table')
def list(format: str):
    """List installed skills."""
    registry = SkillRegistry()
    skills = registry.list()

    if format == 'json':
        click.echo(json.dumps(skills, indent=2))
    else:
        # Table output
        for skill in skills:
            click.echo(f"{skill['name']:<30} {skill['version']:<10} {skill['tier']}")

# Textual TUI
from textual.app import App
from textual.widgets import Header, Footer, DataTable, Static
from textual.containers import Container

class MyceliumTUI(App):
    """Interactive TUI for Mycelium Skills."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "skills", "Skills"),
        ("a", "analytics", "Analytics"),
    ]

    def compose(self):
        yield Header()
        yield Container(
            DataTable(id="skills_table"),
            Static(id="analytics_panel"),
        )
        yield Footer()

    def on_mount(self):
        table = self.query_one("#skills_table", DataTable)
        table.add_columns("Name", "Version", "Tier", "Status")

        # Load skills
        registry = SkillRegistry()
        for skill in registry.list():
            table.add_row(
                skill['name'],
                skill['version'],
                str(skill['tier']),
                "Active"
            )

if __name__ == '__main__':
    app = MyceliumTUI()
    app.run()