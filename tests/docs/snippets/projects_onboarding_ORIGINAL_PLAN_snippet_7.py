# Source: projects/onboarding/ORIGINAL_PLAN.md
# Line: 1181
# Valid syntax: True
# Has imports: False
# Has assignments: True

# tests/test_onboarding.py
def test_docker_compose_generation():
    config = {
        "services": {"redis": {"enabled": True}},
        "deployment": {"method": "docker-compose"}
    }

    compose_file = generate_docker_compose(config)
    assert "redis:" in compose_file
    assert "6379:6379" in compose_file

def test_justfile_generation():
    config = {
        "services": {"redis": {"enabled": True}},
        "deployment": {"method": "baremetal"}
    }

    justfile = generate_justfile(config)
    assert "start-redis:" in justfile
    assert "[parallel]" in justfile
