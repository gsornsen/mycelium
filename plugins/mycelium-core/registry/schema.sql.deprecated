-- Agent Registry Schema for Mycelium
-- PostgreSQL 15+ with pgvector extension
-- Supports 384-dimensional embeddings for semantic search

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create schema version tracking table
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    description TEXT NOT NULL
);

-- Main agents table with vector embeddings
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id TEXT NOT NULL UNIQUE,  -- e.g., "01-core-backend-developer"
    agent_type TEXT NOT NULL UNIQUE,  -- e.g., "backend-developer"
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,

    -- Capabilities and tools
    capabilities TEXT[] DEFAULT '{}',
    tools TEXT[] DEFAULT '{}',
    keywords TEXT[] DEFAULT '{}',

    -- Vector embedding for semantic search (384 dimensions for all-MiniLM-L6-v2)
    embedding vector(384),

    -- Metadata
    file_path TEXT NOT NULL,
    estimated_tokens INTEGER,
    metadata JSONB DEFAULT '{}',

    -- Performance metrics
    avg_response_time_ms INTEGER,
    success_rate DECIMAL(5,2),
    usage_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_used_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_success_rate CHECK (success_rate >= 0 AND success_rate <= 100),
    CONSTRAINT valid_usage_count CHECK (usage_count >= 0)
);

-- Create indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_agents_agent_type ON agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_category ON agents(category);
CREATE INDEX IF NOT EXISTS idx_agents_capabilities ON agents USING GIN(capabilities);
CREATE INDEX IF NOT EXISTS idx_agents_tools ON agents USING GIN(tools);
CREATE INDEX IF NOT EXISTS idx_agents_keywords ON agents USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_agents_created_at ON agents(created_at);
CREATE INDEX IF NOT EXISTS idx_agents_updated_at ON agents(updated_at);

-- HNSW index for fast vector similarity search
-- m = 16: number of bi-directional links per element (higher = better recall, more memory)
-- ef_construction = 64: size of dynamic candidate list (higher = better index quality, slower build)
CREATE INDEX IF NOT EXISTS idx_agents_embedding_hnsw
ON agents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Agent dependencies table (for tracking agent prerequisites)
CREATE TABLE IF NOT EXISTS agent_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    depends_on_agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    dependency_type TEXT NOT NULL,  -- 'required', 'optional', 'recommended'
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CONSTRAINT no_self_dependency CHECK (agent_id != depends_on_agent_id),
    CONSTRAINT valid_dependency_type CHECK (dependency_type IN ('required', 'optional', 'recommended')),
    UNIQUE(agent_id, depends_on_agent_id)
);

CREATE INDEX IF NOT EXISTS idx_agent_dependencies_agent_id ON agent_dependencies(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_dependencies_depends_on ON agent_dependencies(depends_on_agent_id);

-- Agent usage tracking table
CREATE TABLE IF NOT EXISTS agent_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    workflow_id UUID,
    session_id TEXT,

    -- Usage details
    invoked_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL,  -- 'in_progress', 'completed', 'failed', 'timeout'
    response_time_ms INTEGER,

    -- Context
    task_description TEXT,
    context_metadata JSONB DEFAULT '{}',

    -- Error tracking
    error_message TEXT,
    error_code TEXT,

    CONSTRAINT valid_status CHECK (status IN ('in_progress', 'completed', 'failed', 'timeout')),
    CONSTRAINT valid_response_time CHECK (response_time_ms IS NULL OR response_time_ms >= 0)
);

CREATE INDEX IF NOT EXISTS idx_agent_usage_agent_id ON agent_usage(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_usage_workflow_id ON agent_usage(workflow_id);
CREATE INDEX IF NOT EXISTS idx_agent_usage_invoked_at ON agent_usage(invoked_at);
CREATE INDEX IF NOT EXISTS idx_agent_usage_status ON agent_usage(status);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER update_agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to update agent metrics based on usage
CREATE OR REPLACE FUNCTION update_agent_metrics()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND NEW.response_time_ms IS NOT NULL THEN
        UPDATE agents
        SET
            usage_count = usage_count + 1,
            last_used_at = NEW.completed_at,
            avg_response_time_ms = COALESCE(
                (avg_response_time_ms * usage_count + NEW.response_time_ms) / (usage_count + 1),
                NEW.response_time_ms
            ),
            success_rate = COALESCE(
                ((success_rate * usage_count / 100.0) + 1) / (usage_count + 1) * 100,
                100.0
            )
        WHERE id = NEW.agent_id;
    ELSIF NEW.status = 'failed' THEN
        UPDATE agents
        SET
            usage_count = usage_count + 1,
            last_used_at = NEW.completed_at,
            success_rate = COALESCE(
                ((success_rate * usage_count / 100.0)) / (usage_count + 1) * 100,
                0.0
            )
        WHERE id = NEW.agent_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for INSERT operations (no OLD reference)
CREATE TRIGGER update_agent_metrics_on_insert
    AFTER INSERT ON agent_usage
    FOR EACH ROW
    WHEN (NEW.status IN ('completed', 'failed'))
    EXECUTE FUNCTION update_agent_metrics();

-- Trigger for UPDATE operations (can reference OLD)
CREATE TRIGGER update_agent_metrics_on_update
    AFTER UPDATE ON agent_usage
    FOR EACH ROW
    WHEN (NEW.status IN ('completed', 'failed') AND OLD.status = 'in_progress')
    EXECUTE FUNCTION update_agent_metrics();

-- Insert initial schema version
INSERT INTO schema_version (version, description)
VALUES (1, 'Initial agent registry schema with pgvector support')
ON CONFLICT (version) DO NOTHING;

-- Create materialized view for agent statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS agent_statistics AS
SELECT
    a.id,
    a.agent_type,
    a.name,
    a.category,
    a.usage_count,
    a.success_rate,
    a.avg_response_time_ms,
    a.last_used_at,
    COUNT(DISTINCT au.workflow_id) as workflow_count,
    COUNT(CASE WHEN au.status = 'completed' THEN 1 END) as successful_invocations,
    COUNT(CASE WHEN au.status = 'failed' THEN 1 END) as failed_invocations,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY au.response_time_ms) as p95_response_time_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY au.response_time_ms) as p99_response_time_ms
FROM agents a
LEFT JOIN agent_usage au ON a.id = au.agent_id
GROUP BY a.id, a.agent_type, a.name, a.category, a.usage_count,
         a.success_rate, a.avg_response_time_ms, a.last_used_at;

CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_statistics_id ON agent_statistics(id);

-- Grant permissions (adjust as needed for your environment)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mycelium_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mycelium_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO mycelium_app;
