# Source: guides/coordination-best-practices.md
# Line: 182
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Specific, targeted queries
# For API performance issues
agents = discover_agents("API performance optimization latency reduction")

# For database design
agents = discover_agents("PostgreSQL schema design normalization")

# For security audit
agents = discover_agents("web application security OWASP authentication")

# ❌ BAD: Generic queries
agents = discover_agents("development")  # Too vague
agents = discover_agents("help")  # No useful information
agents = discover_agents("computer stuff")  # Meaningless