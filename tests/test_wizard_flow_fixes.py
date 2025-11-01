# Quick fixes for failing tests
import sys

sys.path.insert(0, "/home/gerald/git/mycelium")

from mycelium_onboarding.wizard.flow import WizardState

# Test that empty project name uses default
state = WizardState(project_name="")
config = state.to_config()
print(f"Empty project name result: {config.project_name}")
assert config.project_name == "mycelium", f"Expected 'mycelium', got '{config.project_name}'"

# Test that explicit project name is used
state2 = WizardState(
    project_name="test-project",
    services_enabled={"redis": True, "postgres": True, "temporal": False},
)
config2 = state2.to_config()
print(f"Explicit project name result: {config2.project_name}")
assert config2.project_name == "test-project", f"Expected 'test-project', got '{config2.project_name}'"

print("All manual tests passed!")
