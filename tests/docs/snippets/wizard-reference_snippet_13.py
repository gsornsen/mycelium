# Source: wizard-reference.md
# Line: 345
# Valid syntax: True
# Has imports: False
# Has assignments: True

flow = WizardFlow()
try:
    next_step = flow.advance()
    print(f"Advanced to {next_step}")
except ValueError as e:
    print(f"Cannot advance: {e}")