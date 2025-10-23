# Source: troubleshooting/discovery-coordination.md
# Line: 725
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Solution 1: Reduce context size
# Before:
context = {
    "entire_file": read_file("large_file.txt"),  # 5MB
    "all_data": load_all_data()  # 10MB
}

# After:
context = {
    "file_path": "large_file.txt",  # Reference
    "data_summary": {
        "row_count": 10000,
        "columns": ["id", "name", "email"],
        "sample": data[:100]  # Small sample
    }
}

# Solution 2: Clear completed workflows
from plugins.mycelium_core.coordination import cleanup_workflows

# Clean up workflows older than 24 hours
cleanup_workflows(older_than_hours=24)

# Solution 3: Use workflow checkpoints
# Enable checkpointing to disk instead of keeping in memory
workflow = coordinate_workflow(
    steps=[...],
    checkpoint_to_disk=True  # Reduces memory usage
)
