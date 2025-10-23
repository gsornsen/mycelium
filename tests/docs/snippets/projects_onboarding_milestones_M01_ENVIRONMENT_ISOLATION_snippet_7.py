# Source: projects/onboarding/milestones/M01_ENVIRONMENT_ISOLATION.md
# Line: 755
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Example: Loading config with fallback
import yaml


def load_config():
    """Load configuration with hierarchical fallback."""
    config_file = find_config_file("config.yaml")

    if config_file:
        with open(config_file) as f:
            return yaml.safe_load(f)

    # No config file found, return defaults
    return {
        "deployment_method": "docker-compose",
        "services": ["redis", "postgres"],
    }
