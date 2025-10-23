# Source: wizard-reference.md
# Line: 541
# Valid syntax: True
# Has imports: False
# Has assignments: True

screens = WizardScreens(state)
services = screens.show_services()
# Returns: {"redis": True, "postgres": True, "temporal": False}