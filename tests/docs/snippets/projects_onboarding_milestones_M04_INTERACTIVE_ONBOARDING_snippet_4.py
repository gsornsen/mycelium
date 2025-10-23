# Source: projects/onboarding/milestones/M04_INTERACTIVE_ONBOARDING.md
# Line: 355
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/wizard/integration.py
"""Integration between wizard and detection system."""

from mycelium_onboarding.detection.orchestrator import detect_all_services
from mycelium_onboarding.wizard.flow import WizardState, create_wizard_state
from mycelium_onboarding.wizard.screens import (
    show_welcome_screen,
    prompt_service_selection,
    prompt_deployment_method,
)

async def run_wizard_with_detection(use_cache: bool = True) -> 'MyceliumConfig':
    """Run full wizard flow with service detection."""

    # Step 1: Detect services (use cache if available)
    console.print("[dim]Detecting available services...[/dim]")
    detection_results = await detect_all_services(use_cache=use_cache)

    # Step 2: Initialize wizard state
    state = create_wizard_state(detection_results)

    # Step 3: Show welcome with detection summary
    show_welcome_screen(detection_results)

    # Step 4: Service selection
    state.selected_services = prompt_service_selection(detection_results)

    # Step 5: Deployment method
    state.deployment_method = prompt_deployment_method(
        has_docker=detection_results.docker.available
    )

    # Step 6: Project metadata
    metadata = prompt_project_metadata()

    # Step 7: Build configuration
    config = build_config_from_selections(
        selected_services=state.selected_services,
        deployment_method=state.deployment_method,
        project_name=metadata["name"],
        detection_results=detection_results,
    )

    # Step 8: Review and confirm
    confirmed = show_configuration_review(config)
    if not confirmed:
        console.print("[yellow]Configuration not saved. Exiting.[/yellow]")
        return None

    return config

def build_config_from_selections(
    selected_services: set[str],
    deployment_method: str,
    project_name: str,
    detection_results: 'DetectionResults',
) -> 'MyceliumConfig':
    """Build MyceliumConfig from wizard selections."""
    from mycelium_onboarding.config.schema import (
        MyceliumConfig,
        DeploymentConfig,
        ServicesConfig,
        RedisConfig,
        PostgresConfig,
    )

    # Create service configs based on selections
    redis_config = RedisConfig(
        enabled="redis" in selected_services,
        port=detection_results.redis.port if detection_results.redis.reachable else 6379,
    )

    postgres_config = PostgresConfig(
        enabled="postgres" in selected_services,
        port=detection_results.postgres.port if detection_results.postgres.reachable else 5432,
    )

    # Build full config
    config = MyceliumConfig(
        project_name=project_name,
        deployment=DeploymentConfig(method=deployment_method),
        services=ServicesConfig(
            redis=redis_config,
            postgres=postgres_config,
            # ... other services ...
        ),
    )

    return config