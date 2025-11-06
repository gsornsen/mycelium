# Complete Screen Specification

## Purpose

Show success message, generated files, and next steps after configuration is complete.

## Layout

```
╔══════════════════════════════════════════════════════════════╗
║                    🎉 Setup Complete! 🎉                     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Your Mycelium environment is configured and ready to go!   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generated Files
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✓ Configuration saved:
    ~/.config/mycelium/mycelium.yaml

  ✓ Docker Compose configuration:
    docker-compose.yml
    .env

  ✓ Documentation:
    README-MYCELIUM.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Next Steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Start your services:
     $ docker compose up -d

  2. Verify services are running:
     $ docker compose ps

  3. Check service health:
     $ mycelium-onboard health check

  4. View logs:
     $ docker compose logs -f

  5. Read the documentation:
     $ cat README-MYCELIUM.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Useful Commands
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  View configuration:
    $ mycelium-onboard config show

  Update configuration:
    $ mycelium-onboard config edit

  Re-run wizard:
    $ mycelium-onboard wizard

  Get help:
    $ mycelium-onboard --help

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Service URLs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Redis:          localhost:6379
  PostgreSQL:     localhost:5432
  Temporal UI:    http://localhost:8080

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Need help? Visit: https://github.com/gsornsen/mycelium
Report issues: https://github.com/gsornsen/mycelium/issues

Press Enter to exit...
```

## Display Sections

### Success Banner

- Celebratory message with emojis
- Confirmation that setup is complete
- Welcoming tone

### Generated Files

- List of all files created during wizard
- Full paths to each file
- Checkmarks to indicate success
- File descriptions

### Next Steps

Numbered list of immediate actions:

1. Start services (deployment-specific command)
1. Verify services are running
1. Check service health
1. View logs
1. Read documentation

### Useful Commands

Common commands the user will need:

- Configuration management
- Service management
- Getting help
- Re-running wizard

### Service URLs

- Connection URLs for each enabled service
- Web UI URLs where applicable
- Ready to copy-paste

### Support Links

- Documentation URL
- GitHub repository
- Issue tracker
- Community resources

## Deployment-Specific Next Steps

### Docker Compose

```
Next Steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Start your services:
     $ docker compose up -d

  2. Verify services are running:
     $ docker compose ps

  3. View logs:
     $ docker compose logs -f

  4. Stop services:
     $ docker compose down
```

### Kubernetes

```
Next Steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Apply Kubernetes manifests:
     $ kubectl apply -f k8s/

  2. Check pod status:
     $ kubectl get pods -n mycelium

  3. View logs:
     $ kubectl logs -f -n mycelium <pod-name>

  4. Port forward to access services:
     $ kubectl port-forward -n mycelium <pod-name> 6379:6379
```

### systemd

```
Next Steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Install systemd units:
     $ sudo cp systemd/*.service /etc/systemd/system/
     $ sudo systemctl daemon-reload

  2. Start services:
     $ sudo systemctl start mycelium-*

  3. Enable at boot:
     $ sudo systemctl enable mycelium-*

  4. Check status:
     $ sudo systemctl status mycelium-*
```

### Manual

```
Next Steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Review the generated configuration:
     $ cat ~/.config/mycelium/mycelium.yaml

  2. Install required services:
     - Redis: https://redis.io/docs/getting-started/
     - PostgreSQL: https://www.postgresql.org/download/
     - Temporal: https://docs.temporal.io/install

  3. Start services using your preferred method

  4. Update connection settings if needed:
     $ mycelium-onboard config edit
```

## Auto-Start Behavior

If `auto_start` is enabled and deployment method supports it:

```
Starting services...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ⏳ Starting Redis...         [  OK  ] (2.1s)
  ⏳ Starting PostgreSQL...    [  OK  ] (3.4s)
  ⏳ Starting Temporal...      [  OK  ] (5.2s)

All services started successfully! ✓

Waiting for health checks...

  ✓ Redis:        Healthy (127.0.0.1:6379)
  ✓ PostgreSQL:   Healthy (127.0.0.1:5432)
  ✓ Temporal:     Healthy (127.0.0.1:7233)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Error Handling

### File Generation Errors

```
⚠️  Warning: Some files could not be created

  ✓ Configuration saved:      ~/.config/mycelium/mycelium.yaml
  ✗ Docker Compose failed:    docker-compose.yml
    Error: Permission denied

  Partial setup completed. Please check errors above.
```

### Auto-Start Errors

```
⚠️  Warning: Some services failed to start

  ✓ Redis:        Started successfully
  ✗ PostgreSQL:   Failed to start
    Error: Port 5432 already in use
  ✗ Temporal:     Failed to start
    Error: Requires PostgreSQL

  You can manually start services after fixing the issues.
```

## State Updates

On this screen:

- Set `completed` = True
- Set `current_step` = COMPLETE
- Save final state to disk (if save feature enabled)

## User Actions

### Exit

- Press Enter to exit
- No further navigation available
- Wizard session ends

### Optional Actions

If enabled in implementation:

- View generated files
- Start services now
- Open documentation
- Run health check

## InquirerPy Implementation

```python
from InquirerPy import inquirer
from pathlib import Path
import subprocess

