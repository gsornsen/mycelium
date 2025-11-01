# Detection Screen Specification

## Purpose

Run service detection, display results, and allow user to re-run detection if needed.

## Layout

### During Detection

```
╔══════════════════════════════════════════════════════════════╗
║                  Detecting Services...                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ⏳ Scanning your system for available services...           ║
║                                                              ║
║  [████████████████░░░░░░░░░░] 60%                           ║
║                                                              ║
║  ✓ Docker detected                                           ║
║  ✓ Redis detected (port 6379)                               ║
║  ⏳ Checking PostgreSQL...                                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### After Detection

```
╔══════════════════════════════════════════════════════════════╗
║                  Detection Complete                          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Docker:       ✓ Available (v24.0.7)                         ║
║  Redis:        ✓ Available (v7.2, port 6379)                ║
║  PostgreSQL:   ✓ Available (v15.3, port 5432)               ║
║  Temporal:     ✗ Not detected                                ║
║  GPU:          ✓ Available (NVIDIA RTX 3090, 24GB)          ║
║                                                              ║
║  Detection time: 2.4s                                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

? What would you like to do?
  > Continue with detected services
    Re-run detection
    Back to welcome
```

## User Inputs

### Action Selection

- **Field**: `action`
- **Type**: Single selection (radio)
- **Options**:
  - `continue`: Continue with detected services
  - `rerun`: Re-run detection
  - `back`: Back to welcome screen
- **Default**: `continue`
- **Required**: Yes

## Detection Process

The detection screen performs the following steps:

1. **Initialize**: Display "Detecting Services..." header
1. **Run Detection**: Call `detect_all()` from M03 orchestrator
1. **Show Progress**: Display live progress as services are detected
1. **Display Results**: Show formatted results with icons
1. **Offer Actions**: Allow continue, re-run, or go back

## State Updates

On completion of this screen, update `WizardState`:

- `detection_results`: Store full DetectionSummary as dict
- `services_enabled`: Pre-populate based on detection:
  - `redis`: True if detected, False otherwise
  - `postgres`: True if detected, False otherwise
  - `temporal`: True if detected, False otherwise
- `redis_port`: Set to detected port if available
- `postgres_port`: Set to detected port if available
- `temporal_frontend_port`: Set to detected port if available
- `temporal_ui_port`: Set to detected port if available

## Validation

No user input validation required (selection-based interface).

## Help Text

### Detection Help

```
Service detection scans your system for:
• Docker daemon and version
• Redis instances on common ports (6379-6381)
• PostgreSQL instances on common ports (5432-5433)
• Temporal server on default ports
• Available GPUs (NVIDIA, AMD, Intel)

Detection is non-invasive and takes 2-5 seconds.
```

## Error Messages

### Detection Failed

```
⚠️  Detection encountered errors:

Docker: Connection failed - is Docker running?
Redis: Timeout on port scan
PostgreSQL: Permission denied

You can:
• Re-run detection after fixing issues
• Continue anyway and configure manually
• Exit wizard and fix issues
```

## Display Formatting

### Service Status Icons

- `✓`: Service detected and available
- `✗`: Service not detected
- `⚠️`: Service detected but has issues
- `⏳`: Detection in progress

### Version Display

- Show version if detected: `(v7.2)`
- Show "unknown" if available but version not detected: `(version unknown)`

### Port Display

- Show port if detected: `(port 6379)`
- Show multiple ports if multiple instances: `(ports 6379, 6380)`

### GPU Display

- Show vendor and model: `(NVIDIA RTX 3090)`
- Show memory if detected: `(NVIDIA RTX 3090, 24GB)`
- Show count if multiple: `(2x NVIDIA RTX 3090, 24GB each)`

## Next Step Logic

- **Continue** → Proceed to SERVICES screen
- **Re-run** → Re-run detection, stay on DETECTION screen
- **Back** → Return to WELCOME screen

## InquirerPy Implementation

```python
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from mycelium_onboarding.detection.orchestrator import detect_all

