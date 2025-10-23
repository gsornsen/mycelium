# Source: deployment-integration.md
# Line: 217
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.deployment.renderer import TemplateRenderer

# Point to custom templates
renderer = TemplateRenderer(
    templates_dir=Path("./my-templates")
)

# Render with custom templates
content = renderer.render_docker_compose(config)