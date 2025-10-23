# Source: deployment-reference.md
# Line: 543
# Valid syntax: True
# Has imports: False
# Has assignments: True

manifests = renderer.render_kubernetes(config)

for filename, content in manifests.items():
    output_path = Path(f"kubernetes/{filename}")
    output_path.write_text(content)
