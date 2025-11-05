# Agent Registry API Documentation

## Overview

The Agent Registry provides a centralized system for managing agent metadata with PostgreSQL backend and pgvector
support for semantic search. This API enables CRUD operations, full-text search, and vector similarity search for agent
discovery.

**Version:** 1.0.0 **Database:** PostgreSQL 15+ with pgvector extension **Vector Dimensions:** 384 (for
sentence-transformers/all-MiniLM-L6-v2)

## Architecture

### Database Schema

The registry uses the following core tables:

- **agents**: Main table storing agent metadata and embeddings
- **agent_dependencies**: Tracks agent prerequisites and dependencies
- **agent_usage**: Logs agent invocations and performance metrics
- **agent_statistics**: Materialized view for performance analytics

### Performance Characteristics

- **Query Performance**: \<100ms for standard lookups
- **Search Performance**: \<100ms for full-text search
- **Similarity Search**: \<200ms with HNSW index
- **Bulk Insert**: ~10-50 agents/second depending on batch size

## Installation

### Prerequisites

```bash
# PostgreSQL 15+ with pgvector extension
docker run -d \
  --name mycelium-postgres \
  -e POSTGRES_DB=mycelium_registry \
  -e POSTGRES_USER=mycelium \
  -e POSTGRES_PASSWORD=<secure-password> \
  -p 5432:5432 \
  ankane/pgvector:latest
```

### Schema Setup

```bash
# Apply the schema
psql -d mycelium_registry -f plugins/mycelium-core/registry/schema.sql
```

### Python Dependencies

```bash
# Install required packages
pip install asyncpg
```

## API Reference

### AgentRegistry Class

Main class providing all registry operations.

#### Initialization

```python
from plugins.mycelium_core.registry import AgentRegistry

# Initialize with connection string
registry = AgentRegistry(
    connection_string="postgresql://localhost:5432/mycelium_registry"
)
await registry.initialize()

# Initialize with existing pool
import asyncpg
pool = await asyncpg.create_pool(connection_string)
registry = AgentRegistry(pool=pool)
await registry.initialize()

# Use as context manager (recommended)
async with AgentRegistry(connection_string) as registry:
    # Use registry
    pass
```

#### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://localhost:5432/mycelium_registry`)

______________________________________________________________________

### CRUD Operations

#### create_agent()

Create a new agent in the registry.

**Signature:**

```python
from uuid import UUID
from typing import Optional, List, Dict, Any

async def create_agent(
    agent_id: str,
    agent_type: str,
    name: str,
    display_name: str,
    category: str,
    description: str,
    file_path: str,
    capabilities: Optional[List[str]] = None,
    tools: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    embedding: Optional[List[float]] = None,
    estimated_tokens: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> UUID:
    """Create an agent in the registry."""
    pass
```

**Parameters:**

- `agent_id` (str): Unique agent identifier (e.g., "01-core-backend-developer")
- `agent_type` (str): Agent type/name (e.g., "backend-developer")
- `name` (str): Agent name
- `display_name` (str): Display name for UI
- `category` (str): Agent category
- `description` (str): Agent description
- `file_path` (str): Path to agent definition file
- `capabilities` (List\[str\], optional): List of agent capabilities
- `tools` (List\[str\], optional): List of tools the agent can use
- `keywords` (List\[str\], optional): Keywords for search
- `embedding` (List\[float\], optional): Vector embedding (384-dim)
- `estimated_tokens` (int, optional): Estimated token count
- `metadata` (Dict, optional): Additional metadata as JSON

**Returns:** UUID of the created agent

**Raises:**

- `AgentAlreadyExistsError`: If agent_id or agent_type already exists

**Example:**

```python
agent_uuid = await registry.create_agent(
    agent_id="01-core-backend-developer",
    agent_type="backend-developer",
    name="Backend Developer",
    display_name="Backend Developer",
    category="Core Development",
    description="Senior backend engineer for scalable API development",
    file_path="plugins/mycelium-core/agents/01-core-backend-developer.md",
    capabilities=["api-development", "database-design"],
    tools=["Bash", "Docker", "PostgreSQL"],
    keywords=["backend", "api", "database"],
    estimated_tokens=1200,
    metadata={"version": "1.0"}
)
```

______________________________________________________________________

#### get_agent_by_id()

Retrieve an agent by its agent_id.

