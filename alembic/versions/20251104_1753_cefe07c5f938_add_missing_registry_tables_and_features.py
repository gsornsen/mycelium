"""Add missing registry tables and features.

Revision ID: cefe07c5f938
Revises: 45db6a6fd943
Create Date: 2025-11-04 17:53:29.777319

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cefe07c5f938"
down_revision: str | None = "45db6a6fd943"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add missing registry tables and update vector dimensions."""
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == "postgresql"

    if is_postgresql:
        # First, update the vector dimension from 1536 to 384 for agents table
        # We need to drop and recreate the column due to vector dimension change
        op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS embedding")
        op.execute("ALTER TABLE agents ADD COLUMN embedding vector(384)")

        # Recreate the index with correct dimension
        op.execute("DROP INDEX IF EXISTS idx_agent_embedding")
        op.execute(
            "CREATE INDEX idx_agents_embedding_hnsw ON agents "
            "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
        )

        # Create agent_dependencies table
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
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["depends_on_agent_id"], ["agents.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("agent_id", "depends_on_agent_id"),
            sa.CheckConstraint("agent_id != depends_on_agent_id", name="no_self_dependency"),
            sa.CheckConstraint(
                "dependency_type IN ('required', 'optional', 'recommended')",
                name="valid_dependency_type",
            ),
        )

        # Create agent_usage table
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
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
            sa.CheckConstraint(
                "status IN ('in_progress', 'completed', 'failed', 'timeout')",
                name="valid_status",
            ),
            sa.CheckConstraint(
                "response_time_ms IS NULL OR response_time_ms >= 0",
                name="valid_response_time",
            ),
        )

        # Create indexes for agent_dependencies
        op.create_index("idx_agent_dependencies_agent_id", "agent_dependencies", ["agent_id"])
        op.create_index("idx_agent_dependencies_depends_on", "agent_dependencies", ["depends_on_agent_id"])

        # Create indexes for agent_usage
        op.create_index("idx_agent_usage_agent_id", "agent_usage", ["agent_id"])
        op.create_index("idx_agent_usage_workflow_id", "agent_usage", ["workflow_id"])
        op.create_index("idx_agent_usage_invoked_at", "agent_usage", ["invoked_at"])
        op.create_index("idx_agent_usage_status", "agent_usage", ["status"])

        # Create update_updated_at_column function
        op.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)

        # Create trigger for agents table
        op.execute("""
            CREATE TRIGGER update_agents_updated_at
                BEFORE UPDATE ON agents
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)

        # Create update_agent_metrics function
        op.execute("""
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
        """)

        # Create triggers for agent_usage table
        op.execute("""
            CREATE TRIGGER update_agent_metrics_on_insert
                AFTER INSERT ON agent_usage
                FOR EACH ROW
                WHEN (NEW.status IN ('completed', 'failed'))
                EXECUTE FUNCTION update_agent_metrics();
        """)

        op.execute("""
            CREATE TRIGGER update_agent_metrics_on_update
                AFTER UPDATE ON agent_usage
                FOR EACH ROW
                WHEN (NEW.status IN ('completed', 'failed') AND OLD.status = 'in_progress')
                EXECUTE FUNCTION update_agent_metrics();
        """)

        # Create materialized view for agent statistics
        op.execute("""
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
        """)

        op.execute("CREATE UNIQUE INDEX idx_agent_statistics_id ON agent_statistics(id)")

        # Update schema_version with new entry
        op.execute("""
            INSERT INTO schema_version (version, description)
            VALUES (2, 'Added agent_usage, agent_dependencies tables and related features')
            ON CONFLICT (version) DO NOTHING;
        """)

    else:
        # SQLite-compatible versions
        op.create_table(
            "agent_dependencies",
            sa.Column("id", sa.Text(), nullable=False),
            sa.Column("agent_id", sa.Text(), nullable=False),
            sa.Column("depends_on_agent_id", sa.Text(), nullable=False),
            sa.Column("dependency_type", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["depends_on_agent_id"], ["agents.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("agent_id", "depends_on_agent_id"),
        )

        op.create_table(
            "agent_usage",
            sa.Column("id", sa.Text(), nullable=False),
            sa.Column("agent_id", sa.Text(), nullable=False),
            sa.Column("workflow_id", sa.Text()),
            sa.Column("session_id", sa.Text()),
            sa.Column(
                "invoked_at",
                sa.TIMESTAMP(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column("completed_at", sa.TIMESTAMP()),
            sa.Column("status", sa.Text(), nullable=False),
            sa.Column("response_time_ms", sa.Integer()),
            sa.Column("task_description", sa.Text()),
            sa.Column("context_metadata", sa.Text(), server_default="{}"),
            sa.Column("error_message", sa.Text()),
            sa.Column("error_code", sa.Text()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        )

        # Create indexes for SQLite
        op.create_index("idx_agent_dependencies_agent_id", "agent_dependencies", ["agent_id"])
        op.create_index("idx_agent_dependencies_depends_on", "agent_dependencies", ["depends_on_agent_id"])
        op.create_index("idx_agent_usage_agent_id", "agent_usage", ["agent_id"])
        op.create_index("idx_agent_usage_workflow_id", "agent_usage", ["workflow_id"])
        op.create_index("idx_agent_usage_invoked_at", "agent_usage", ["invoked_at"])
        op.create_index("idx_agent_usage_status", "agent_usage", ["status"])


def downgrade() -> None:
    """Drop added tables and features."""
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == "postgresql"

    if is_postgresql:
        # Drop materialized view
        op.execute("DROP MATERIALIZED VIEW IF EXISTS agent_statistics")

        # Drop triggers
        op.execute("DROP TRIGGER IF EXISTS update_agent_metrics_on_update ON agent_usage")
        op.execute("DROP TRIGGER IF EXISTS update_agent_metrics_on_insert ON agent_usage")
        op.execute("DROP TRIGGER IF EXISTS update_agents_updated_at ON agents")

        # Drop functions
        op.execute("DROP FUNCTION IF EXISTS update_agent_metrics()")
        op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

        # Restore original vector dimension (1536)
        op.execute("DROP INDEX IF EXISTS idx_agents_embedding_hnsw")
        op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS embedding")
        op.execute("ALTER TABLE agents ADD COLUMN embedding vector(1536)")
        op.execute("CREATE INDEX idx_agent_embedding ON agents USING ivfflat(embedding vector_l2_ops)")

    # Drop indexes
    op.drop_index("idx_agent_usage_status", table_name="agent_usage")
    op.drop_index("idx_agent_usage_invoked_at", table_name="agent_usage")
    op.drop_index("idx_agent_usage_workflow_id", table_name="agent_usage")
    op.drop_index("idx_agent_usage_agent_id", table_name="agent_usage")
    op.drop_index("idx_agent_dependencies_depends_on", table_name="agent_dependencies")
    op.drop_index("idx_agent_dependencies_agent_id", table_name="agent_dependencies")

    # Drop tables
    op.drop_table("agent_usage")
    op.drop_table("agent_dependencies")

    if is_postgresql:
        # Remove schema_version entry
        op.execute("DELETE FROM schema_version WHERE version = 2")
