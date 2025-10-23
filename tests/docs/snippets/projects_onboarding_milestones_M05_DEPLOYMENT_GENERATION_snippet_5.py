# Source: projects/onboarding/milestones/M05_DEPLOYMENT_GENERATION.md
# Line: 942
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/cli/generate.py
"""CLI command for deployment generation."""

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from mycelium_onboarding.config.manager import ConfigManager
from mycelium_onboarding.generators.docker_compose import DockerComposeGenerator
from mycelium_onboarding.generators.justfile import JustfileGenerator
from mycelium_onboarding.generators.secrets import generate_env_file

console = Console()

@click.command()
@click.option(
    '--method',
    type=click.Choice(['docker-compose', 'justfile'], case_sensitive=False),
    help='Deployment method (auto-detected if not specified)'
)
@click.option(
    '--output',
    type=click.Path(),
    default='.',
    help='Output directory for generated files'
)
@click.option(
    '--force',
    is_flag=True,
    help='Overwrite existing files'
)
@click.option(
    '--no-secrets',
    is_flag=True,
    help='Skip .env file generation'
)
def generate(method: str, output: str, force: bool, no_secrets: bool):
    """Generate deployment files from configuration."""

    # Load configuration
    try:
        config = ConfigManager.load()
    except FileNotFoundError:
        console.print("[red]✗ No configuration found. Run /mycelium-onboarding first.[/red]")
        raise click.Abort()

    # Determine deployment method
    if method is None:
        method = config.deployment.method

    output_dir = Path(output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[cyan]Generating {method} deployment...[/cyan]\n")

    # Generate based on method
    generated_files = []

    if method == 'docker-compose':
        generator = DockerComposeGenerator()

        compose_file = output_dir / 'docker-compose.yml'
        generator.generate_to_file(config, compose_file, overwrite=force)
        generated_files.append(compose_file)

        env_example = output_dir / '.env.example'
        env_example.write_text(generator.generate_env_example(config))
        generated_files.append(env_example)

    elif method == 'justfile':
        generator = JustfileGenerator()

        justfile = output_dir / 'Justfile'
        generator.generate_to_file(config, justfile, overwrite=force)
        generated_files.append(justfile)

        scripts = generator.generate_service_scripts(config, output_dir / 'bin')
        generated_files.extend(scripts)

    # Generate .env file with secrets
    if not no_secrets:
        env_file = output_dir / '.env'
        generate_env_file(config, env_file, overwrite=force)
        generated_files.append(env_file)

    # Show success message
    console.print(Panel(
        f"[bold green]✓ Deployment files generated![/bold green]\n\n"
        f"Output directory: [cyan]{output_dir}[/cyan]\n\n"
        f"Generated files:\n" +
        "\n".join(f"  • {f.relative_to(output_dir)}" for f in generated_files) +
        f"\n\nNext steps:\n"
        f"1. Review generated files\n"
        f"2. Start services: [bold]just up[/bold] or [bold]docker-compose up[/bold]\n"
        f"3. Test coordination: [bold]/mycelium-test[/bold]",
        border_style="green"
    ))

if __name__ == '__main__':
    generate()