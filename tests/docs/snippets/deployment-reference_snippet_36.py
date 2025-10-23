# Source: deployment-reference.md
# Line: 518
# Valid syntax: True
# Has imports: False
# Has assignments: True

config = MyceliumConfig(
    project_name="my-app",
    services={"redis": {"enabled": True}}
)

compose_yaml = renderer.render_docker_compose(config)
Path("docker-compose.yml").write_text(compose_yaml)