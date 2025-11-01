# Mycelium Agent Registry

A centralized agent registry system with PostgreSQL backend and pgvector support for semantic search.

## Features

- **PostgreSQL 15+ Backend**: Reliable, scalable storage with ACID guarantees
- **Vector Embeddings**: 384-dimensional embeddings for semantic search using pgvector
- **High Performance**: \<100ms query performance with optimized indexes
- **HNSW Index**: Fast approximate nearest neighbor search for similarity queries
- **Async API**: Built on asyncpg for high-concurrency workloads
- **Comprehensive Metadata**: Track capabilities, tools, keywords, and performance metrics
- **Usage Tracking**: Automatic metrics collection for agent invocations
- **Bulk Operations**: Efficient batch loading from index.json

## Quick Start

### Prerequisites

1. **PostgreSQL 15+ with pgvector extension**

```bash
# Using Docker (recommended)
docker run -d \
  --name mycelium-postgres \
  -e POSTGRES_DB=mycelium_registry \
  -e POSTGRES_USER=mycelium \
  -e POSTGRES_PASSWORD=secure_password \
  -p 5432:5432 \
  ankane/pgvector:latest
```

2. **Python Dependencies**

```bash
pip install asyncpg
```

### Setup

1. **Apply Database Schema**

```bash
psql -d mycelium_registry -f schema.sql
```

2. **Set Environment Variable**

```bash
export DATABASE_URL="postgresql://mycelium:secure_password@localhost:5432/mycelium_registry"
```

3. **Populate Registry**

```python
import asyncio
from plugins.mycelium_core.registry import AgentRegistry, load_agents_from_index

async def populate():
    async with AgentRegistry() as registry:
        count = await load_agents_from_index(
            "plugins/mycelium-core/agents/index.json",
            registry
        )
        print(f"Loaded {count} agents")

asyncio.run(populate())
```

Or use the CLI script:

```bash
cd plugins/mycelium-core/registry
python populate.py
```

## Usage Examples

### Basic CRUD Operations

```python
from plugins.mycelium_core.registry import AgentRegistry

async with AgentRegistry() as registry:
    # Create an agent
    agent_uuid = await registry.create_agent(
        agent_id="my-custom-agent",
        agent_type="custom-agent",
        name="Custom Agent",
        display_name="Custom Agent",
        category="Custom",
        description="My custom agent",
        file_path="/path/to/agent.md",
        capabilities=["capability1", "capability2"],
        tools=["Bash", "Read"],
        keywords=["custom", "agent"],
    )

    # Retrieve an agent
    agent = await registry.get_agent_by_id("my-custom-agent")
    print(f"Agent: {agent['name']}")

    # Update an agent
    await registry.update_agent(
        "my-custom-agent",
        description="Updated description"
    )

    # Delete an agent
    await registry.delete_agent("my-custom-agent")
```

### Search Operations

```python
async with AgentRegistry() as registry:
    # Full-text search
    results = await registry.search_agents("backend api")
    for agent in results:
        print(f"{agent['name']}: {agent['description']}")

    # List all agents in a category
    core_agents = await registry.list_agents(category="Core Development")

    # Get agent count
    total = await registry.get_agent_count()
    print(f"Total agents: {total}")
```

### Vector Similarity Search

```python
from sentence_transformers import SentenceTransformer

# Generate embedding
model = SentenceTransformer('all-MiniLM-L6-v2')
query_embedding = model.encode("backend API development").tolist()

async with AgentRegistry() as registry:
    # Search by semantic similarity
    results = await registry.similarity_search(
        embedding=query_embedding,
        limit=5,
        threshold=0.7
    )

    for agent, similarity in results:
        print(f"{similarity:.1%} - {agent['name']}")
```

## Architecture

### Database Schema

```
agents (main table)
├── id (UUID, PK)
├── agent_id (TEXT, UNIQUE)
├── agent_type (TEXT, UNIQUE)
├── name, display_name, category
├── description
├── capabilities[] (TEXT[])
├── tools[] (TEXT[])
├── keywords[] (TEXT[])
├── embedding (vector(384))
├── metadata (JSONB)
├── performance metrics
└── timestamps

agent_dependencies
├── id (UUID, PK)
├── agent_id (FK → agents)
├── depends_on_agent_id (FK → agents)
└── dependency_type

agent_usage (tracking)
├── id (UUID, PK)
├── agent_id (FK → agents)
├── workflow_id
├── invoked_at, completed_at
├── status, response_time_ms
└── error tracking

agent_statistics (materialized view)
└── aggregated metrics per agent
```

