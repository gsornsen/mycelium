# Discovery API Quick Start Guide

Get started with the Mycelium Discovery API in under 10 minutes.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the API](#running-the-api)
- [Basic Usage](#basic-usage)
- [Common Workflows](#common-workflows)
- [Performance Tips](#performance-tips)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have:

- Python 3.10 or later
- PostgreSQL 15+ with pgvector extension
- Agent registry populated (see Task 1.1)

## Installation

### 1. Install Dependencies

```bash
# Install FastAPI and dependencies
pip install fastapi uvicorn asyncpg pydantic

# Or using uv (recommended)
uv pip install fastapi uvicorn asyncpg pydantic
```

### 2. Configure Database

Set your database connection string:

```bash
export DATABASE_URL="postgresql://localhost:5432/mycelium_registry"
```

Or create a `.env` file:

```env
DATABASE_URL=postgresql://localhost:5432/mycelium_registry
```

### 3. Verify Registry

Ensure your registry is populated:

```bash
cd plugins/mycelium-core/registry
python populate.py
```

## Running the API

### Development Server

```bash
cd plugins/mycelium-core/api
uvicorn discovery:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc
- OpenAPI spec: http://localhost:8000/api/v1/openapi.json

### Production Server

```bash
uvicorn discovery:app --host 0.0.0.0 --port 8000 --workers 4
```

## Basic Usage

### Health Check

Verify the API is running:

```bash
curl http://localhost:8000/api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "pgvector_installed": true,
  "agent_count": 130,
  "database_size": "42 MB",
  "timestamp": "2025-10-21T15:30:00Z",
  "version": "1.0.0"
}
```

### Discover Agents

Find agents using natural language:

```bash
curl -X POST http://localhost:8000/api/v1/agents/discover \
  -H "Content-Type: application/json" \
  -d '{
    "query": "python backend development",
    "limit": 5,
    "threshold": 0.7
  }'
```

Response:
```json
{
  "query": "python backend development",
  "matches": [
    {
      "agent": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "agent_id": "01-core-backend-developer",
        "agent_type": "backend-developer",
        "name": "backend-developer",
        "display_name": "Backend Developer",
        "category": "Development",
        "description": "Expert in backend development with Python, Node.js, and Go",
        "capabilities": ["API design", "Database optimization"],
        "tools": ["database", "docker"],
        "keywords": ["backend", "api", "python"],
        "file_path": "plugins/mycelium-core/agents/01-core-backend-developer.md",
        "estimated_tokens": 2500,
        "created_at": "2025-10-20T10:00:00Z",
        "updated_at": "2025-10-21T15:30:00Z"
      },
      "confidence": 0.95,
      "match_reason": "exact match on keywords: backend, python"
    }
  ],
  "total_count": 1,
  "processing_time_ms": 45.3
}
```

### Get Agent Details

Retrieve complete agent metadata:

```bash
curl http://localhost:8000/api/v1/agents/backend-developer
```

### Search Agents

Search with filters:

```bash
# Search by query
curl "http://localhost:8000/api/v1/agents/search?q=security"

# Filter by category
curl "http://localhost:8000/api/v1/agents/search?category=Development"

# Paginated results
curl "http://localhost:8000/api/v1/agents/search?limit=10&offset=0"

# Combined filters
curl "http://localhost:8000/api/v1/agents/search?q=python&category=Development&limit=5"
```

## Common Workflows

### Workflow 1: Find Best Agent for Task

```python
import requests

# Step 1: Discover agents
response = requests.post(
    "http://localhost:8000/api/v1/agents/discover",
    json={
        "query": "secure API authentication implementation",
        "limit": 3,
        "threshold": 0.8
    }
)

matches = response.json()["matches"]

# Step 2: Get top match
if matches:
    best_agent = matches[0]
    print(f"Best match: {best_agent['agent']['name']}")
    print(f"Confidence: {best_agent['confidence']}")
    print(f"Reason: {best_agent['match_reason']}")
```

### Workflow 2: Browse Agents by Category

```python
import requests

# Get all categories
response = requests.get("http://localhost:8000/api/v1/agents/search?limit=100")
agents = response.json()["agents"]

categories = set(agent["category"] for agent in agents)

# Browse each category
for category in categories:
    response = requests.get(
        f"http://localhost:8000/api/v1/agents/search?category={category}"
    )
    print(f"\n{category} ({response.json()['total_count']} agents)")
```

### Workflow 3: Agent Discovery with Fallback

```python
import requests

def discover_agent(query: str, min_confidence: float = 0.8):
    """Discover agent with fallback to lower confidence."""

    # Try high confidence first
    response = requests.post(
        "http://localhost:8000/api/v1/agents/discover",
        json={"query": query, "threshold": min_confidence}
    )

    matches = response.json()["matches"]

    if not matches and min_confidence > 0.5:
        # Fallback to lower confidence
        print(f"No high-confidence matches, trying threshold 0.5...")
        return discover_agent(query, min_confidence=0.5)

    return matches

# Usage
agents = discover_agent("machine learning model training")
if agents:
    print(f"Found {len(agents)} agents")
else:
    print("No agents found for this query")
```

## Performance Tips

### 1. Use Appropriate Thresholds

- **High confidence (0.8-1.0)**: For exact matches
- **Medium confidence (0.6-0.8)**: For related capabilities
- **Low confidence (0.5-0.6)**: For broad exploration

### 2. Limit Results

Request only what you need:

```python
# Good: Specific limit
{"query": "backend", "limit": 5}

# Avoid: Excessive results
{"query": "backend", "limit": 50}
```

### 3. Monitor Performance

Check response headers:

```bash
curl -I http://localhost:8000/api/v1/health
```

Headers include:
- `X-Processing-Time-Ms`: Response time
- `X-RateLimit-Remaining`: Rate limit status
- `X-Request-ID`: Request tracing

### 4. Cache Common Queries

For frequently accessed agents, cache responses:

```python
from functools import lru_cache
import requests

@lru_cache(maxsize=100)
def get_agent(agent_id: str):
    response = requests.get(f"http://localhost:8000/api/v1/agents/{agent_id}")
    return response.json()
```

## Rate Limiting

The API enforces rate limiting:

- **Default**: 100 requests per minute per IP
- **Burst**: 10 requests
- **Headers**: Check `X-RateLimit-*` headers

Example handling:

```python
import requests
import time

def discover_with_retry(query: str, max_retries: int = 3):
    """Discover agents with rate limit retry."""

    for attempt in range(max_retries):
        response = requests.post(
            "http://localhost:8000/api/v1/agents/discover",
            json={"query": query}
        )

        if response.status_code == 429:
            # Rate limited
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"Rate limited, waiting {retry_after}s...")
            time.sleep(retry_after)
            continue

        return response.json()

    raise Exception("Max retries exceeded")
