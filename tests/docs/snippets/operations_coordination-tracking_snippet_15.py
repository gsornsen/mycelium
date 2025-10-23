# Source: operations/coordination-tracking.md
# Line: 537
# Valid syntax: True
# Has imports: False
# Has assignments: False

# Add audit logging to queries
logger.info(
    f"User {user_id} accessed workflow events",
    extra={"workflow_id": workflow_id, "user_id": user_id}
)
