# Source: guides/coordination-best-practices.md
# Line: 877
# Valid syntax: True
# Has imports: False
# Has assignments: False

# ❌ ANTI-PATTERN: Excessive handoffs
async def process_files(files):
    for file in files:
        # Handoff for each file - wasteful!
        await handoff_to_agent(
            "file-processor",
            f"Process {file}"
        )

# ✅ SOLUTION: Batch processing
async def process_files(files):
    await handoff_to_agent(
        "file-processor",
        "Process files in batch",
        context={"files": files}  # Single handoff
    )
