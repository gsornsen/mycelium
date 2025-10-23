# Source: wizard-integration.md
# Line: 715
# Valid syntax: True
# Has imports: False
# Has assignments: False

# Don't only test happy paths
def test_wizard():
    # Only tests successful completion
    assert wizard_completes_successfully()