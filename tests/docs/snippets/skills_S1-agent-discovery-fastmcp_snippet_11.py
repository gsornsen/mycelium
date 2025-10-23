# Source: skills/S1-agent-discovery-fastmcp.md
# Line: 773
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: invalid syntax (<unknown>, line 2)

# config/fastmcp.yaml
server:
  name: "Mycelium Agent Discovery"
  version: "1.0.0"
  description: "Agent discovery with NLP matching"

tools:
  discover_agents:
    enabled: true
    timeout_seconds: 30
    rate_limit: 100  # requests per minute

  get_agent_details:
    enabled: true
    timeout_seconds: 10
    rate_limit: 200

registry:
  database_url: "postgresql://localhost:5432/mycelium_registry"
  cache_ttl_seconds: 3600
  embeddings_cache_size: 1000

nlp:
  model: "all-MiniLM-L6-v2"
  batch_size: 32
  device: "cpu"  # or "cuda"