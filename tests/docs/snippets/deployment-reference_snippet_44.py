# Source: deployment-reference.md
# Line: 654
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.deployment.renderer import TemplateRenderer

renderer = TemplateRenderer()

# Render Docker Compose
compose_content = renderer.render_docker_compose(config)

# Render Kubernetes
k8s_manifests = renderer.render_kubernetes(config)

# Process manifests
for name, content in k8s_manifests.items():
    print(f"Manifest: {name}")
    print(f"Size: {len(content)} bytes")
