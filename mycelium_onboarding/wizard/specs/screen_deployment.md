# Deployment Screen Specification

## Purpose
Select deployment method and configure basic deployment settings.

## Layout
```
╔══════════════════════════════════════════════════════════════╗
║                  Deployment Configuration                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Choose how you want to deploy your services:               ║
║                                                              ║
║  • Docker Compose: Simple, single-host deployment           ║
║    Status: Docker detected ✓                                ║
║                                                              ║
║  • Kubernetes: Multi-host, production-grade orchestration   ║
║    Status: kubectl not detected                             ║
║                                                              ║
║  • systemd: Native Linux service management                 ║
║    Status: systemd available                                ║
║                                                              ║
║  • Manual: Self-managed deployment                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

? Select deployment method:
  > Docker Compose (recommended) ✓
    Kubernetes
    systemd
    Manual
```

## User Inputs

### Deployment Method Selection
- **Field**: `deployment_method`
- **Type**: Single selection (radio)
- **Options**:
  - `docker-compose`: Docker Compose (recommended)
  - `kubernetes`: Kubernetes
  - `systemd`: systemd services
  - `manual`: Manual deployment
- **Default**: `docker-compose` if Docker detected, else `manual`
- **Required**: Yes

### Auto-start Services
- **Field**: `auto_start`
- **Type**: Boolean (yes/no)
- **Default**: `true`
- **Description**: Automatically start services after deployment
- **Only shown if**: deployment_method in ['docker-compose', 'systemd']

## Validation

### Deployment Method
No validation required (selection-based).

### Docker Compose Prerequisites
```python
if deployment_method == "docker-compose":
    if not detection_results.get("docker", {}).get("available"):
        warnings.append(
            "⚠️  Docker not detected. Install Docker to use Docker Compose deployment."
        )
```

### Kubernetes Prerequisites
```python
if deployment_method == "kubernetes":
    # Check if kubectl is available
    result = subprocess.run(
        ["which", "kubectl"],
        capture_output=True,
        timeout=2
    )
    if result.returncode != 0:
        warnings.append(
            "⚠️  kubectl not found. Install kubectl to use Kubernetes deployment."
        )
```

## Help Text

### Docker Compose
```
Docker Compose (Recommended)
═══════════════════════════════════════════════════════════

Best for:
• Local development
• Single-host deployments
• Getting started quickly
• Testing and experimentation

Requirements:
• Docker Engine installed
• Docker Compose plugin (included in recent Docker versions)

Generated files:
• docker-compose.yml - Service definitions
• .env - Environment variables
• volumes/ - Persistent data

Commands:
• docker compose up -d    - Start services
• docker compose down     - Stop services
• docker compose logs     - View logs
```

### Kubernetes
```
Kubernetes
═══════════════════════════════════════════════════════════

Best for:
• Production deployments
• Multi-host clusters
• High availability
• Auto-scaling requirements

Requirements:
• kubectl installed and configured
• Access to a Kubernetes cluster
• Basic Kubernetes knowledge

Generated files:
• k8s/namespace.yaml       - Namespace definition
• k8s/configmap.yaml       - Configuration
• k8s/deployment.yaml      - Service deployments
• k8s/service.yaml         - Service definitions
• k8s/persistent-volume.yaml - Storage

Commands:
• kubectl apply -f k8s/    - Deploy services
• kubectl get pods         - Check status
• kubectl logs <pod>       - View logs
```

### systemd
```
systemd
═══════════════════════════════════════════════════════════

Best for:
• Native Linux deployments
• System-level service management
• Boot-time startup
• Integration with system logging

Requirements:
• systemd-based Linux distribution
• sudo/root access for service installation
• Services installed via package manager

Generated files:
• systemd/mycelium-redis.service
• systemd/mycelium-postgres.service
• systemd/mycelium-temporal.service

Commands:
• sudo systemctl start mycelium-*   - Start services
• sudo systemctl enable mycelium-*  - Enable at boot
• sudo journalctl -u mycelium-*     - View logs
```

### Manual
```
Manual Deployment
═══════════════════════════════════════════════════════════

Best for:
• Custom deployment scenarios
• Existing infrastructure integration
• Non-standard environments
• Learning and experimentation

Requirements:
• Manual service management
• Custom configuration

Generated files:
• config/mycelium.yaml     - Configuration file
• scripts/start.sh         - Helper start script
• scripts/stop.sh          - Helper stop script
• README.md                - Deployment instructions

You will need to:
• Install and configure services manually
• Start services using your preferred method
• Configure service discovery and networking
```

## Error Messages

### Docker Not Available
```
⚠️  Docker not detected

Docker Compose requires Docker to be installed and running.

Options:
1. Install Docker: https://docs.docker.com/get-docker/
2. Choose a different deployment method
3. Exit wizard and install Docker first

Would you still like to continue with Docker Compose?
This will generate configuration files, but deployment will
fail until Docker is installed.
```

### Kubectl Not Found
```
⚠️  kubectl not found

Kubernetes deployment requires kubectl to be installed.

Options:
1. Install kubectl: https://kubernetes.io/docs/tasks/tools/
2. Choose a different deployment method
3. Exit wizard and install kubectl first

Would you still like to continue with Kubernetes?
This will generate configuration files, but you'll need
to install kubectl before deploying.
```

