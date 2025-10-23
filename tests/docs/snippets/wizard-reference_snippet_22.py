# Source: wizard-reference.md
# Line: 513
# Valid syntax: True
# Has imports: False
# Has assignments: True

screens = WizardScreens(state)
summary = screens.show_detection()
print(f"Detected services: {summary.has_redis}, {summary.has_postgres}")
