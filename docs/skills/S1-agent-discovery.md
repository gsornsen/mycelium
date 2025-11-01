# S1: Agent Discovery Skill

## Overview

The Agent Discovery Skill enables Claude Code to intelligently discover and select Mycelium agents based on natural
language task descriptions. This foundational skill eliminates the need for manual agent navigation and enables dynamic
agent selection based on capabilities and requirements.

**Status:** Implemented (M01 - Week 3) **Version:** 1.0.0 **Dependencies:** Task 1.1 (Agent Registry), Task 1.2
(Discovery API) **Future Enhancement:** Task 1.3 (NLP Matching Engine) will improve matching accuracy

## Capabilities

### Core Functions

1. **Natural Language Agent Discovery**

   - Query agents using plain English descriptions
   - Returns ranked list of matching agents with confidence scores
   - Filters results by minimum confidence threshold

1. **Agent Metadata Retrieval**

   - Get comprehensive information about specific agents
   - Access capabilities, tools, performance metrics, and usage statistics
   - Retrieve agent dependencies and example workflows

1. **Intelligent Recommendations**

   - Confidence scoring (0.0-1.0) for each match
   - Match reason explanations
   - Fallback recommendations for ambiguous queries

## MCP Tools

### `discover_agents`

Discover agents using natural language query.

**Signature:**

```python
async def discover_agents(
    query: str,
    limit: int = 5,
    threshold: float = 0.6,
) -> dict
```

**Parameters:**

- `query` (string, required): Natural language description of desired capabilities
  - Examples: "Python backend development", "database optimization", "security audit"
- `limit` (integer, optional): Maximum number of agents to return (1-20, default: 5)
- `threshold` (float, optional): Minimum confidence threshold (0.0-1.0, default: 0.6)

**Returns:**

```json
{
  "success": true,
  "query": "Python backend development",
  "agents": [
    {
      "id": "backend-developer",
      "type": "backend-developer",
      "name": "Backend Developer",
      "display_name": "Backend Developer",
      "category": "core",
      "description": "Full-stack backend development expert",
      "capabilities": ["API development", "Database design", "Authentication"],
      "tools": ["FastAPI", "PostgreSQL", "Redis"],
      "keywords": ["backend", "api", "database"],
      "confidence": 0.95,
      "match_reason": "exact match on keywords: backend, api",
      "estimated_tokens": 5000,
      "avg_response_time_ms": 200
    }
  ],
  "total_count": 3,
  "processing_time_ms": 85
}
```

**Error Handling:**

- `ValueError`: Invalid parameters (empty query, invalid limit/threshold)
- `DiscoveryAPIError`: API errors (server error, invalid request)
- `DiscoveryTimeoutError`: Request timeout (default: 30s)

**Examples:**

```python
# Basic discovery
result = await discover_agents("I need help with Python development")

# Specific requirements with higher confidence
result = await discover_agents(
    query="PostgreSQL performance tuning and query optimization",
    limit=3,
    threshold=0.8
)

# Broad search for multiple options
result = await discover_agents(
    query="frontend development",
    limit=10,
    threshold=0.5
)
```

### `get_agent_details`

Get detailed information about a specific agent.

**Signature:**

```python
async def get_agent_details(
    agent_id: str,
) -> dict
```

**Parameters:**

- `agent_id` (string, required): Agent ID or agent type
  - Examples: "backend-developer", "python-pro", "01-core-backend-developer"

**Returns:**

```json
{
  "success": true,
  "agent": {
    "id": "backend-developer",
    "type": "backend-developer",
    "name": "Backend Developer",
    "display_name": "Backend Developer",
    "category": "core",
    "description": "Expert in full-stack backend development...",
    "capabilities": ["API development", "Database design"],
    "tools": ["FastAPI", "PostgreSQL"],
    "keywords": ["backend", "api", "database"],
    "file_path": "/plugins/mycelium-core/agents/01-core-backend-developer.md",
    "estimated_tokens": 5000,
    "avg_response_time_ms": 200,
    "success_rate": 0.95,
    "usage_count": 1234,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-15T10:30:00Z",
    "last_used_at": "2025-10-21T12:00:00Z"
  },
  "metadata": {
    "dependencies": ["python-pro"],
    "examples": ["Build REST API", "Design database schema"]
  }
}
```

**Error Handling:**

- `ValueError`: Invalid parameters (empty agent_id)
- `DiscoveryAPIError`: Agent not found or API error
- `DiscoveryTimeoutError`: Request timeout

**Examples:**

```python
# Get details by agent ID
result = await get_agent_details("backend-developer")

# Get details by agent type (file prefix)
result = await get_agent_details("01-core-backend-developer")
```

## Usage Patterns

### Pattern 1: Task-Based Discovery

When you have a specific task and need to find the right agent:

