# Database Migrations

This directory contains database migrations managed by Alembic for the Mycelium project.

## Overview

The migrations handle the creation and versioning of all database schemas including:

- Agent registry tables (agents, agent_usage, agent_dependencies)
- Coordination tables (workflow_states, task_states, coordination_events)
- Performance tracking and statistics
- Vector embeddings for semantic search (using pgvector)

## Prerequisites

- PostgreSQL 15+ with pgvector extension
- Python dependencies: `alembic`, `sqlalchemy`, `psycopg2-binary`

## Configuration

Migrations use the `DATABASE_URL` environment variable if set, otherwise fall back to the default in `alembic.ini`:

```bash
export DATABASE_URL="postgresql://user:password@host:port/database"
```

## Running Migrations

### Apply all migrations (upgrade to latest)

```bash
uv run alembic upgrade head
```

### Check current migration version

```bash
uv run alembic current
```

### View migration history

```bash
uv run alembic history
```

### Rollback migrations

```bash
# Rollback one migration
uv run alembic downgrade -1

# Rollback to specific revision
uv run alembic downgrade <revision>

# Rollback all migrations
uv run alembic downgrade base
```

### Preview migration SQL without applying

```bash
uv run alembic upgrade head --sql
```

## Creating New Migrations

### Auto-generate migration from model changes

```bash
uv run alembic revision --autogenerate -m "Description of changes"
```

### Create empty migration

```bash
uv run alembic revision -m "Description of changes"
```

## CI/CD Integration

The GitHub Actions workflow automatically:

1. Runs migrations on test databases
1. Verifies migration idempotency (can be run multiple times safely)
1. Tests rollback capabilities
1. Validates schema integrity

See `.github/workflows/ci.yml` for the migration test job.

## Schema Overview

### Registry Tables

- `agents` - Main agent registry with vector embeddings
- `agent_dependencies` - Agent prerequisite tracking
- `agent_usage` - Usage metrics and performance tracking
- `agent_statistics` - Materialized view for analytics

### Coordination Tables

- `workflow_states` - Workflow execution state
- `task_states` - Individual task state within workflows
- `workflow_state_history` - State versioning for rollback
- `coordination_events` - Event tracking for observability

### Extensions Used

- `uuid-ossp` - UUID generation
- `vector` - pgvector for embedding storage and similarity search

## Troubleshooting

### Migration fails with "extension does not exist"

Ensure pgvector is installed:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Migration history out of sync

Check and fix the alembic_version table:

```bash
uv run alembic stamp head  # Mark current version as head
```

### Testing migrations locally

```bash
# Create test database
createdb mycelium_test

# Run migrations
DATABASE_URL="postgresql://localhost/mycelium_test" uv run alembic upgrade head

# Verify tables
psql mycelium_test -c "\dt"

# Test rollback
DATABASE_URL="postgresql://localhost/mycelium_test" uv run alembic downgrade base

# Clean up
dropdb mycelium_test
```
