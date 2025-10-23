# Source: troubleshooting/discovery-coordination.md
# Line: 256
# Valid syntax: True
# Has imports: False
# Has assignments: True

workflow = coordinate_workflow(steps=[...])
time.sleep(60)
status = get_workflow_status(workflow["workflow_id"])
# status["status"] == "in_progress"
# No progress for extended time