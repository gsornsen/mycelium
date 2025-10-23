# Source: deployment-reference.md
# Line: 344
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Rotate PostgreSQL password
try:
    rotated = manager.rotate_secret("postgres")
    print("Password rotated successfully")
except ValueError as e:
    print(f"Rotation failed: {e}")