### Indexes

- **B-Tree indexes**: agent_type, category, timestamps
- **GIN indexes**: capabilities, tools, keywords (array search)
- **HNSW index**: embedding vector (cosine similarity)

### Performance Characteristics

| Operation         | Target  | Actual (100 agents) |
| ----------------- | ------- | ------------------- |
| get_agent_by_id   | \<100ms | ~5-10ms             |
| search_agents     | \<100ms | ~15-30ms            |
| similarity_search | \<200ms | ~50-100ms           |
| bulk_insert (100) | \<10s   | ~2-5s               |

## API Reference

See [API Documentation](../../../docs/api/registry-api.md) for complete API reference.

### Core Classes

- **AgentRegistry**: Main registry class with all CRUD operations
- **AgentRegistryError**: Base exception class
- **AgentNotFoundError**: Raised when agent not found
- **AgentAlreadyExistsError**: Raised on duplicate creation

### Key Methods

- `create_agent()`: Add new agent
- `get_agent_by_id()`, `get_agent_by_type()`, `get_agent_by_uuid()`: Retrieve agents
- `update_agent()`: Update agent fields
- `delete_agent()`: Remove agent
- `list_agents()`: List with filtering and pagination
- `search_agents()`: Full-text search
- `similarity_search()`: Vector similarity search
- `bulk_insert_agents()`: Batch insert
- `health_check()`: System health status

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Set test database URL
export TEST_DATABASE_URL="postgresql://localhost:5432/mycelium_test"

# Run tests
pytest tests/unit/test_registry.py -v

# With coverage
pytest tests/unit/test_registry.py -v --cov=plugins/mycelium_core/registry --cov-report=html
```

### Test Coverage

Current coverage: >90%

See `tests/unit/test_registry.py` for comprehensive test suite including:

- CRUD operations
- Query operations
- Vector similarity search
- Bulk operations
- Error handling
- Performance benchmarks

### Performance Testing

```bash
# Run performance benchmarks
pytest tests/unit/test_registry.py::TestPerformance -v
```

## Troubleshooting

### "pgvector extension not found"

```sql
-- Install pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Slow Similarity Search

```sql
-- Check if HNSW index exists
SELECT indexname FROM pg_indexes WHERE tablename = 'agents';

-- Rebuild with optimized parameters
DROP INDEX IF EXISTS idx_agents_embedding_hnsw;
CREATE INDEX idx_agents_embedding_hnsw
ON agents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Update statistics
ANALYZE agents;
```

### Connection Pool Exhaustion

```python
# Increase pool size
registry = AgentRegistry(connection_string)
# Pool created with min_size=2, max_size=10 by default

# Or use custom pool
import asyncpg
pool = await asyncpg.create_pool(
    connection_string,
    min_size=10,
    max_size=50
)
registry = AgentRegistry(pool=pool)
```

## Migration Guide

### Adding New Fields

1. Create migration SQL file in `migrations/`
1. Update schema.sql
1. Update registry.py to handle new fields
1. Add tests for new functionality
1. Update documentation

Example migration:

```sql
-- migrations/002_add_priority.sql
ALTER TABLE agents ADD COLUMN priority INTEGER DEFAULT 0;
CREATE INDEX idx_agents_priority ON agents(priority);
```

### Updating HNSW Parameters

```sql
-- For better accuracy (slower)
DROP INDEX idx_agents_embedding_hnsw;
CREATE INDEX idx_agents_embedding_hnsw
ON agents USING hnsw (embedding vector_cosine_ops)
WITH (m = 32, ef_construction = 128);

-- For faster queries (less accurate)
DROP INDEX idx_agents_embedding_hnsw;
CREATE INDEX idx_agents_embedding_hnsw
ON agents USING hnsw (embedding vector_cosine_ops)
WITH (m = 8, ef_construction = 32);
```

## Contributing

1. Write tests for new features
1. Ensure >90% test coverage
1. Update documentation
1. Follow existing code style
1. Run linting: `ruff check .`
1. Run type checking: `mypy plugins/mycelium-core/registry/`

## License

MIT License - See LICENSE file for details
