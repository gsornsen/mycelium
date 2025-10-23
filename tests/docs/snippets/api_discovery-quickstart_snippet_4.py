# Source: api/discovery-quickstart.md
# Line: 261
# Valid syntax: True
# Has imports: False
# Has assignments: False

# Good: Specific limit
{"query": "backend", "limit": 5}

# Avoid: Excessive results
{"query": "backend", "limit": 50}
