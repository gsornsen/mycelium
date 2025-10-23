# Source: wizard-flow-diagram.md
# Line: 443
# Valid syntax: True
# Has imports: False
# Has assignments: True

def test_quick_setup_flow():
    flow = WizardFlow()
    steps = [WizardStep.WELCOME, WizardStep.DETECTION,
             WizardStep.SERVICES, WizardStep.DEPLOYMENT,
             WizardStep.REVIEW, WizardStep.COMPLETE]

    for expected_step in steps:
        assert flow.state.current_step == expected_step
        if expected_step != WizardStep.COMPLETE:
            flow.advance()