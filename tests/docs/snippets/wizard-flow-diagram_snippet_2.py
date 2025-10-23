# Source: wizard-flow-diagram.md
# Line: 388
# Valid syntax: True
# Has imports: False
# Has assignments: False

def can_proceed_to(self, step: WizardStep) -> bool:
    if step == WizardStep.SERVICES:
        return self.detection_results is not None

    if step == WizardStep.REVIEW:
        return (
            bool(self.project_name) and
            any(self.services_enabled.values())
        )

    if step == WizardStep.COMPLETE:
        return self.completed

    return True
