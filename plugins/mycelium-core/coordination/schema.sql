-- Coordination Schema for Mycelium
-- PostgreSQL 14+
--
-- This schema supports multi-agent workflow coordination, including:
-- - Event tracking for inter-agent communication
-- - Workflow state persistence and history
-- - Task state management
-- - State history for rollback capabilities

-- ============================================================================
-- COORDINATION EVENTS
-- ============================================================================
CREATE TABLE IF NOT EXISTS coordination_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    source VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_id VARCHAR(255),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_coordination_events_event_type ON coordination_events(event_type);
CREATE INDEX idx_coordination_events_agent_id ON coordination_events(agent_id);
CREATE INDEX idx_coordination_events_timestamp ON coordination_events(timestamp DESC);
CREATE INDEX idx_coordination_events_correlation ON coordination_events(correlation_id);
CREATE INDEX idx_coordination_events_payload ON coordination_events USING GIN(payload);

-- ============================================================================
-- WORKFLOW STATES
-- ============================================================================
CREATE TABLE IF NOT EXISTS workflow_states (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    context JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    version INTEGER NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_workflow_states_status ON workflow_states(status);
CREATE INDEX idx_workflow_states_created_at ON workflow_states(created_at DESC);
CREATE INDEX idx_workflow_states_updated_at ON workflow_states(updated_at DESC);
CREATE INDEX idx_workflow_states_context ON workflow_states USING GIN(context);

CREATE OR REPLACE FUNCTION update_workflow_state_version()
RETURNS TRIGGER AS $$
BEGIN
    NEW.version = OLD.version + 1;
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER workflow_states_version_trigger
    BEFORE UPDATE ON workflow_states
    FOR EACH ROW
    EXECUTE FUNCTION update_workflow_state_version();

-- ============================================================================
-- TASK STATES
-- ============================================================================
CREATE TABLE IF NOT EXISTS task_states (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    workflow_id VARCHAR(255) NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    result JSONB,
    error TEXT,
    metadata JSONB DEFAULT '{}',
    version INTEGER NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (workflow_id) REFERENCES workflow_states(workflow_id) ON DELETE CASCADE
);

CREATE INDEX idx_task_states_workflow_id ON task_states(workflow_id);
CREATE INDEX idx_task_states_agent_id ON task_states(agent_id);
CREATE INDEX idx_task_states_status ON task_states(status);
CREATE INDEX idx_task_states_created_at ON task_states(created_at DESC);
CREATE INDEX idx_task_states_updated_at ON task_states(updated_at DESC);
CREATE INDEX idx_task_states_result ON task_states USING GIN(result);
CREATE INDEX idx_task_states_workflow_status ON task_states(workflow_id, status);

CREATE OR REPLACE FUNCTION update_task_state_version()
RETURNS TRIGGER AS $$
BEGIN
    NEW.version = OLD.version + 1;
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER task_states_version_trigger
    BEFORE UPDATE ON task_states
    FOR EACH ROW
    EXECUTE FUNCTION update_task_state_version();

-- ============================================================================
-- WORKFLOW STATE HISTORY
-- ============================================================================
CREATE TABLE IF NOT EXISTS workflow_state_history (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    context JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    version INTEGER NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    changed_by VARCHAR(255),
    change_reason TEXT,
    FOREIGN KEY (workflow_id) REFERENCES workflow_states(workflow_id) ON DELETE CASCADE
);

CREATE INDEX idx_workflow_state_history_workflow_id ON workflow_state_history(workflow_id);
CREATE INDEX idx_workflow_state_history_changed_at ON workflow_state_history(changed_at DESC);
CREATE INDEX idx_workflow_state_history_version ON workflow_state_history(workflow_id, version);

CREATE OR REPLACE FUNCTION create_workflow_state_history()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO workflow_state_history (
        workflow_id,
        status,
        context,
        metadata,
        version,
        changed_at
    ) VALUES (
        OLD.workflow_id,
        OLD.status,
        OLD.context,
        OLD.metadata,
        OLD.version,
        OLD.updated_at
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER workflow_states_history_trigger
    AFTER UPDATE ON workflow_states
    FOR EACH ROW
    EXECUTE FUNCTION create_workflow_state_history();

-- ============================================================================
-- TASK STATE HISTORY
-- ============================================================================
CREATE TABLE IF NOT EXISTS task_state_history (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL,
    workflow_id VARCHAR(255) NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    result JSONB,
    error TEXT,
    metadata JSONB DEFAULT '{}',
    version INTEGER NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    changed_by VARCHAR(255),
    change_reason TEXT,
    FOREIGN KEY (task_id) REFERENCES task_states(task_id) ON DELETE CASCADE
);

CREATE INDEX idx_task_state_history_task_id ON task_state_history(task_id);
CREATE INDEX idx_task_state_history_workflow_id ON task_state_history(workflow_id);
CREATE INDEX idx_task_state_history_changed_at ON task_state_history(changed_at DESC);
CREATE INDEX idx_task_state_history_version ON task_state_history(task_id, version);

CREATE OR REPLACE FUNCTION create_task_state_history()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO task_state_history (
        task_id,
        workflow_id,
        agent_id,
        status,
        result,
        error,
        metadata,
        version,
        changed_at
    ) VALUES (
        OLD.task_id,
        OLD.workflow_id,
        OLD.agent_id,
        OLD.status,
        OLD.result,
        OLD.error,
        OLD.metadata,
        OLD.version,
        OLD.updated_at
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER task_states_history_trigger
    AFTER UPDATE ON task_states
    FOR EACH ROW
    EXECUTE FUNCTION create_task_state_history();

-- ============================================================================
-- UTILITY VIEWS
-- ============================================================================
CREATE OR REPLACE VIEW active_workflows AS
SELECT
    ws.workflow_id,
    ws.status,
    ws.created_at,
    ws.started_at,
    COUNT(ts.task_id) as total_tasks,
    COUNT(CASE WHEN ts.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN ts.status = 'failed' THEN 1 END) as failed_tasks,
    COUNT(CASE WHEN ts.status = 'running' THEN 1 END) as running_tasks,
    COUNT(CASE WHEN ts.status = 'pending' THEN 1 END) as pending_tasks
FROM workflow_states ws
LEFT JOIN task_states ts ON ws.workflow_id = ts.workflow_id
WHERE ws.status IN ('pending', 'running')
GROUP BY ws.workflow_id, ws.status, ws.created_at, ws.started_at;

CREATE OR REPLACE VIEW workflow_execution_metrics AS
SELECT
    workflow_id,
    status,
    EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_seconds,
    EXTRACT(EPOCH FROM (completed_at - created_at)) as total_time_seconds,
    created_at,
    started_at,
    completed_at
FROM workflow_states
WHERE started_at IS NOT NULL;

-- Analyze tables for query optimization
ANALYZE coordination_events;
ANALYZE workflow_states;
ANALYZE task_states;
ANALYZE workflow_state_history;
ANALYZE task_state_history;