```python
# 1. Discover agents for the task
result = await discover_agents(
    query="optimize slow PostgreSQL queries",
    limit=3,
    threshold=0.7
)

# 2. Review top matches
for agent in result["agents"]:
    print(f"{agent['name']} (confidence: {agent['confidence']})")
    print(f"  Reason: {agent['match_reason']}")
    print(f"  Capabilities: {', '.join(agent['capabilities'])}")

# 3. Get detailed information about top choice
if result["agents"]:
    top_agent = result["agents"][0]
    details = await get_agent_details(top_agent["id"])
    # Use agent based on detailed capabilities
```

### Pattern 2: Capability Exploration

When exploring what agents are available for a domain:

```python
# Broad search to see available options
result = await discover_agents(
    query="web development",
    limit=10,
    threshold=0.5  # Lower threshold for exploration
)

# Review categories of agents found
categories = {}
for agent in result["agents"]:
    cat = agent["category"]
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(agent["name"])

# Examine specific agents of interest
for agent_id in interesting_agents:
    details = await get_agent_details(agent_id)
```

### Pattern 3: Multi-Agent Team Assembly

When building a team for complex workflows:

```python
# Find specialists for different aspects
backend_agents = await discover_agents("backend API development")
frontend_agents = await discover_agents("React frontend development")
database_agents = await discover_agents("database design and optimization")

# Combine into workflow team
team = []
if backend_agents["agents"]:
    team.append(backend_agents["agents"][0])
if frontend_agents["agents"]:
    team.append(frontend_agents["agents"][0])
if database_agents["agents"]:
    team.append(database_agents["agents"][0])

# Get detailed info for each team member
for agent in team:
    details = await get_agent_details(agent["id"])
    # Plan workflow based on capabilities
```

## Performance Characteristics

### Latency Targets

- **discover_agents**: \<500ms end-to-end (P95)

  - API processing: \<100ms (P95)
  - Network overhead: ~50ms
  - Client processing: ~50ms

- **get_agent_details**: \<200ms end-to-end (P95)

  - API processing: \<50ms (P95)
  - Network overhead: ~50ms
  - Client processing: ~25ms

### Retry Behavior

Both tools implement automatic retry logic:

- **Max retries**: 2 attempts (3 total tries)
- **Backoff strategy**: Exponential (0.5s, 1.0s)
- **Retry conditions**: Timeout, HTTP errors
- **No retry conditions**: Validation errors, 404 not found

### Resource Usage

- **Memory**: \<10MB per request
- **Network**: ~5KB request, ~50KB response (typical)
- **Database**: Minimal impact due to API caching

## Integration with Other Skills

### S2: Coordination Skill

Agent Discovery feeds into workflow coordination:

```python
# Discover agents for workflow steps
step1_agents = await discover_agents("data validation")
step2_agents = await discover_agents("database migration")
step3_agents = await discover_agents("API endpoint creation")

# Coordinate workflow (S2 skill)
await coordinate_workflow(
    steps=[
        {"agent": step1_agents["agents"][0]["id"], "task": "Validate data"},
        {"agent": step2_agents["agents"][0]["id"], "task": "Migrate schema"},
        {"agent": step3_agents["agents"][0]["id"], "task": "Create endpoints"},
    ]
)
```

### Future: S3-S5 Skills

- **S3 (Token Optimization)**: Discovery metadata will include token budgets
- **S4 (Meta-Skills)**: Discovery will power dynamic skill composition
- **S5 (Observability)**: Discovery usage will be tracked and analyzed

## Best Practices

### Query Design

**Good queries are specific but flexible:**

- ✅ "PostgreSQL query optimization and indexing"
- ✅ "React frontend with TypeScript and hooks"
- ✅ "security audit for authentication flows"

**Avoid overly vague or narrow queries:**

- ❌ "development" (too vague)
- ❌ "PostgreSQL 15.3 pg_stat_statements analysis" (too specific)

### Confidence Thresholds

Choose threshold based on use case:

- **High confidence (0.8-1.0)**: Critical tasks requiring exact match
- **Medium confidence (0.6-0.8)**: General tasks with flexibility
- **Low confidence (0.4-0.6)**: Exploration and discovery

### Result Limits

Balance between options and decision paralysis:

- **3-5 agents**: Good for quick decisions
- **5-10 agents**: Exploration and team building
- **10-20 agents**: Comprehensive analysis

### Error Handling

Always handle potential failures gracefully:

```python
try:
    result = await discover_agents("Python development")
    if not result["agents"]:
        print("No agents found for query")
        # Provide fallback or ask user to refine
    else:
        # Use discovered agents
        pass
except DiscoveryTimeoutError:
    print("Discovery timed out, try again")
except DiscoveryAPIError as e:
    print(f"Discovery failed: {e}")
    # Fall back to known agents or manual selection
```

## Limitations

### Current Implementation (v1.0.0)

