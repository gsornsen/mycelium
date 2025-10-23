# Source: wizard-reference.md
# Line: 44
# Valid syntax: True
# Has imports: False
# Has assignments: True

class WizardStep(str, Enum):
    """Wizard steps in order."""
    WELCOME = "welcome"
    DETECTION = "detection"
    SERVICES = "services"
    DEPLOYMENT = "deployment"
    ADVANCED = "advanced"
    REVIEW = "review"
    COMPLETE = "complete"
