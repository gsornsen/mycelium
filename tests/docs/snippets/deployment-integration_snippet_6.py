# Source: deployment-integration.md
# Line: 297
# Valid syntax: True
# Has imports: False
# Has assignments: False

# In Jinja2 templates, access:
{{ config.project_name }}              # Project name
{{ config.services.redis.enabled }}    # Service enabled status
{{ config.services.redis.port }}       # Redis port
{{ config.services.redis.max_memory }} # Redis memory limit
{{ config.services.postgres.database }}# PostgreSQL database name
{{ config.deployment.method }}         # Deployment method
