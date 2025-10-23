# Source: projects/onboarding/milestones/M07_CONFIGURATION_MANAGEMENT.md
# Line: 283
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/cli/config.py (continued)

import subprocess
import tempfile


@config.command()
@click.option(
    '--project',
    is_flag=True,
    help='Edit project-local configuration'
)
@click.option(
    '--editor',
    envvar='EDITOR',
    default='nano',
    help='Editor to use (default: $EDITOR or nano)'
)
def edit(project: bool, editor: str):
    """Edit configuration in your preferred editor."""

    try:
        # Load current configuration
        config = ConfigManager.load(prefer_project=project)
        config_path = ConfigManager.get_config_path(prefer_project=project)

    except FileNotFoundError:
        console.print("[yellow]⚠ No configuration found. Creating new one...[/yellow]")
        config = MyceliumConfig()
        config_path = ConfigManager.get_config_path(prefer_project=project)
        config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        tmp_path = Path(tmp.name)
        yaml_content = yaml.dump(
            config.model_dump(),
            default_flow_style=False,
            sort_keys=False
        )
        tmp.write(yaml_content)

    # Open in editor
    try:
        subprocess.run([editor, str(tmp_path)], check=True)

    except subprocess.CalledProcessError:
        console.print(f"[red]✗ Editor '{editor}' failed[/red]")
        tmp_path.unlink()
        raise click.Abort()

    except FileNotFoundError:
        console.print(f"[red]✗ Editor '{editor}' not found[/red]")
        console.print("[dim]Set EDITOR environment variable or use --editor[/dim]")
        tmp_path.unlink()
        raise click.Abort()

    # Load edited content
    try:
        edited_yaml = tmp_path.read_text()
        edited_dict = yaml.safe_load(edited_yaml)

        # Validate
        edited_config = MyceliumConfig(**edited_dict)

        # Save if valid
        ConfigManager.save(edited_config, project_local=project)

        console.print(f"[green]✓ Configuration saved to {config_path}[/green]")

    except yaml.YAMLError as e:
        console.print("[red]✗ Invalid YAML syntax:[/red]")
        console.print(str(e))
        console.print("\n[yellow]Configuration not saved. Fix errors and try again.[/yellow]")

    except Exception as e:
        console.print("[red]✗ Validation failed:[/red]")
        console.print(str(e))
        console.print("\n[yellow]Configuration not saved. Fix errors and try again.[/yellow]")

    finally:
        # Cleanup temp file
        tmp_path.unlink()
