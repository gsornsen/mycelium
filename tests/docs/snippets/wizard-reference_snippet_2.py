# Source: wizard-reference.md
# Line: 66
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.wizard.flow import WizardStep

current_step = WizardStep.WELCOME
if current_step == WizardStep.WELCOME:
    print("Starting wizard")