**Signature:**

```python
from typing import Dict, Any

async def get_agent_by_id(agent_id: str) -> Dict[str, Any]:
    """Get agent by ID."""
    pass
```

**Parameters:**

- `agent_id` (str): The agent_id to search for

**Returns:** Dictionary containing agent data

**Raises:**

- `AgentNotFoundError`: If the agent is not found

**Example:**

```python
async def example():
    agent = await registry.get_agent_by_id("01-core-backend-developer")
    print(f"Agent: {agent['name']}")
    print(f"Description: {agent['description']}")
    print(f"Capabilities: {agent['capabilities']}")
```

______________________________________________________________________

#### get_agent_by_type()

Retrieve an agent by its agent_type.

**Signature:**

```python
async def get_agent_by_type(agent_type: str) -> Dict[str, Any]
```

**Parameters:**

- `agent_type` (str): The agent_type to search for

**Returns:** Dictionary containing agent data

**Raises:**

- `AgentNotFoundError`: If the agent is not found

**Example:**

```python
agent = await registry.get_agent_by_type("backend-developer")
```

______________________________________________________________________

#### get_agent_by_uuid()

Retrieve an agent by its UUID.

**Signature:**

```python
async def get_agent_by_uuid(uuid: UUID) -> Dict[str, Any]
```

**Parameters:**

- `uuid` (UUID): The agent's UUID

**Returns:** Dictionary containing agent data

**Raises:**

- `AgentNotFoundError`: If the agent is not found

**Example:**

```python
from uuid import UUID
agent = await registry.get_agent_by_uuid(
    UUID("550e8400-e29b-41d4-a716-446655440000")
)
```

______________________________________________________________________

#### update_agent()

Update an agent's fields.

**Signature:**

```python
async def update_agent(agent_id: str, **fields: Any) -> None
```

**Parameters:**

- `agent_id` (str): The agent_id to update
- `**fields`: Fields to update (any field from the agents table)

**Raises:**

- `AgentNotFoundError`: If the agent is not found

**Example:**

```python
await registry.update_agent(
    "01-core-backend-developer",
    description="Updated description",
    capabilities=["api-development", "microservices", "database-design"],
    metadata={"version": "2.0", "updated": True}
)
```

______________________________________________________________________

#### delete_agent()

Delete an agent from the registry.

**Signature:**

```python
async def delete_agent(agent_id: str) -> None
```

**Parameters:**

- `agent_id` (str): The agent_id to delete

**Raises:**

- `AgentNotFoundError`: If the agent is not found

**Example:**

```python
await registry.delete_agent("01-core-backend-developer")
```

______________________________________________________________________

### Query Operations

#### list_agents()

List agents with optional filtering and pagination.

**Signature:**

```python
async def list_agents(
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]
```

**Parameters:**

- `category` (str, optional): Filter by category
- `limit` (int): Maximum number of results (default: 100)
- `offset` (int): Offset for pagination (default: 0)

**Returns:** List of agent dictionaries

**Example:**

```python
# Get all agents
all_agents = await registry.list_agents()

# Get agents in specific category
core_agents = await registry.list_agents(category="Core Development")

# Get paginated results
page1 = await registry.list_agents(limit=20, offset=0)
page2 = await registry.list_agents(limit=20, offset=20)
```

______________________________________________________________________

#### search_agents()

Full-text search on agent descriptions and keywords.

**Signature:**

```python
async def search_agents(
    query: str,
    limit: int = 10,
) -> List[Dict[str, Any]]
```

**Parameters:**

- `query` (str): Search query
- `limit` (int): Maximum number of results (default: 10)

**Returns:** List of matching agent dictionaries, ranked by relevance

**Example:**

```python
# Search for backend-related agents
results = await registry.search_agents("backend api development")

for agent in results:
    print(f"{agent['name']}: {agent['description']}")
```

______________________________________________________________________

#### similarity_search()

Semantic search using vector embeddings (pgvector).

**Signature:**

```python
async def similarity_search(
    embedding: List[float],
    limit: int = 10,
    threshold: float = 0.5,
) -> List[Tuple[Dict[str, Any], float]]
```

**Parameters:**

- `embedding` (List\[float\]): Query embedding vector (384-dim)
- `limit` (int): Maximum number of results (default: 10)
- `threshold` (float): Minimum similarity threshold 0.0-1.0 (default: 0.5)

