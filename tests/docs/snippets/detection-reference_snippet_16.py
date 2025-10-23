# Source: detection-reference.md
# Line: 315
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection.docker_detector import verify_docker_permissions

has_perms, message = verify_docker_permissions()
if not has_perms:
    print(f"Permission issue: {message}")
    print("Try: sudo usermod -aG docker $USER")