def complete_screen(state: WizardState, generated_files: dict[str, Path]) -> None:
    """Display completion screen with success message and next steps.

    Args:
        state: Final wizard state
        generated_files: Dict mapping file types to paths of generated files
    """
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                    🎉 Setup Complete! 🎉                     ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║                                                              ║")
    print("║  Your Mycelium environment is configured and ready to go!   ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Generated Files
    print("━" * 64)
    print("Generated Files")
    print("━" * 64)
    print()

    for file_type, file_path in generated_files.items():
        if file_path.exists():
            print(f"  ✓ {file_type}:")
            print(f"    {file_path}")
            print()
        else:
            print(f"  ✗ {file_type}:")
            print(f"    {file_path} (not created)")
            print()

    # Next Steps
    print("━" * 64)
    print("Next Steps")
    print("━" * 64)
    print()

    if state.deployment_method == "docker-compose":
        print("  1. Start your services:")
        print("     $ docker compose up -d")
        print()
        print("  2. Verify services are running:")
        print("     $ docker compose ps")
        print()
        print("  3. Check service health:")
        print("     $ mycelium-onboard health check")
        print()
        print("  4. View logs:")
        print("     $ docker compose logs -f")
        print()

    elif state.deployment_method == "kubernetes":
        print("  1. Apply Kubernetes manifests:")
        print("     $ kubectl apply -f k8s/")
        print()
        print("  2. Check pod status:")
        print(f"     $ kubectl get pods -n {state.project_name}")
        print()
        print("  3. View logs:")
        print(f"     $ kubectl logs -f -n {state.project_name} <pod-name>")
        print()

    elif state.deployment_method == "systemd":
        print("  1. Install systemd units:")
        print("     $ sudo cp systemd/*.service /etc/systemd/system/")
        print("     $ sudo systemctl daemon-reload")
        print()
        print("  2. Start services:")
        print("     $ sudo systemctl start mycelium-*")
        print()
        print("  3. Enable at boot:")
        print("     $ sudo systemctl enable mycelium-*")
        print()

    elif state.deployment_method == "manual":
        print("  1. Review the generated configuration:")
        print(f"     $ cat {generated_files.get('config', '')}")
        print()
        print("  2. Install and start services manually")
        print()
        print("  3. Refer to README-MYCELIUM.md for details")
        print()

    print("  5. Read the documentation:")
    print("     $ cat README-MYCELIUM.md")
    print()

    # Useful Commands
    print("━" * 64)
    print("Useful Commands")
    print("━" * 64)
    print()
    print("  View configuration:")
    print("    $ mycelium-onboard config show")
    print()
    print("  Update configuration:")
    print("    $ mycelium-onboard config edit")
    print()
    print("  Re-run wizard:")
    print("    $ mycelium-onboard wizard")
    print()
    print("  Get help:")
    print("    $ mycelium-onboard --help")
    print()

    # Service URLs
    print("━" * 64)
    print("Service URLs")
    print("━" * 64)
    print()

    if state.services_enabled.get("redis"):
        print(f"  Redis:          localhost:{state.redis_port}")

    if state.services_enabled.get("postgres"):
        print(f"  PostgreSQL:     localhost:{state.postgres_port}")

    if state.services_enabled.get("temporal"):
        print(f"  Temporal UI:    http://localhost:{state.temporal_ui_port}")

    print()

    # Support
    print("━" * 64)
    print()
    print("Need help? Visit: https://github.com/gsornsen/mycelium")
    print("Report issues: https://github.com/gsornsen/mycelium/issues")
    print()
    print("━" * 64)
    print()

    # Wait for user to exit
    inquirer.text(
        message="Press Enter to exit...",
        default="",
        mandatory=False,
    ).execute()


def start_services_if_enabled(state: WizardState) -> dict[str, bool]:
    """Start services if auto_start is enabled.

    Args:
        state: Wizard state with auto_start setting

    Returns:
        Dict mapping service names to start success status
    """
    if not state.auto_start:
        return {}

    if state.deployment_method != "docker-compose":
        return {}

    print()
    print("Starting services...")
    print("━" * 64)
    print()

    results = {}

    try:
        # Start services with docker compose
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            print("  ✓ All services started successfully!")
            results["all"] = True
        else:
            print(f"  ✗ Failed to start services: {result.stderr}")
            results["all"] = False

    except subprocess.TimeoutExpired:
        print("  ✗ Timeout while starting services")
        results["all"] = False
    except Exception as e:
        print(f"  ✗ Error starting services: {e}")
        results["all"] = False

    print()
    print("━" * 64)
    print()

    return results
```

## Accessibility Notes

- Clear success indicators
- Structured information hierarchy
- Copyable commands
- Full paths provided
- Support links easily accessible
- Keyboard-only interaction for exit

## Design Rationale

This screen provides closure and guidance:

1. **Celebration**: Success message provides positive reinforcement
1. **Transparency**: Shows exactly what was created
1. **Actionable**: Provides concrete next steps
1. **Educational**: Commands teach how to use the system
1. **Support**: Easy access to help resources
1. **Deployment-Aware**: Instructions match chosen method
1. **URLs Ready**: Connection strings ready to use
1. **Reference**: Can be used as future reference guide
