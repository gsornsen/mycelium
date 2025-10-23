# Source: guides/coordination-best-practices.md
# Line: 932
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ❌ ANTI-PATTERN: Implicit state via files
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "data-processor",
            "task": "Process data and write to /tmp/result.json"  # Side effect
        },
        {
            "agent": "analyzer",
            "task": "Analyze data in /tmp/result.json",  # Implicit dependency
            "depends_on": ["step-0"]
        }
    ]
)

# ✅ SOLUTION: Explicit state passing
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "data-processor",
            "task": "Process data",
            "params": {"output_file": "result.json"}
        },
        {
            "agent": "analyzer",
            "task": "Analyze processed data",
            "depends_on": ["step-0"],
            "params": {
                "input": "{{step-0.output_file}}"  # Explicit reference
            }
        }
    ]
)