```

## Using with Python Client

```python
import asyncio
import aiohttp

async def discover_agents_async(query: str):
    """Async agent discovery."""

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/api/v1/agents/discover",
            json={"query": query, "limit": 10}
        ) as response:
            return await response.json()

# Usage
results = asyncio.run(discover_agents_async("python development"))
print(f"Found {results['total_count']} agents")
```

## Integration with Claude Code

The Discovery API integrates seamlessly with Claude Code via MCP tools (Task 1.4).

Claude Code will use these endpoints internally when you invoke discovery tools:

```
User: "Find me an agent for backend API development"

Claude Code internally calls:
POST /api/v1/agents/discover
{
  "query": "backend API development",
  "limit": 5,
  "threshold": 0.7
}
```

## Troubleshooting

### API Not Starting

**Error**: `RuntimeError: Registry not initialized`

**Solution**: Check database connection:
```bash
psql $DATABASE_URL -c "SELECT 1"
```

### No Results Returned

**Problem**: Discovery returns empty matches

**Solutions**:
1. Lower the confidence threshold: `"threshold": 0.5`
2. Broaden your query: `"backend"` instead of `"backend-developer-python-async"`
3. Verify agents are in registry:
   ```bash
   curl http://localhost:8000/api/v1/health
   # Check agent_count
   ```

### Rate Limit Exceeded

**Error**: `429 Too Many Requests`

**Solutions**:
1. Check `Retry-After` header
2. Implement exponential backoff
3. Reduce request frequency
4. Contact admin to increase limit

### Slow Response Times

**Problem**: `processing_time_ms > 100ms`

**Solutions**:
1. Check database indexes:
   ```sql
   SELECT * FROM pg_indexes WHERE tablename = 'agents';
   ```
2. Reduce result limit
3. Monitor database performance:
   ```bash
   curl http://localhost:8000/api/v1/health
   # Check database_size
   ```

### Invalid Agent ID

**Error**: `404 Agent not found`

**Solutions**:
1. Use agent type instead: `backend-developer` vs `01-core-backend-developer`
2. Search first to find valid IDs:
   ```bash
   curl "http://localhost:8000/api/v1/agents/search?q=backend"
   ```

## Next Steps

1. **Explore Interactive Docs**: Visit http://localhost:8000/api/v1/docs
2. **Read Full API Spec**: See `discovery-api.yaml`
3. **Integrate with MCP**: See Task 1.4 documentation
4. **Enable NLP Matching**: See Task 1.3 for semantic search

## Additional Resources

- [OpenAPI Specification](discovery-api.yaml)
- [Task 1.1: Agent Registry](../../plugins/mycelium-core/registry/README.md)
- [Task 1.3: NLP Matching](../../plugins/mycelium-core/matching/README.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Support

For issues or questions:
- Check logs: `uvicorn.log`
- Health check: `curl http://localhost:8000/api/v1/health`
- GitHub Issues: [Mycelium Issues](https://github.com/mycelium/issues)