**Returns:** List of tuples (agent_dict, similarity_score) sorted by similarity

**Example:**

```python
# Generate embedding for query
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
query_embedding = model.encode("backend API development").tolist()

# Search for similar agents
results = await registry.similarity_search(
    embedding=query_embedding,
    limit=5,
    threshold=0.7
)

for agent, similarity in results:
    print(f"{agent['name']}: {similarity:.2%} match")
```

______________________________________________________________________

#### get_agent_count()

Get the total number of agents in the registry.

**Signature:**

```python
async def get_agent_count(category: Optional[str] = None) -> int
```

**Parameters:**

- `category` (str, optional): Optional category filter

**Returns:** Total agent count

**Example:**

```python
total = await registry.get_agent_count()
print(f"Total agents: {total}")

core_count = await registry.get_agent_count(category="Core Development")
print(f"Core agents: {core_count}")
```

______________________________________________________________________

#### get_categories()

Get all unique categories in the registry.

**Signature:**

```python
async def get_categories() -> List[str]
```

**Returns:** List of category names

**Example:**

```python
categories = await registry.get_categories()
print("Available categories:", categories)
```

______________________________________________________________________

### Bulk Operations

#### bulk_insert_agents()

Bulk insert agents into the registry.

**Signature:**

```python
async def bulk_insert_agents(
    agents: List[Dict[str, Any]],
    batch_size: int = 100,
) -> int
```

**Parameters:**

- `agents` (List\[Dict\]): List of agent dictionaries
- `batch_size` (int): Number of agents per batch (default: 100)

**Returns:** Number of agents successfully inserted

**Note:** Duplicates are skipped without error

**Example:**

```python
agents_to_insert = [
    {
        "agent_id": "agent-1",
        "agent_type": "type-1",
        "name": "Agent 1",
        "display_name": "Agent 1",
        "category": "Test",
        "description": "Test agent 1",
        "file_path": "/path/to/agent1.md",
    },
    # ... more agents
]

count = await registry.bulk_insert_agents(agents_to_insert)
print(f"Inserted {count} agents")
```

______________________________________________________________________

### Utility Methods

#### health_check()

Perform a health check on the registry.

**Signature:**

```python
async def health_check() -> Dict[str, Any]
```

**Returns:** Dictionary with health check results

**Example:**

```python
health = await registry.health_check()
print(f"Status: {health['status']}")
print(f"pgvector installed: {health['pgvector_installed']}")
print(f"Agent count: {health['agent_count']}")
print(f"Database size: {health['database_size']}")
```

______________________________________________________________________

## Helper Functions

### load_agents_from_index()

Load agents from index.json file into the registry.

**Signature:**

```python
async def load_agents_from_index(
    index_path: str | Path,
    registry: AgentRegistry,
) -> int
```

**Parameters:**

- `index_path` (str | Path): Path to the index.json file
- `registry` (AgentRegistry): Registry instance

**Returns:** Number of agents loaded

**Raises:**

- `FileNotFoundError`: If index file doesn't exist

**Example:**

```python
from plugins.mycelium_core.registry import load_agents_from_index

async with AgentRegistry(connection_string) as registry:
    count = await load_agents_from_index(
        "plugins/mycelium-core/agents/index.json",
        registry
    )
    print(f"Loaded {count} agents")
```

______________________________________________________________________

## Exceptions

### AgentRegistryError

Base exception for all registry errors.

### AgentNotFoundError

Raised when an agent is not found in the registry.

**Example:**

```python
try:
    agent = await registry.get_agent_by_id("nonexistent")
except AgentNotFoundError as e:
    print(f"Agent not found: {e}")
```

### AgentAlreadyExistsError

Raised when attempting to create an agent that already exists.

**Example:**

```python
try:
    await registry.create_agent(...)
except AgentAlreadyExistsError as e:
    print(f"Agent already exists: {e}")
```

______________________________________________________________________

## Usage Examples

### Complete Workflow Example