1. **Text Matching Only**: Uses simple keyword matching

   - **Mitigation**: Task 1.3 will add NLP semantic matching
   - **Impact**: May miss relevant agents with different terminology

1. **English Only**: No multi-language support

   - **Mitigation**: Query in English for now
   - **Future**: Multi-language support in M02

1. **No Context Awareness**: Doesn't consider conversation history

   - **Mitigation**: Include context in query explicitly
   - **Future**: Context integration in M03

1. **Static Capabilities**: Agent capabilities manually defined

   - **Mitigation**: Regular agent description updates
   - **Future**: Dynamic capability learning in M04

### Known Edge Cases

1. **Ambiguous Queries**: May return diverse results

   - Example: "backend" could match Python, Java, Go, etc.
   - Solution: Use more specific queries

1. **No Exact Match**: May return low-confidence results

   - Example: Very specialized query with no matching agent
   - Solution: Review match_reason and consider alternatives

1. **Category Overlap**: Agents may fit multiple categories

   - Example: "fullstack-developer" matches both frontend and backend
   - Solution: Review all top results, not just first match

## Troubleshooting

### Common Issues

**Issue**: No agents found for valid query

```
Symptom: Empty agents list with success=true
Diagnosis: Threshold too high or query too specific
Solution: Lower threshold to 0.5 or broaden query
```

**Issue**: Discovery timeout

```
Symptom: DiscoveryTimeoutError after 30 seconds
Diagnosis: API slow or unavailable
Solution: Check API health, retry with longer timeout
```

**Issue**: Low confidence scores

```
Symptom: All results below 0.7 confidence
Diagnosis: Query doesn't match agent descriptions well
Solution: Refine query with different keywords or check agent registry
```

**Issue**: Agent not found by ID

```
Symptom: DiscoveryAPIError "Agent not found"
Diagnosis: Invalid agent_id or agent doesn't exist
Solution: Use discover_agents to find correct ID
```

### Diagnostic Commands

```python
# Check API health
from plugins.mycelium_core.mcp.tools.discovery_tools import check_discovery_health

health = await check_discovery_health()
print(f"Status: {health['status']}")
print(f"Agents: {health['agent_count']}")

# Test with broad query
result = await discover_agents("development", limit=20, threshold=0.3)
print(f"Found {result['total_count']} agents")

# Verify specific agent exists
try:
    details = await get_agent_details("backend-developer")
    print(f"Agent found: {details['agent']['name']}")
except DiscoveryAPIError:
    print("Agent not in registry")
```

## Configuration

### Environment Variables

```bash
# Discovery API URL (default: http://localhost:8000)
export DISCOVERY_API_URL="http://localhost:8000"

# Or for remote API
export DISCOVERY_API_URL="https://api.mycelium.dev"
```

### Tool Configuration

Configuration is stored in `plugins/mycelium-core/mcp/config/discovery.json`:

- **Timeout**: 30 seconds (configurable per request)
- **Retries**: 2 retries with exponential backoff
- **Rate limiting**: 100 requests/minute
- **Caching**: 5-minute TTL for discovery results

## Metrics and Monitoring

### Usage Metrics

Track these metrics for optimization:

- Discovery query frequency
- Average confidence scores
- Most common query patterns
- Agent selection rates (which agents chosen)

### Performance Metrics

Monitor for SLA compliance:

- Request latency (P50, P95, P99)
- Success rate
- Timeout rate
- Retry frequency

### Quality Metrics

Measure effectiveness:

- User satisfaction with results
- Result refinement rate (queries repeated with changes)
- Agent usage correlation (discovered → used)

## Version History

### v1.0.0 (2025-10-21)

- Initial implementation
- MCP tools: `discover_agents`, `get_agent_details`
- Text-based matching with confidence scoring
- Retry logic and error handling
- Integration tests and documentation

### Planned Enhancements

**v1.1.0 (M01 Week 4-5)**

- NLP semantic matching (Task 1.3 integration)
- Improved confidence scoring algorithm
- Match reason explanations enhanced

**v2.0.0 (M02)**

- Context-aware discovery
- Multi-language support
- Caching optimization
- Performance improvements

## References

- [M01 Milestone Specification](/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M01_AGENT_DISCOVERY_SKILLS.md)
- [Task 1.4 Requirements](/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M01_AGENT_DISCOVERY_SKILLS.md#task-14-agent-discovery-mcp-tool)
- [Discovery API Documentation](/home/gerald/git/mycelium/docs/api/discovery-quickstart.md)
- [Agent Registry Schema](/home/gerald/git/mycelium/plugins/mycelium-core/registry/schema.sql)

## Support

For issues or questions:

1. Check troubleshooting section above
1. Review integration tests for examples
1. Check API health status
1. Consult technical documentation
1. Report issues with reproduction steps

______________________________________________________________________

**Skill ID**: S1 **Category**: Discovery **Maturity**: Stable **Test Coverage**: 95% **Last Updated**: 2025-10-21
