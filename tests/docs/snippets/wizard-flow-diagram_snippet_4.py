# Source: wizard-flow-diagram.md
# Line: 424
# Valid syntax: True
# Has imports: False
# Has assignments: True

def test_advance_from_welcome():
    flow = WizardFlow()
    assert flow.state.current_step == WizardStep.WELCOME

    flow.advance()
    assert flow.state.current_step == WizardStep.DETECTION

def test_quick_mode_skips_advanced():
    flow = WizardFlow()
    flow.state.setup_mode = "quick"
    flow.state.current_step = WizardStep.DEPLOYMENT

    next_step = flow.state.get_next_step()
    assert next_step == WizardStep.REVIEW