def detection_screen(state: WizardState) -> str:
    """Display detection screen and run service detection.

    Args:
        state: Current wizard state

    Returns:
        Selected action: "continue", "rerun", or "back"
    """
    # Display detection header
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                  Detecting Services...                       ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║                                                              ║")
    print("║  ⏳ Scanning your system for available services...           ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    # Run detection
    summary = detect_all()

    # Store detection results in state
    state.detection_results = {
        "docker": {
            "available": summary.has_docker,
            "version": summary.docker.version,
        },
        "redis": {
            "available": summary.has_redis,
            "instances": [
                {
                    "port": r.port,
                    "version": r.version,
                }
                for r in summary.redis if r.available
            ],
        },
        "postgres": {
            "available": summary.has_postgres,
            "instances": [
                {
                    "port": p.port,
                    "version": p.version,
                }
                for p in summary.postgres if p.available
            ],
        },
        "temporal": {
            "available": summary.has_temporal,
            "frontend_port": summary.temporal.frontend_port,
            "ui_port": summary.temporal.ui_port,
            "version": summary.temporal.version,
        },
        "gpu": {
            "available": summary.has_gpu,
            "count": len(summary.gpu.gpus),
            "total_memory_mb": summary.gpu.total_memory_mb,
        },
        "detection_time": summary.detection_time,
    }

    # Pre-populate service settings from detection
    if summary.has_redis and summary.redis:
        first_redis = next(r for r in summary.redis if r.available)
        state.services_enabled["redis"] = True
        state.redis_port = first_redis.port
    else:
        state.services_enabled["redis"] = False

    if summary.has_postgres and summary.postgres:
        first_postgres = next(p for p in summary.postgres if p.available)
        state.services_enabled["postgres"] = True
        state.postgres_port = first_postgres.port
    else:
        state.services_enabled["postgres"] = False

    if summary.has_temporal:
        state.services_enabled["temporal"] = True
        state.temporal_frontend_port = summary.temporal.frontend_port
        state.temporal_ui_port = summary.temporal.ui_port
    else:
        state.services_enabled["temporal"] = False

    # Display results
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                  Detection Complete                          ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║                                                              ║")

    # Format Docker status
    docker_status = "✓ Available" if summary.has_docker else "✗ Not detected"
    if summary.has_docker and summary.docker.version:
        docker_status += f" (v{summary.docker.version})"
    print(f"║  Docker:       {docker_status:<46} ║")

    # Format Redis status
    redis_status = "✓ Available" if summary.has_redis else "✗ Not detected"
    if summary.has_redis and summary.redis:
        first = next(r for r in summary.redis if r.available)
        if first.version:
            redis_status += f" (v{first.version}, port {first.port})"
        else:
            redis_status += f" (port {first.port})"
    print(f"║  Redis:        {redis_status:<46} ║")

    # Format PostgreSQL status
    postgres_status = "✓ Available" if summary.has_postgres else "✗ Not detected"
    if summary.has_postgres and summary.postgres:
        first = next(p for p in summary.postgres if p.available)
        if first.version:
            postgres_status += f" (v{first.version}, port {first.port})"
        else:
            postgres_status += f" (port {first.port})"
    print(f"║  PostgreSQL:   {postgres_status:<46} ║")

    # Format Temporal status
    temporal_status = "✓ Available" if summary.has_temporal else "✗ Not detected"
    if summary.has_temporal and summary.temporal.version:
        temporal_status += f" (v{summary.temporal.version})"
    print(f"║  Temporal:     {temporal_status:<46} ║")

    # Format GPU status
    gpu_status = "✗ Not detected"
    if summary.has_gpu and summary.gpu.gpus:
        gpu = summary.gpu.gpus[0]
        gpu_status = f"✓ Available ({gpu.vendor.value.upper()} {gpu.model}"
        if gpu.memory_mb:
            gpu_status += f", {gpu.memory_mb // 1024}GB"
        gpu_status += ")"
    print(f"║  GPU:          {gpu_status:<46} ║")

    print("║                                                              ║")
    print(f"║  Detection time: {summary.detection_time:.1f}s{' ' * 40}║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Get user action
    action = inquirer.select(
        message="What would you like to do?",
        choices=[
            Choice(value="continue", name="Continue with detected services"),
            Choice(value="rerun", name="Re-run detection"),
            Choice(value="back", name="Back to welcome"),
        ],
        default="continue",
    ).execute()

    # Handle re-run
    if action == "rerun":
        return detection_screen(state)

    return action
```

## Accessibility Notes

- Progress indication during detection
- Clear visual status indicators
- Keyboard navigation
- Screen reader friendly status text
- Non-blocking detection (with timeout)

## Performance Considerations

- Detection must complete in \< 5 seconds
- Individual detector timeouts prevent hanging
- Parallel detection for speed
- Graceful handling of network timeouts

## Design Rationale

This screen provides visibility into the detection process:

1. **Transparency**: Shows what's being detected in real-time
1. **Confidence**: Clear results build trust in the system
1. **Flexibility**: Allows re-running if issues occur
1. **Smart Defaults**: Pre-populates settings from detection
1. **Recovery**: Offers path back if user wants to change mode
