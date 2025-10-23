# Source: projects/onboarding/ORIGINAL_PLAN.md
# Line: 77
# Valid syntax: True
# Has imports: True
# Has assignments: False

# ~/.claude/plugins/mycelium-core/lib/onboarding/tui.py
from textual.app import App
from textual.widgets import Checkbox, Button, SelectionList

class MyceliumOnboarding(App):
    def compose(self):
        yield Header()
        yield ServiceSelector(detected_services)
        yield DeploymentMethodSelector()
        yield EnvironmentIsolationSelector()
        yield ProgressView()
        yield Footer()