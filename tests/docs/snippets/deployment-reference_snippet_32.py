# Source: deployment-reference.md
# Line: 475
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.deployment.renderer import TemplateRenderer

renderer = TemplateRenderer()
content = renderer.render_docker_compose(config)