# Source: wizard-integration.md
# Line: 51
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.wizard.flow import WizardFlow, WizardState, WizardStep
from mycelium_onboarding.wizard.screens import WizardScreens
from mycelium_onboarding.wizard.validation import WizardValidator
from mycelium_onboarding.wizard.persistence import WizardStatePersistence
from mycelium_onboarding.config.manager import ConfigManager

def run_wizard_programmatically():
    """Run the wizard programmatically."""
    # Initialize components
    state = WizardState()
    flow = WizardFlow(state)
    screens = WizardScreens(state)
    validator = WizardValidator(state)
    persistence = WizardStatePersistence()

    try:
        # Check for saved state
        if persistence.exists():
            state = persistence.load()
            if state:
                flow = WizardFlow(state)
                screens = WizardScreens(state)
                validator = WizardValidator(state)
                print(f"Resuming from {state.current_step}")

        # Main wizard loop
        while not state.is_complete():
            # Persist state
            persistence.save(state)

            # Execute current step
            current_step = state.current_step

            if current_step == WizardStep.WELCOME:
                setup_mode = screens.show_welcome()
                state.setup_mode = setup_mode
                flow.advance()

            elif current_step == WizardStep.DETECTION:
                summary = screens.show_detection()
                state.detection_results = summary
                flow.advance()

            elif current_step == WizardStep.SERVICES:
                # Prompt for project name if not set
                if not state.project_name:
                    state.project_name = input("Project name: ").strip()

                services = screens.show_services()
                state.services_enabled = services
                flow.advance()

            elif current_step == WizardStep.DEPLOYMENT:
                deployment = screens.show_deployment()
                state.deployment_method = deployment

                # Handle mode-specific flow
                if state.setup_mode == "quick":
                    state.current_step = WizardStep.REVIEW
                else:
                    flow.advance()

            elif current_step == WizardStep.ADVANCED:
                screens.show_advanced()
                flow.advance()

            elif current_step == WizardStep.REVIEW:
                action = screens.show_review()

                if action == "confirm":
                    # Validate before saving
                    if not validator.validate_state():
                        print("Validation errors:")
                        for error in validator.get_error_messages():
                            print(f"  - {error}")
                        continue

                    # Generate and save configuration
                    config = state.to_config()
                    manager = ConfigManager()
                    manager.save(config)

                    # Mark complete
                    state.completed = True
                    state.current_step = WizardStep.COMPLETE
                    flow.advance()

                elif action.startswith("edit:"):
                    # Jump to step for editing
                    edit_step = action.split(":")[1]
                    state.current_step = WizardStep(edit_step)

                elif action == "cancel":
                    print("Wizard cancelled")
                    return None

            elif current_step == WizardStep.COMPLETE:
                config_path = manager._determine_save_path()
                screens.show_complete(str(config_path))
                break

        # Clear saved state on success
        persistence.clear()
        return state

    except KeyboardInterrupt:
        print("\nWizard interrupted. Run again with resume.")
        persistence.save(state)
        return None
    except Exception as e:
        print(f"Error: {e}")
        persistence.save(state)
        raise

# Usage
if __name__ == "__main__":
    final_state = run_wizard_programmatically()
    if final_state:
        print(f"Wizard completed! Project: {final_state.project_name}")