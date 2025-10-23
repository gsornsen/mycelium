# Source: troubleshooting/discovery-coordination.md
# Line: 362
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Solution 1: Validate workflow before execution
def validate_workflow(steps):
    # Check required fields
    for i, step in enumerate(steps):
        if "agent" not in step:
            raise ValueError(f"Step {i} missing 'agent' field")
        if "task" not in step:
            raise ValueError(f"Step {i} missing 'task' field")

    # Check dependencies
    step_ids = {f"step-{i}" for i in range(len(steps))}
    for i, step in enumerate(steps):
        for dep in step.get("depends_on", []):
            if dep not in step_ids:
                raise ValueError(f"Step {i} has invalid dependency: {dep}")

validate_workflow(steps)  # Validate before executing
workflow = coordinate_workflow(steps=steps)

# Solution 2: Fix dependency issues
# Check for circular dependencies
def find_circular_dependencies(steps):
    # Build dependency graph
    graph = {f"step-{i}": step.get("depends_on", [])
             for i, step in enumerate(steps)}

    # Detect cycles
    visited = set()
    path = set()

    def has_cycle(node):
        if node in path:
            return True
        if node in visited:
            return False

        visited.add(node)
        path.add(node)

        for neighbor in graph.get(node, []):
            if has_cycle(neighbor):
                return True

        path.remove(node)
        return False

    for node in graph:
        if has_cycle(node):
            return True

    return False

if find_circular_dependencies(steps):
    print("Circular dependency detected!")
    # Fix dependencies before retrying

# Solution 3: Simplify workflow
# Start with minimal workflow and add steps incrementally
workflow = coordinate_workflow(
    steps=[steps[0]]  # Just first step
)

if workflow["status"] == "completed":
    # First step works, add second
    workflow = coordinate_workflow(
        steps=[steps[0], steps[1]]
    )
    # Continue adding steps