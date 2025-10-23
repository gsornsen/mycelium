# Source: deployment-reference.md
# Line: 493
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Use built-in templates
renderer = TemplateRenderer()

# Use custom templates
renderer = TemplateRenderer(templates_dir=Path("./my-templates"))
