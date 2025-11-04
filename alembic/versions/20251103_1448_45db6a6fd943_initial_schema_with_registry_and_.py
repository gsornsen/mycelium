"""Initial schema with registry and coordination tables.

Revision ID: 45db6a6fd943
Revises:
Create Date: 2025-11-03 14:48:50.456859

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
    # Enable required extensions (PostgreSQL only)
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == "postgresql"

    if is_postgresql:
        op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')

        # Create schema version tracking table with PostgreSQL-specific syntax
        op.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                description TEXT NOT NULL
            )
        """)
    else:
        # Create schema version tracking table with SQLite-compatible syntax
        op.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                description TEXT NOT NULL
            )
        """)

    # Main agents table with vector embeddings
    # Use dialect-specific column types
    if is_postgresql:
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
        )

        # Add vector column for PostgreSQL
        op.execute("ALTER TABLE agents ADD COLUMN embedding vector(1536)")
    else:
        # SQLite-compatible version (using TEXT for arrays and JSON)
        op.create_table(
            "agents",
            sa.Column(
                "id",
                sa.Text(),  # SQLite doesn't have UUID
                nullable=False,
            ),
            sa.Column("agent_id", sa.Text(), nullable=False),
            sa.Column("agent_type", sa.Text(), nullable=False),
            sa.Column("name", sa.Text(), nullable=False),
            sa.Column("display_name", sa.Text(), nullable=False),
            sa.Column("category", sa.Text(), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("capabilities", sa.Text(), server_default="[]"),  # JSON array as text
            sa.Column("tools", sa.Text(), server_default="[]"),
            sa.Column("keywords", sa.Text(), server_default="[]"),
            sa.Column("file_path", sa.Text(), nullable=False),
            sa.Column("estimated_tokens", sa.Integer()),
            sa.Column("metadata", sa.Text(), server_default="{}"),  # JSON as text
            sa.Column("avg_response_time_ms", sa.Integer()),
            sa.Column("success_rate", sa.Numeric(5, 2)),
            sa.Column("usage_count", sa.Integer(), server_default="0"),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.TIMESTAMP(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column("last_used_at", sa.TIMESTAMP()),
            sa.Column("embedding", sa.Text()),  # Store as text/JSON in SQLite
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("agent_id"),
        )

    # Create indexes
    op.create_index(op.f("ix_agents_agent_id"), "agents", ["agent_id"], unique=False)
    op.create_index(op.f("ix_agents_agent_type"), "agents", ["agent_type"], unique=False)
    op.create_index(op.f("ix_agents_category"), "agents", ["category"], unique=False)

    # Additional indexes for PostgreSQL
    if is_postgresql:
        op.execute("CREATE INDEX idx_agent_capabilities ON agents USING GIN(capabilities)")
        op.execute("CREATE INDEX idx_agent_tools ON agents USING GIN(tools)")
        op.execute("CREATE INDEX idx_agent_keywords ON agents USING GIN(keywords)")
        op.execute("CREATE INDEX idx_agent_metadata ON agents USING GIN(metadata)")
        op.execute("CREATE INDEX idx_agent_embedding ON agents USING ivfflat(embedding vector_l2_ops)")

    # Coordination events table
    if is_postgresql:
        op.create_table(
            "coordination_events",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                server_default=sa.text("uuid_generate_v4()"),
                nullable=False,
            ),
            sa.Column("workflow_id", sa.Text(), nullable=False),
            sa.Column("event_type", sa.Text(), nullable=False),
            sa.Column("event_data", postgresql.JSONB(astext_type=sa.Text()), server_default="{}"),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        op.create_table(
            "coordination_events",
            sa.Column("id", sa.Text(), nullable=False),
            sa.Column("workflow_id", sa.Text(), nullable=False),
            sa.Column("event_type", sa.Text(), nullable=False),
            sa.Column("event_data", sa.Text(), server_default="{}"),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    op.create_index(
        op.f("ix_coordination_events_workflow_id"),
        "coordination_events",
        ["workflow_id"],
        unique=False,
    )
    op.create_index(op.f("ix_coordination_events_event_type"), "coordination_events", ["event_type"], unique=False)

    # Workflow states table
    if is_postgresql:
        op.create_table(
            "workflow_states",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                server_default=sa.text("uuid_generate_v4()"),
                nullable=False,
            ),
            sa.Column("workflow_id", sa.Text(), nullable=False),
            sa.Column("state_type", sa.Text(), nullable=False),
            sa.Column("state_data", postgresql.JSONB(astext_type=sa.Text()), server_default="{}"),
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
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("workflow_id"),
        )
    else:
        op.create_table(
            "workflow_states",
            sa.Column("id", sa.Text(), nullable=False),
            sa.Column("workflow_id", sa.Text(), nullable=False),
            sa.Column("state_type", sa.Text(), nullable=False),
            sa.Column("state_data", sa.Text(), server_default="{}"),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.TIMESTAMP(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("workflow_id"),
        )

    op.create_index(op.f("ix_workflow_states_state_type"), "workflow_states", ["state_type"], unique=False)

    # Task states table
    if is_postgresql:
        op.create_table(
            "task_states",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                server_default=sa.text("uuid_generate_v4()"),
                nullable=False,
            ),
            sa.Column("task_id", sa.Text(), nullable=False),
            sa.Column("workflow_id", sa.Text()),
            sa.Column("status", sa.Text(), nullable=False),
            sa.Column("result_data", postgresql.JSONB(astext_type=sa.Text())),
            sa.Column("error_message", sa.Text()),
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
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("task_id"),
        )
    else:
        op.create_table(
            "task_states",
            sa.Column("id", sa.Text(), nullable=False),
            sa.Column("task_id", sa.Text(), nullable=False),
            sa.Column("workflow_id", sa.Text()),
            sa.Column("status", sa.Text(), nullable=False),
            sa.Column("result_data", sa.Text()),
            sa.Column("error_message", sa.Text()),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.TIMESTAMP(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("task_id"),
        )

    op.create_index(op.f("ix_task_states_workflow_id"), "task_states", ["workflow_id"], unique=False)
    op.create_index(op.f("ix_task_states_status"), "task_states", ["status"], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index(op.f("ix_task_states_status"), table_name="task_states")
    op.drop_index(op.f("ix_task_states_workflow_id"), table_name="task_states")
    op.drop_table("task_states")

    op.drop_index(op.f("ix_workflow_states_state_type"), table_name="workflow_states")
    op.drop_table("workflow_states")

    op.drop_index(op.f("ix_coordination_events_event_type"), table_name="coordination_events")
    op.drop_index(op.f("ix_coordination_events_workflow_id"), table_name="coordination_events")
    op.drop_table("coordination_events")

    # Drop PostgreSQL-specific indexes
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS idx_agent_embedding")
        op.execute("DROP INDEX IF EXISTS idx_agent_metadata")
        op.execute("DROP INDEX IF EXISTS idx_agent_keywords")
        op.execute("DROP INDEX IF EXISTS idx_agent_tools")
        op.execute("DROP INDEX IF EXISTS idx_agent_capabilities")

    op.drop_index(op.f("ix_agents_category"), table_name="agents")
    op.drop_index(op.f("ix_agents_agent_type"), table_name="agents")
    op.drop_index(op.f("ix_agents_agent_id"), table_name="agents")
    op.drop_table("agents")

    op.execute("DROP TABLE IF EXISTS schema_version")