```python
import asyncio
from plugins.mycelium_core.registry import AgentRegistry, load_agents_from_index

async def main():
    # Initialize registry
    async with AgentRegistry() as registry:
        # Load agents from index.json
        count = await load_agents_from_index(
            "plugins/mycelium-core/agents/index.json",
            registry
        )
        print(f"Loaded {count} agents")

        # Get agent count by category
        categories = await registry.get_categories()
        for category in categories:
            count = await registry.get_agent_count(category=category)
            print(f"{category}: {count} agents")

        # Search for agents
        results = await registry.search_agents("backend development")
        print(f"\nFound {len(results)} agents matching 'backend development':")
        for agent in results[:5]:
            print(f"  - {agent['name']}: {agent['description']}")

        # Get specific agent
        agent = await registry.get_agent_by_type("backend-developer")
        print(f"\nAgent details:")
        print(f"  Name: {agent['display_name']}")
        print(f"  Category: {agent['category']}")
        print(f"  Tools: {', '.join(agent['tools'])}")
        print(f"  Usage count: {agent['usage_count']}")

asyncio.run(main())
```

### Vector Similarity Search Example

```python
from sentence_transformers import SentenceTransformer
from plugins.mycelium_core.registry import AgentRegistry

async def semantic_agent_discovery(query: str):
    # Initialize embedding model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    async with AgentRegistry() as registry:
        # Generate query embedding
        query_embedding = model.encode(query).tolist()

        # Perform similarity search
        results = await registry.similarity_search(
            embedding=query_embedding,
            limit=5,
            threshold=0.6
        )

        print(f"Top agents for '{query}':")
        for agent, similarity in results:
            print(f"  {similarity:.1%} - {agent['name']}: {agent['description']}")

# Usage
import asyncio
asyncio.run(semantic_agent_discovery(
    "I need to build a REST API with authentication"
))
```

### Performance Monitoring Example

```python
import time
from plugins.mycelium_core.registry import AgentRegistry

async def benchmark_queries():
    async with AgentRegistry() as registry:
        # Benchmark get_agent_by_id
        start = time.time()
        await registry.get_agent_by_id("01-core-backend-developer")
        duration = (time.time() - start) * 1000
        print(f"get_agent_by_id: {duration:.2f}ms")

        # Benchmark search
        start = time.time()
        await registry.search_agents("backend")
        duration = (time.time() - start) * 1000
        print(f"search_agents: {duration:.2f}ms")

        # Health check
        health = await registry.health_check()
        print(f"Health: {health['status']}")
        print(f"Agents: {health['agent_count']}")
        print(f"DB size: {health['database_size']}")

import asyncio
asyncio.run(benchmark_queries())
```

______________________________________________________________________

## Performance Tuning

### Index Optimization

The HNSW index parameters can be tuned for your workload:

```sql
-- More accuracy, slower queries
CREATE INDEX idx_agents_embedding_hnsw
ON agents USING hnsw (embedding vector_cosine_ops)
WITH (m = 32, ef_construction = 128);

-- Faster queries, less accuracy
CREATE INDEX idx_agents_embedding_hnsw
ON agents USING hnsw (embedding vector_cosine_ops)
WITH (m = 8, ef_construction = 32);
```

### Connection Pool Tuning

```python
# For high-concurrency workloads
pool = await asyncpg.create_pool(
    connection_string,
    min_size=10,
    max_size=50,
    command_timeout=30,
)
registry = AgentRegistry(pool=pool)
```

### Query Performance Tips

1. **Use indexes**: The schema includes indexes on commonly queried fields
1. **Limit results**: Always use `limit` parameter to prevent large result sets
1. **Use specific queries**: `get_agent_by_id` is faster than `search_agents`
1. **Cache results**: Cache frequently accessed agents in application layer
1. **Batch operations**: Use `bulk_insert_agents` for loading multiple agents

______________________________________________________________________

## Troubleshooting

### Common Issues

**Issue: "pgvector extension not found"**

```bash
# Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
```

**Issue: "Connection pool timeout"**

```python
# Increase pool size or timeout
pool = await asyncpg.create_pool(
    connection_string,
    max_size=20,
    command_timeout=120
)
```

**Issue: "Slow similarity search"**

```sql
-- Rebuild HNSW index with better parameters
DROP INDEX idx_agents_embedding_hnsw;
CREATE INDEX idx_agents_embedding_hnsw
ON agents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Refresh statistics
ANALYZE agents;
```

______________________________________________________________________

## Support

For issues or questions:

- Documentation: `/docs/api/registry-api.md`
- Source: `/plugins/mycelium-core/registry/`
- Tests: `/tests/unit/test_registry.py`
