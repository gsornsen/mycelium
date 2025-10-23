# Source: skills/S2-coordination.md
# Line: 727
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Start workflow
workflow = await coordinate_workflow(steps=[...])
workflow_id = workflow["workflow_id"]

# Monitor progress
async def monitor_workflow(wf_id):
    while True:
        status = await get_workflow_status(wf_id)

        if status["status"] == "completed":
            print(f"✅ Workflow completed in {status['total_duration_ms']}ms")
            break
        if status["status"] == "failed":
            print(f"❌ Workflow failed at step {status['current_step']}")
            # Get failure events
            events = await get_coordination_events(
                workflow_id=wf_id,
                event_type="failure"
            )
            for event in events["events"]:
                print(f"  Error: {event['metadata']['error']}")
            break
        print(f"⏳ Progress: {status['progress_percent']}%")
        await asyncio.sleep(1)

await monitor_workflow(workflow_id)
