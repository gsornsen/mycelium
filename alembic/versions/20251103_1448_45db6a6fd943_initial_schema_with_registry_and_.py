"""Initial schema with registry and coordination tables.

Revision ID: 45db6a6fd943
Revises:
Create Date: 2025-11-03 14:48:56.234652

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "45db6a6fd943"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all initial tables for mycelium registry and coordination."""
    # Enable required extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')

    # Create schema version tracking table
    op.create_table(
        "schema_version",
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "applied_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("version"),
    )

    # Main agents table with vector embeddings
    op.create_table(
        "agents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("agent_id", sa.Text(), nullable=False),
        sa.Column("agent_type", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("capabilities", postgresql.ARRAY(sa.Text()), server_default="{}"),
        sa.Column("tools", postgresql.ARRAY(sa.Text()), server_default="{}"),
        sa.Column("keywords", postgresql.ARRAY(sa.Text()), server_default="{}"),
        # Vector column - we'll add this with raw SQL due to pgvector type
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("estimated_tokens", sa.Integer()),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="{}"),
        sa.Column("avg_response_time_ms", sa.Integer()),
        sa.Column("success_rate", sa.Numeric(5, 2)),
        sa.Column("usage_count", sa.Integer(), server_default="0"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id"),
        sa.UniqueConstraint("agent_type"),
        sa.CheckConstraint("success_rate >= 0 AND success_rate <= 100", name="valid_success_rate"),
        sa.CheckConstraint("usage_count >= 0", name="valid_usage_count"),
    )

    # Add vector column using raw SQL
    op.execute("ALTER TABLE agents ADD COLUMN embedding vector(384)")

    # Create indexes for agents table
    op.create_index("idx_agents_agent_type", "agents", ["agent_type"])
    op.create_index("idx_agents_category", "agents", ["category"])
    op.create_index("idx_agents_capabilities", "agents", ["capabilities"], postgresql_using="gin")
    op.create_index("idx_agents_tools", "agents", ["tools"], postgresql_using="gin")
    op.create_index("idx_agents_keywords", "agents", ["keywords"], postgresql_using="gin")
    op.create_index("idx_agents_created_at", "agents", ["created_at"])
    op.create_index("idx_agents_updated_at", "agents", ["updated_at"])

    # HNSW index for vector similarity search
    op.execute(
        """
        CREATE INDEX idx_agents_embedding_hnsw
        ON agents USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )

    # Agent dependencies table
    op.create_table(
        "agent_dependencies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("depends_on_agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dependency_type", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["depends_on_agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", "depends_on_agent_id"),
        sa.CheckConstraint("agent_id != depends_on_agent_id", name="no_self_dependency"),
        sa.CheckConstraint(
            "dependency_type IN ('required', 'optional', 'recommended')",
            name="valid_dependency_type",
        ),
    )

    op.create_index("idx_agent_dependencies_agent_id", "agent_dependencies", ["agent_id"])
    op.create_index("idx_agent_dependencies_depends_on", "agent_dependencies", ["depends_on_agent_id"])

    # Agent usage tracking table
    op.create_table(
        "agent_usage",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True)),
        sa.Column("session_id", sa.Text()),
        sa.Column(
            "invoked_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("response_time_ms", sa.Integer()),
        sa.Column("task_description", sa.Text()),
        sa.Column("context_metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="{}"),
        sa.Column("error_message", sa.Text()),
        sa.Column("error_code", sa.Text()),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("status IN ('in_progress', 'completed', 'failed', 'timeout')", name="valid_status"),
        sa.CheckConstraint("response_time_ms IS NULL OR response_time_ms >= 0", name="valid_response_time"),
    )

    op.create_index("idx_agent_usage_agent_id", "agent_usage", ["agent_id"])
    op.create_index("idx_agent_usage_workflow_id", "agent_usage", ["workflow_id"])
    op.create_index("idx_agent_usage_invoked_at", "agent_usage", ["invoked_at"])
    op.create_index("idx_agent_usage_status", "agent_usage", ["status"])

    # Workflow states table
    op.create_table(
        "workflow_states",
        sa.Column("workflow_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("variables", postgresql.JSONB(astext_type=sa.Text()), server_default="{}"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="{}"),
        sa.Column("error", sa.Text()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("workflow_id"),
    )

    op.create_index("idx_workflow_status", "workflow_states", ["status"])

    # Task states table
    op.create_table(
        "task_states",
        sa.Column("task_id", sa.Text(), nullable=False),
        sa.Column("workflow_id", sa.Text(), nullable=False),
        sa.Column("agent_id", sa.Text(), nullable=False),
        sa.Column("agent_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("execution_time", sa.Float()),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("retry_count", sa.Integer(), server_default="0"),
        sa.Column("dependencies", postgresql.ARRAY(sa.Text()), server_default=sa.text("ARRAY[]::TEXT[]")),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflow_states.workflow_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("task_id", "workflow_id"),
    )

    op.create_index("idx_task_workflow", "task_states", ["workflow_id"])
    op.create_index("idx_task_status", "task_states", ["status"])

    # Workflow state history table
    op.create_table(
        "workflow_state_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workflow_id", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("state_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_id", "version"),
    )

    op.create_index("idx_history_workflow", "workflow_state_history", ["workflow_id"])

    # Coordination events table
    op.create_table(
        "coordination_events",
        sa.Column("event_id", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("workflow_id", sa.Text(), nullable=False),
        sa.Column("task_id", sa.Text()),
        sa.Column("timestamp", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("agent_id", sa.Text()),
        sa.Column("agent_type", sa.Text()),
        sa.Column("source_agent", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("target_agent", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("status", sa.Text()),
        sa.Column("duration_ms", sa.Float()),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("performance", postgresql.JSONB(astext_type=sa.Text())),
        sa.PrimaryKeyConstraint("event_id"),
    )

    # Performance indexes for coordination events
    op.create_index("idx_events_workflow", "coordination_events", ["workflow_id", sa.text("timestamp DESC")])
    op.create_index("idx_events_task", "coordination_events", ["task_id", sa.text("timestamp DESC")])
    op.create_index("idx_events_agent", "coordination_events", ["agent_id", sa.text("timestamp DESC")])
    op.create_index(
        "idx_events_workflow_type",
        "coordination_events",
        ["workflow_id", "event_type", sa.text("timestamp DESC")],
    )

    # Create functions and triggers
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER update_agents_updated_at
            BEFORE UPDATE ON agents
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """
    )

    op.execute(
        """
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
        """
    )

    op.execute(
        """
        CREATE TRIGGER update_agent_metrics_on_insert
            AFTER INSERT ON agent_usage
            FOR EACH ROW
            WHEN (NEW.status IN ('completed', 'failed'))
            EXECUTE FUNCTION update_agent_metrics();
        """
    )

    op.execute(
        """
        CREATE TRIGGER update_agent_metrics_on_update
            AFTER UPDATE ON agent_usage
            FOR EACH ROW
            WHEN (NEW.status IN ('completed', 'failed') AND OLD.status = 'in_progress')
            EXECUTE FUNCTION update_agent_metrics();
        """
    )

    # Create materialized view for agent statistics
    op.execute(
        """
        CREATE MATERIALIZED VIEW agent_statistics AS
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
        """
    )

    op.create_index("idx_agent_statistics_id", "agent_statistics", ["id"], unique=True)

    # Insert initial schema version
    op.execute(
        """
        INSERT INTO schema_version (version, description)
        VALUES (1, 'Initial agent registry and coordination schema with pgvector support')
        ON CONFLICT (version) DO NOTHING
        """
    )


def downgrade() -> None:
    """Drop all tables in reverse order."""
    # Drop materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS agent_statistics")

    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_agent_metrics_on_update ON agent_usage")
    op.execute("DROP TRIGGER IF EXISTS update_agent_metrics_on_insert ON agent_usage")
    op.execute("DROP TRIGGER IF EXISTS update_agents_updated_at ON agents")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS update_agent_metrics()")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop tables in reverse dependency order
    op.drop_table("coordination_events")
    op.drop_table("workflow_state_history")
    op.drop_table("task_states")
    op.drop_table("workflow_states")
    op.drop_table("agent_usage")
    op.drop_table("agent_dependencies")
    op.drop_table("agents")
    op.drop_table("schema_version")

    # Note: Extensions are not dropped as they might be used by other databases
