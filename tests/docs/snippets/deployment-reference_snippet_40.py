# Source: deployment-reference.md
# Line: 566
# Valid syntax: True
# Has imports: False
# Has assignments: True

services = renderer.render_systemd(config)

for service_name, content in services.items():
    output_path = Path(f"systemd/{service_name}")
    output_path.write_text(content)
