# Source: deployment-reference.md
# Line: 365
# Valid syntax: True
# Has imports: False
# Has assignments: False

if manager.delete_secrets():
    print("Secrets deleted")
else:
    print("No secrets to delete")