### systemd Not Available
```
⚠️  systemd not detected

This system doesn't appear to be using systemd.

Options:
1. Choose a different deployment method
2. Use Manual deployment for custom setup

systemd deployment will not work on this system.
```

## State Updates

On completion of this screen, update `WizardState`:
- `deployment_method`: Selected deployment method
- `auto_start`: Auto-start preference (if applicable)

## Next Step Logic

- **Quick Setup Mode** → Proceed directly to REVIEW screen (skip ADVANCED)
- **Custom Setup Mode** → Proceed to ADVANCED screen
- **Back** → Return to SERVICES screen

## InquirerPy Implementation

```python
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
import subprocess

def deployment_screen(state: WizardState) -> str:
    """Display deployment configuration screen.

    Args:
        state: Current wizard state

    Returns:
        Action: "continue" or "back"
    """
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                  Deployment Configuration                    ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║                                                              ║")
    print("║  Choose how you want to deploy your services.               ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Check prerequisites
    docker_available = (
        state.detection_results
        and state.detection_results.get("docker", {}).get("available")
    )

    kubectl_available = False
    try:
        result = subprocess.run(
            ["which", "kubectl"],
            capture_output=True,
            timeout=2,
        )
        kubectl_available = result.returncode == 0
    except Exception:
        pass

    systemd_available = False
    try:
        result = subprocess.run(
            ["which", "systemctl"],
            capture_output=True,
            timeout=2,
        )
        systemd_available = result.returncode == 0
    except Exception:
        pass

    # Build deployment method choices with status
    choices = []

    # Docker Compose
    docker_status = " ✓" if docker_available else " (Docker not detected)"
    choices.append(
        Choice(
            value="docker-compose",
            name=f"Docker Compose (recommended){docker_status}",
        )
    )

    # Kubernetes
    k8s_status = " ✓" if kubectl_available else " (kubectl not found)"
    choices.append(
        Choice(
            value="kubernetes",
            name=f"Kubernetes{k8s_status}",
        )
    )

    # systemd
    systemd_status = " ✓" if systemd_available else " (systemd not detected)"
    choices.append(
        Choice(
            value="systemd",
            name=f"systemd{systemd_status}",
        )
    )

    # Manual
    choices.append(
        Choice(
            value="manual",
            name="Manual (self-managed)",
        )
    )

    # Select deployment method
    deployment_method = inquirer.select(
        message="Select deployment method:",
        choices=choices,
        default=state.deployment_method or ("docker-compose" if docker_available else "manual"),
        long_instruction="Use arrow keys to navigate, Enter to select, ? for help",
    ).execute()

    state.deployment_method = deployment_method

    # Show warning if prerequisites not met
    if deployment_method == "docker-compose" and not docker_available:
        print()
        print("⚠️  Warning: Docker not detected")
        print()
        print("Docker Compose requires Docker to be installed and running.")
        print("Configuration files will be generated, but deployment will")
        print("fail until Docker is installed.")
        print()

        continue_anyway = inquirer.confirm(
            message="Continue with Docker Compose anyway?",
            default=True,
        ).execute()

        if not continue_anyway:
            # Recursively call to re-select
            return deployment_screen(state)

    elif deployment_method == "kubernetes" and not kubectl_available:
        print()
        print("⚠️  Warning: kubectl not found")
        print()
        print("Kubernetes deployment requires kubectl to be installed.")
        print("Configuration files will be generated, but you'll need")
        print("kubectl installed before deploying.")
        print()

        continue_anyway = inquirer.confirm(
            message="Continue with Kubernetes anyway?",
            default=True,
        ).execute()

        if not continue_anyway:
            # Recursively call to re-select
            return deployment_screen(state)

    elif deployment_method == "systemd" and not systemd_available:
        print()
        print("⚠️  Error: systemd not available")
        print()
        print("This system doesn't appear to be using systemd.")
        print("Please choose a different deployment method.")
        print()

        inquirer.confirm(
            message="Press Enter to go back",
            default=True,
        ).execute()

        # Recursively call to re-select
        return deployment_screen(state)

    # Auto-start configuration (only for docker-compose and systemd)
    if deployment_method in ["docker-compose", "systemd"]:
        print()
        auto_start = inquirer.confirm(
            message="Automatically start services after deployment?",
            default=state.auto_start,
            long_instruction="Services will start immediately after configuration",
        ).execute()

        state.auto_start = auto_start

    # Navigation
    print()
    action = inquirer.select(
        message="What would you like to do?",
        choices=[
            {"name": "Continue", "value": "continue"},
            {"name": "Back to services", "value": "back"},
        ],
        default="continue",
    ).execute()

    return action
```

## Accessibility Notes

- Clear status indicators for prerequisites
- Warnings for missing prerequisites
- Comprehensive help text for each method
- Keyboard navigation
- Graceful handling of missing tools
- Option to continue anyway (for CI/planning)

## Design Rationale

This screen guides deployment decisions:

1. **Context-Aware**: Shows status of available tools
2. **Recommended Choice**: Highlights Docker Compose as default
3. **Informed Decisions**: Comprehensive help for each method
4. **Graceful Degradation**: Allows continuing even with warnings
5. **Flexibility**: Supports multiple deployment paradigms
6. **Educational**: Explains requirements and tradeoffs
