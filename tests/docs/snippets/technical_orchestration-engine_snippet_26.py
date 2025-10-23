# Source: technical/orchestration-engine.md
# Line: 633
# Valid syntax: True
# Has imports: False
# Has assignments: True

state_manager = StateManager()
try:
    await state_manager.initialize()
    # Use state manager
finally:
    await state_manager.close()
