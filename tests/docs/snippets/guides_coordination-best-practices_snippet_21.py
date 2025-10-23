# Source: guides/coordination-best-practices.md
# Line: 834
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Validation before execution
def validate_workflow_spec(steps):
    """Validate workflow structure."""
    if not steps:
        raise ValueError("Workflow must have at least one step")

    step_ids = [f"step-{i}" for i in range(len(steps))]

    for step in steps:
        # Required fields
        if "agent" not in step:
            raise ValueError("Each step must have 'agent'")
        if "task" not in step:
            raise ValueError("Each step must have 'task'")

        # Validate dependencies
        for dep in step.get("depends_on", []):
            if dep not in step_ids:
                raise ValueError(f"Invalid dependency: {dep}")

    # Check for circular dependencies
    if has_circular_dependencies(steps):
        raise ValueError("Circular dependencies detected")

    return True

# Use validation
workflow_spec = {...}
validate_workflow_spec(workflow_spec["steps"])
workflow = coordinate_workflow(**workflow_spec)
