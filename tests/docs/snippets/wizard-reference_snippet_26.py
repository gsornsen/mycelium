# Source: wizard-reference.md
# Line: 621
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: expected an indented block after 'if' statement on line 4 (<unknown>, line 6)

screens = WizardScreens(state)
action = screens.show_review()

if action == "confirm":
    # Save configuration
elif action.startswith("edit:"):
    step = action.split(":")[1]
    # Jump to step for editing