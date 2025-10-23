# Source: wizard-reference.md
# Line: 1105
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.wizard.flow import WizardFlow, WizardState, WizardStep
from mycelium_onboarding.wizard.persistence import WizardStatePersistence
from mycelium_onboarding.wizard.screens import WizardScreens
from mycelium_onboarding.wizard.validation import WizardValidator

# Initialize
state = WizardState()
flow = WizardFlow(state)
screens = WizardScreens(state)
validator = WizardValidator(state)
persistence = WizardStatePersistence()

# Main wizard loop
while not state.is_complete():
    # Save state for resume
    persistence.save(state)

    current_step = state.current_step

    if current_step == WizardStep.WELCOME:
        setup_mode = screens.show_welcome()
        state.setup_mode = setup_mode
        flow.advance()

    elif current_step == WizardStep.DETECTION:
        summary = screens.show_detection()
        flow.advance()

    elif current_step == WizardStep.SERVICES:
        services = screens.show_services()
        flow.advance()

    elif current_step == WizardStep.REVIEW:
        action = screens.show_review()
        if action == "confirm":
            if validator.validate_state():
                config = state.to_config()
                # Save config
                flow.mark_complete()
        elif action.startswith("edit:"):
            step = action.split(":")[1]
            flow.jump_to(WizardStep(step))

# Clear saved state on completion
persistence.clear()
