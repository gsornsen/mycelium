# Source: projects/onboarding/milestones/M04_INTERACTIVE_ONBOARDING.md
# Line: 65
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/wizard/flow.py
"""
Wizard flow design and orchestration.

Flow Sequence:
1. Welcome screen with system detection summary
2. Service selection (Redis, Postgres, Temporal, TaskQueue)
3. Service configuration (ports, persistence, memory limits)
4. Deployment method selection (Docker Compose, Justfile)
5. Project metadata (name, description)
6. Configuration review and confirmation
7. Write configuration and show next steps
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass

class WizardStep(str, Enum):
    WELCOME = "welcome"
    SERVICE_SELECTION = "service_selection"
    SERVICE_CONFIG = "service_config"
    DEPLOYMENT_METHOD = "deployment_method"
    PROJECT_METADATA = "project_metadata"
    REVIEW = "review"
    FINALIZE = "finalize"

@dataclass
class WizardState:
    """Maintains state across wizard steps."""
    current_step: WizardStep
    detection_results: Optional['DetectionResults'] = None
    selected_services: set[str] = None
    deployment_method: Optional[str] = None
    config: Optional['MyceliumConfig'] = None

    def can_proceed(self) -> bool:
        """Validate if current step is complete."""
        if self.current_step == WizardStep.SERVICE_SELECTION:
            return self.selected_services is not None
        elif self.current_step == WizardStep.DEPLOYMENT_METHOD:
            return self.deployment_method is not None
        return True

    def next_step(self) -> Optional[WizardStep]:
        """Determine next step in flow."""
        steps = list(WizardStep)
        current_idx = steps.index(self.current_step)
        if current_idx < len(steps) - 1:
            return steps[current_idx + 1]
        return None

def create_wizard_state(detection_results: 'DetectionResults') -> WizardState:
    """Initialize wizard state with detection results."""
    return WizardState(
        current_step=WizardStep.WELCOME,
        detection_results=detection_results,
        selected_services=set(),
    )