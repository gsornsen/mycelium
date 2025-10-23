# Source: deployment-integration.md
# Line: 311
# Valid syntax: True
# Has imports: True
# Has assignments: True

from jinja2 import Environment, FileSystemLoader

def create_custom_renderer():
    """Create renderer with custom filters."""
    env = Environment(
        loader=FileSystemLoader("./my-templates"),
        trim_blocks=True,
        lstrip_blocks=True
    )

    # Add custom filter
    def to_memory_mb(memory_str: str) -> int:
        """Convert memory string to MB."""
        units = {'kb': 1/1024, 'mb': 1, 'gb': 1024}
        value = int(''.join(filter(str.isdigit, memory_str)))
        unit = ''.join(filter(str.isalpha, memory_str)).lower()
        return int(value * units.get(unit, 1))

    env.filters['to_mb'] = to_memory_mb

    return env

# Use in template:
# Memory limit: {{ config.services.redis.max_memory|to_mb }} MB